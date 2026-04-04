<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Contributing to DesignProof

Thank you for considering contributing to DesignProof! Every contribution matters, no matter how small.

## Ways to contribute

- **Report bugs** -- Open an [issue](https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/issues) with steps to reproduce. Attach the `.FCStd` model if possible.
- **Test on other platforms** -- We've only tested on Windows so far. Linux and macOS feedback is very welcome.
- **Share test results** -- Run DesignProof on your models and share the results (via Issues or Discussions).
- **Suggest features** -- Open a [Discussion](https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/discussions) or Issue with your idea.
- **Improve code or docs** -- Submit a pull request.

## Setting up for development

1. Clone the repository into your FreeCAD Mod directory:
   - **Windows**: `%APPDATA%/FreeCAD/Mod/`
   - **Linux**: `~/.FreeCAD/Mod/`
   - **macOS**: `~/Library/Preferences/FreeCAD/Mod/`

2. Restart FreeCAD. The workbench will appear in the workbench selector.

3. No external Python dependencies are needed -- DesignProof uses only the Python standard library and the FreeCAD API.

## Submitting a pull request

1. Fork the repository and create a branch from `main`.
2. Make your changes. Keep commits focused on a single change.
3. Test your changes by running the workbench on a parametric FreeCAD model.
4. Open a pull request with a clear description of what you changed and why.

## Code style

- Python files use 4-space indentation.
- No external dependencies -- only Python standard library and FreeCAD API.
- Each core module should stay under ~200 lines.
- Add SPDX license headers to new files: `# SPDX-License-Identifier: LGPL-2.1-or-later`

## License

By contributing, you agree that your contributions will be licensed under the [LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html) license.
