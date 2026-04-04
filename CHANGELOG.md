<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.1]: https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/releases/tag/v0.1.1
[0.1.0]: https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/releases/tag/v0.1.0
