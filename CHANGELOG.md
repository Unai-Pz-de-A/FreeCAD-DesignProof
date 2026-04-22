<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-04-22

### Fixed

- `package.xml`: `<subdirectory>` set to `.` (the addon root). The previous value `freecad/DesignProof` mistakenly pointed to the Python namespace package instead of the addon root.

### Changed

- `package.xml`: `<author>` and `<maintainer>` emails switched to the GitHub noreply address.
- README: clarified manual installation instructions (paths now include the final `DesignProof/` directory).
- README: validation row mentions FreeCAD 1.1 instead of 1.0.2, matching the current `freecadmin` requirement.

## [0.1.2] - 2026-04-22

### Changed

- **Breaking**: Minimum FreeCAD raised to 1.1.0 (Qt6) and minimum Python to 3.11. FreeCAD 1.0.x is no longer supported.
- Migrated GUI from `PySide` to `PySide6`. Qt widgets now live under `QtWidgets` (e.g. `QtWidgets.QDialog` instead of `QtGui.QDialog`).
- Commands renamed to match the addon prefix convention: `DP_*` -> `DesignProof_*` (`DesignProof_DetectParameters`, `DesignProof_RunAnalysis`, `DesignProof_FocusedAnalysis`, `DesignProof_ModelMetrics`).
- Icons and other runtime assets are now loaded via `importlib.resources`, replacing `os.path.join(__file__, ...)` lookups.
- `pyproject.toml` reduced to the upstream Addon Academy stub; PySide6 declared as a dev dependency, `freecad-stubs` version pin removed.
- Screenshots used only in documentation moved from `freecad/DesignProof/Resources/screenshots/` to a top-level `Resources/screenshots/` directory; runtime icons stay under `freecad/DesignProof/Resources/icons/`.
- `CONTRIBUTING.md` moved to `.github/CONTRIBUTING.md`.

### Removed

- Unused `freecad/DesignProof/init.py` stub.
- Workflow demo GIF is no longer committed to the repository; it is distributed as an asset of the v0.1.2 GitHub release.

## [0.1.1] - 2026-04-04

### Changed

- Updated package.xml to comply with Addon Academy requirements (pythonmin, author, freecadmin placement, tags, URLs).
- Updated README: FreeCAD 0.21 requirement changed to FreeCAD 1.0.
- Verified compatibility with FreeCAD 1.1.0.

### Added

- CHANGELOG.md, CONTRIBUTING.md, pyproject.toml, .editorconfig.

## [0.1.0] - 2026-03-30

### Added

- Automatic parameter detection: sketch constraints (Distance, DistanceX, DistanceY, Radius, Diameter, Angle), extrusion properties (LengthFwd, LengthRev), and spreadsheet-driven parameters.
- Three variation modes: One-at-a-Time (OAT), Full Factorial, and Random Sampling.
- Robustness testing engine with pre-existing error filtering.
- Model complexity metrics: feature count, dependency graph density, cyclomatic complexity, Li entropy, maximum depth.
- Interactive GUI: parameter table with editable ranges, preset margins, save/load configuration as JSON.
- Results dialog with three tabs: Variations, Failure Analysis, and Model Metrics.
- CSV report generation with robustness rating (EXCELLENT/GOOD/MODERATE/POOR/CRITICAL).
- Headless mode support via FreeCADcmd for batch processing.
- Validated on 5 models (PartDesign and Part workbench) with FreeCAD 1.0.2.

[0.1.3]: https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/releases/tag/v0.1.3
[0.1.2]: https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/releases/tag/v0.1.2
[0.1.1]: https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/releases/tag/v0.1.1
[0.1.0]: https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/releases/tag/v0.1.0
