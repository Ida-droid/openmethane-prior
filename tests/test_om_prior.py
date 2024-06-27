import datetime
import os
import subprocess

import numpy as np
import pandas as pd
import pytest
import requests
import xarray as xr

from openmethane_prior.layers.omGFASEmis import downloadGFAS
from openmethane_prior.omInputs import livestockDataPath, sectoralEmissionsPath
from openmethane_prior.omUtils import getenv, secsPerYear
from scripts.omDownloadInputs import download_input_files, downloads, remote


@pytest.fixture(scope="session")
def cro_xr(root_dir):
    cmaqExamplePath = getenv("CMAQ_EXAMPLE")
    croFilePath = os.path.join(root_dir, cmaqExamplePath, getenv("CROFILE"))
    return xr.open_dataset(croFilePath)


@pytest.fixture(scope="session")
def dot_xr(root_dir):
    cmaqExamplePath = getenv("CMAQ_EXAMPLE")
    dotFilePath = os.path.join(root_dir, cmaqExamplePath, getenv("DOTFILE"))
    return xr.open_dataset(dotFilePath)


@pytest.fixture(scope="session")
def geom_xr(root_dir):
    cmaqExamplePath = getenv("CMAQ_EXAMPLE")
    geomFilePath = os.path.join(root_dir, cmaqExamplePath, getenv("GEO_EM"))
    return xr.open_dataset(geomFilePath)


# Fixture to download and later remove all input files
@pytest.fixture(scope="session")
def input_files(root_dir):
    download_input_files(root_path=root_dir, downloads=downloads, remote=remote)

    input_folder = os.path.join(root_dir, "inputs")

    downloaded_files = os.listdir(input_folder)

    yield downloaded_files

    for file in [i for i in downloaded_files if i != "README.md"]:
        filepath = os.path.join(input_folder, file)
        os.remove(filepath)


@pytest.fixture(scope="session")
def input_domain_xr(root_dir, input_files):
    subprocess.run(["python", os.path.join(root_dir, "scripts/omCreateDomainInfo.py")], check=True)  # noqa: S603, S607

    # Generated by scripts/omCreateDomainInfo.py
    filepath_in_domain = os.path.join(root_dir, "inputs/om-domain-info.nc")

    yield xr.load_dataset(filepath_in_domain)

    os.remove(filepath_in_domain)


@pytest.fixture(scope="session")
def output_domain_xr(root_dir, input_domain_xr):
    subprocess.run(
        ["python", os.path.join(root_dir, "scripts/omPrior.py"), "2022-07-01", "2022-07-02"],  # noqa: S603, S607
        check=True,
    )

    # Generated by scripts/omPrior.py
    filepath_out_domain = os.path.join(root_dir, "outputs/out-om-domain-info.nc")

    yield xr.load_dataset(filepath_out_domain)

    os.remove(filepath_out_domain)


def test_001_response_for_download_links():
    for filename, filepath in downloads:
        url = f"{remote}{filename}"
        with requests.get(url, stream=True, timeout=30) as response:
            print(f"Response code for {url}: {response.status_code}")
            assert response.status_code == 200


def test_002_cdsapi_connection(root_dir, tmpdir):
    filepath = tmpdir.mkdir("sub").join("test_download_cdsapi.nc")

    startDate = datetime.datetime.strptime("2022-07-01", "%Y-%m-%d")
    endDate = datetime.datetime.strptime("2022-07-02", "%Y-%m-%d")

    downloadGFAS(startDate=startDate, endDate=endDate, fileName=filepath)

    assert os.path.exists(filepath)


def test_003_inputs_folder_is_empty(root_dir):
    input_folder = os.path.join(root_dir, "inputs")

    EXPECTED_FILES = ["README.md"]

    assert os.listdir(input_folder) == EXPECTED_FILES, f"Folder '{input_folder}' is not empty"


