# DesignProof - FreeCAD Workbench

Proof-test your parametric CAD models before they reach the shop floor.

DesignProof is a FreeCAD workbench that systematically varies the dimensional parameters of a model and checks whether FreeCAD can successfully regenerate the geometry. It identifies fragile features, quantifies model robustness, and helps you build parametric models that actually work across their intended design range.

*Screenshots will be added here.*

## The story behind this project

I'm [Unai Pz de A](https://github.com/Unai-Pz-de-A), a freelance mechanical design engineer specialized in SOLIDWORKS (and currently learning FreeCAD). I've worked across wind energy, distribution systems, and automated machinery.

This plugin was born from a real frustration: parametric models that look solid until someone changes a dimension and everything breaks. The concept of parametric robustness comes from the research of Aritz Aranburu Gorrotxategi and colleagues, who formalized what experienced designers learn the hard way -- a truly robust model isn't just one that works, but one that keeps working.

**This is my first open-source project.** I'm not a software developer -- I'm a mechanical engineer who built this with the help of [Claude Code](https://claude.ai/claude-code). If I could do it, you can contribute too. Every idea, bug report, or pull request is welcome.

## Features

- **Automatic parameter detection** -- Sketch constraints (Distance, DistanceX, DistanceY, Radius, Diameter, Angle), extrusion properties (LengthFwd, LengthRev), and spreadsheet-driven parameters.
- **Three variation modes** -- One-at-a-Time (OAT), Full Factorial, and Random Sampling.
- **Interactive GUI** -- Parameter table with editable ranges, preset margins (+/-10%, 20%, 30%, 50%), save/load configuration as JSON.
- **Results dialog** -- Three tabs: Variations, Failure Analysis, and Model Metrics.
- **Model complexity metrics** -- Feature count, dependency graph density, cyclomatic complexity, Li entropy, maximum depth.
- **CSV report generation** -- Export detailed results for further analysis.
- **Robustness rating** -- EXCELLENT (>=90%), GOOD (>=70%), MODERATE (>=50%), POOR (>=25%), CRITICAL (<25%).

## How it works

In the default **OAT (One-at-a-Time)** mode, each parameter is varied independently while all others remain at their nominal values. For each parameter, the tool generates evenly spaced values between a configured minimum and maximum (e.g., +/-30% of the original value in 5 steps). After each change, FreeCAD recomputes the model and DesignProof checks every feature for errors. The **success rate** is the percentage of variations that regenerate without errors.

This approach isolates the effect of each parameter, making it straightforward to pinpoint which dimensions and features are fragile. Full Factorial and Random Sampling modes are available for more thorough or exploratory analysis.

## Validated results

Tested on 5 models of varying complexity via FreeCAD 1.0.2:

| Model | Type | Parameters | Variations | Success Rate | Rating |
|-------|------|-----------|------------|-------------|--------|
| Bracket (Rookies060) | PartDesign | 26 | 107 | 100.0% | EXCELLENT |
| Flange (Rookies062) | PartDesign | 14 | 58 | 100.0% | EXCELLENT |
| Lever (Rookies063) | PartDesign | 20 | 81 | 100.0% | EXCELLENT |
| Part (Rookies064) | Part WB | 23 | 93 | 100.0% | EXCELLENT |
| TestModel | PartDesign | 7 | 29 | 93.1% | EXCELLENT |

Test models sourced from the FreeCAD Rookies series by Paulo Ferreira 3D (GrabCAD). Mode: OAT, +/-30%, 5 steps.

## Requirements

- FreeCAD 1.0 or later
- No external Python dependencies

## Installation

### Manual

Copy the `DesignProof` folder to your FreeCAD Mod directory:

- **Linux**: `~/.FreeCAD/Mod/`
- **Windows**: `%APPDATA%/FreeCAD/Mod/`
- **macOS**: `~/Library/Preferences/FreeCAD/Mod/`

Restart FreeCAD. The workbench will appear in the workbench selector.

## Usage

1. Open a parametric model (`.FCStd`) in FreeCAD.
2. Switch to the **DesignProof** workbench.
3. Click **Detect Parameters** to scan the model and configure variation ranges.
4. Adjust ranges or use a preset margin, select the variation mode, then click OK.
5. The analysis runs with a progress dialog. Results are presented in three tabs:
   - **Variations** -- Every parameter combination and its result.
   - **Failure Analysis** -- Which parameters and features cause failures.
   - **Model Metrics** -- Complexity and dependency metrics.
6. Use **Model Metrics** from the toolbar for standalone dependency analysis.

## Toolbar commands

| Command | Description |
|---------|-------------|
| Detect Parameters | Scan model, configure ranges and variation mode |
| Run Analysis | Execute variation test with progress dialog |
| Model Metrics | View dependency graph and complexity metrics |

## Headless usage

DesignProof can also be used from FreeCAD's command line (`FreeCADcmd`) for batch processing:

```python
import FreeCAD as App
doc = App.openDocument("model.FCStd")

from core.parameter_detector import detect_parameters
from core.variation_engine import generate_variations, ParameterRange
from core.recompute_tester import RobustnessTester

params = detect_parameters(doc)
ranges = [ParameterRange(p.id, p.value * 0.7, p.value * 1.3, steps=5)
          for p in params if p.value > 0]
nominal = {p.id: p.value for p in params}
variations = generate_variations(ranges, mode="oat", nominal_values=nominal)

tester = RobustnessTester(doc)
results = tester.run(variations, {p.id: p for p in params})

passed = sum(1 for r in results if r.status == "PASS")
print(f"Success rate: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
```

## Known limitations

- Only detects dimensional parameters (sketch constraints and extrusion properties). Booleans, enumerations, and placement parameters are not yet supported.
- Does not detect parameters driven by Python expressions or linked to external files.
- Full Factorial mode can be very slow with many parameters (exponential growth).
- The Fillet/Chamfer features are the most common source of regeneration failures -- this is expected behavior, not a bug.
- Currently tested only on Windows with FreeCAD 1.0.2.

## Roadmap

The goal is for DesignProof to become a comprehensive design verification toolkit. Future directions:

- Manufacturability checks (wall thickness, draft angles, undercuts)
- Tolerance stack-up analysis
- Design rule verification (minimum radii, hole spacing, etc.)
- Batch processing of multiple models
- Integration with FreeCAD's Assembly workbench
- Report generation in HTML/PDF

All ideas are welcome -- see Contributing below.

## References

This work is based on the methodology described in:

- Aranburu, A., Cotillas, M., Justel, D., Contero, M., & Camba, J. D. (2022). *"How Does the Modeling Strategy Influence Design Optimization and the Automatic Generation of Parametric Geometry Variations?"* Computer-Aided Design, 151, 1-13. [DOI: 10.1016/j.cad.2022.103345](https://doi.org/10.1016/j.cad.2022.103345)

- Otto, H. E., & Mandorli, F. (2024). *"Data-Driven Assessment of Parametric Robustness of CAD Models."* Proceedings of CAD'24, Eger, Hungary.

## Contributing

This project is maintained by a mechanical engineer, not a professional developer. **Every contribution matters**, whether it's:

- Reporting a bug or a model that produces unexpected results
- Suggesting a new verification feature
- Improving the code, documentation, or translations
- Sharing your test results with different models
- Proposing ideas for the roadmap

Open an [issue](https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/issues) or submit a pull request. No contribution is too small.

## License

[LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)

## Links

- [Repository](https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof)
- [Issue tracker](https://github.com/Unai-Pz-de-A/FreeCAD-DesignProof/issues)
