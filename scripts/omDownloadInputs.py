#
# Copyright 2023 The Superpower Institute Ltd.
#
# This file is part of OpenMethane.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Download required input files

This downloads the input files that rarely change and can be cached between runs.
"""

import os

import attrs
import requests

from openmethane_prior.config import PriorConfig, load_config_from_env
from openmethane_prior.omUtils import getenv

remote = getenv("PRIOR_REMOTE")


def download_input_files(config: PriorConfig, remote: str):
    """
    Download all input files.

    Parameters
    ----------
    config
        Prior configuration
    remote
        Remote base URL to download from
    """
    os.makedirs(config.input_path, exist_ok=True)

    for item in attrs.asdict(config.layer_inputs).values():
        fragment = str(item)

        filepath = config.as_input_file(fragment)

        print(filepath)
        url = f"{remote}{fragment}"

        if not os.path.exists(filepath):
            print(f"Downloading {fragment} to {filepath} from {url}")

            with requests.get(url, stream=True, timeout=30) as response:
                with open(filepath, mode="wb") as file:
                    for chunk in response.iter_content(chunk_size=10 * 1024):
                        file.write(chunk)
        else:
            print(f"Skipping {fragment} because it already exists at {filepath}")


if __name__ == "__main__":
    config = load_config_from_env()

    download_input_files(config, remote=remote)