def test_004_omDownloadInputs(root_dir, input_files):
    EXPECTED_FILES = [
        "ch4-electricity.csv",
        "coal-mining_emissions-sources.csv",
        "oil-and-gas-production-and-transport_emissions-sources.csv",
        "NLUM_ALUMV8_250m_2015_16_alb.tif",
        "ch4-sectoral-emissions.csv",
        "landuse-sector-map.csv",
        "nasa-nighttime-lights.tiff",
        "AUS_2021_AUST_SHP_GDA2020.zip",
        "EntericFermentation.nc",
        "termite_emissions_2010-2016.nc",
        "DLEM_totflux_CRU_diagnostic.nc",
        "README.md",
    ]

    assert sorted(input_files) == sorted(EXPECTED_FILES)


def test_005_agriculture_emissions(root_dir, input_files):
    filepath_livestock = os.path.join(root_dir, livestockDataPath)
    livestock_data = xr.open_dataset(filepath_livestock)

    filepath_sector = os.path.join(root_dir, sectoralEmissionsPath)
    sector_data = pd.read_csv(filepath_sector).to_dict(orient="records")[0]

    lsVal = round(np.sum(livestock_data["CH4_total"].values))
    agVal = round(sector_data["agriculture"] * 1e9)
    agDX = agVal - lsVal

    assert agDX > 0, f"Livestock CH4 exceeds bounds of total agriculture CH4: {agDX / 1e9}"


# TODO Update this test when file structure is clear.
# This test ensures that the grid size for all input files is 10 km.
def test_006_grid_size_for_geo_files(cro_xr, geom_xr, dot_xr):
    expected_cell_size = 10000

    assert cro_xr.XCELL == expected_cell_size
    assert cro_xr.YCELL == expected_cell_size

    assert geom_xr.DX == expected_cell_size
    assert geom_xr.DY == expected_cell_size

    assert dot_xr.XCELL == expected_cell_size
    assert dot_xr.YCELL == expected_cell_size


def test_007_compare_in_domain_with_cro_dot_files(input_domain_xr, cro_xr, dot_xr):
    assert dot_xr.NCOLS == input_domain_xr.COL_D.size
    assert dot_xr.NROWS == input_domain_xr.ROW_D.size

    assert cro_xr.NCOLS == input_domain_xr.COL.size
    assert cro_xr.NROWS == input_domain_xr.ROW.size


def test_008_compare_out_domain_with_cro_dot_files(output_domain_xr, cro_xr, dot_xr):
    assert dot_xr.NCOLS == output_domain_xr.COL_D.size
    assert dot_xr.NROWS == output_domain_xr.ROW_D.size

    assert cro_xr.NCOLS == output_domain_xr.COL.size
    assert cro_xr.NROWS == output_domain_xr.ROW.size


def test_009_output_domain_xr(output_domain_xr, num_regression):
    mean_values = {key: output_domain_xr[key].mean().item() for key in output_domain_xr.keys()}

    num_regression.check(mean_values)


def test_010_emission_discrepancy(root_dir, output_domain_xr, input_files):
    modelAreaM2 = output_domain_xr.DX * output_domain_xr.DY

    filepath_sector = os.path.join(root_dir, sectoralEmissionsPath)
    sector_data = pd.read_csv(filepath_sector).to_dict(orient="records")[0]

    for sector in sector_data.keys():
        layerName = f"OCH4_{sector.upper()}"
        sectorVal = float(sector_data[sector]) * 1e9

        # Check each layer in the output sums up to the input
        if layerName in output_domain_xr:
            layerVal = np.sum(output_domain_xr[layerName][0].values * modelAreaM2 * secsPerYear)

            if sector == "agriculture":
                layerVal += np.sum(
                    output_domain_xr["OCH4_LIVESTOCK"][0].values * modelAreaM2 * secsPerYear
                )

            diff = round(layerVal - sectorVal)
            perectenageDifference = diff / sectorVal * 100

            assert (
                abs(perectenageDifference) < 0.1
            ), f"Discrepency of {perectenageDifference}% in {sector} emissions"
