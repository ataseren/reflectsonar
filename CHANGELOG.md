# Changelog

All notable changes to ReflectSonar are documented in this file.

## 1.1.2 - 

- Added `--branch` (`-b`) CLI and configuration option for generating branch-specific reports.
- Added automated tests and repository guidance for maintainers.
- Fixed SonarQube Standard Experience and MQR mode detection.
- Prevented incomplete reports after pagination failures or API limits.
- Improved Windows console compatibility and PDF layout consistency.
- Prevented ReportLab `LayoutError` failures by wrapping and paginating oversized issue and hotspot code snippets.

## 1.1.1 - 2026-03-13

- Created CHANGELOG.md.
- Published the current PyPI and standalone-binary release.
- Forgotten to create a CHANGELOG.md in the previous release, so this is a retroactive entry.
