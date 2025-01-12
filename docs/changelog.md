# Changelog

Versions follow [Semantic Versioning](https://semver.org/) (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the **Deprecations** section of releases.


<!--
You should *NOT* be adding new changelog entries to this file, this
file is managed by towncrier. See changelog/README.md.

You *may* edit previous changelogs to fix problems like typo corrections or such.
To add a new changelog entry, please see
https://pip.pypa.io/en/latest/development/contributing/#news-entries,
noting that we use the `changelog` directory instead of news, md instead
of rst and use slightly different categories.
-->

<!-- towncrier release notes start -->

## openmethane-prior v0.3.0 (2025-01-12)

### 🎉 Improvements

- Make OPENMETHANE_PRIOR_VERSION environment variable available inside the container ([#60](https://github.com/openmethane/openmethane-prior/pulls/60))

### 🐛 Bug Fixes

- Fix actions incorrectly populating container image version ([#61](https://github.com/openmethane/openmethane-prior/pulls/61))

### 🔧 Trivial/Internal Changes

- [#53](https://github.com/openmethane/openmethane-prior/pulls/53)


## openmethane-prior v0.2.0 (2024-11-21)

### 🎉 Improvements

- Adopt common release process from openmethane/openmethane

  Adopt common docker build workflow from openmethane/openmethane ([#57](https://github.com/openmethane/openmethane-prior/pulls/57))
