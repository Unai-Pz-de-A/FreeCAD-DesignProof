# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.
"""
Analysis Dialog
===============
Progress dialog during robustness analysis,
followed by a results display.
"""

import os
import FreeCAD as App
import FreeCADGui as Gui

from PySide import QtCore, QtGui

try:
    from ..core.parameter_detector import detect_parameters
    from ..core.variation_engine import (
        ParameterRange, generate_variations, estimate_space_size
    )
    from ..core.recompute_tester import RobustnessTester
    from ..core.dependency_analyzer import analyze_dependencies
    from ..core.report_generator import generate_report
except ImportError:
    from core.parameter_detector import detect_parameters
    from core.variation_engine import (
        ParameterRange, generate_variations, estimate_space_size
    )
    from core.recompute_tester import RobustnessTester
    from core.dependency_analyzer import analyze_dependencies
    from core.report_generator import generate_report


def run_analysis_dialog(ranges=None, params_map=None, mode="oat",
                        n_samples=100, nominal_values=None,
                        live_view=False):
    """
    Main entry point: runs analysis with a progress dialog,
    then shows results.

    Args:
        live_view: If True, update 3D view after each variation (slower).
    """
    doc = App.ActiveDocument
    if doc is None:
        QtGui.QMessageBox.warning(None, "Error", "No active document.")
        return

    # If called directly (not from param_panel), auto-detect everything
    if ranges is None:
        params = detect_parameters(doc)
        if not params:
            QtGui.QMessageBox.warning(None, "Error", "No parameters found.")
            return
        params_map = {p.id: p for p in params}
        ranges = []
        for p in params:
            if p.unit == "deg" and p.value == 0:
                continue
            margin = max(p.value * 0.3, 1.0) if p.unit != "deg" else 15
            mn = max(0.1, p.value - margin)
            mx = p.value + margin
            ranges.append(ParameterRange(p.id, round(mn, 2), round(mx, 2),
                                        steps=5, unit=p.unit))
        nominal_values = {p.id: p.value for p in params
                         if p.id in {r.param_id for r in ranges}}

    # Generate variations
    variations = generate_variations(ranges, mode=mode,
                                     n_samples=n_samples,
                                     nominal_values=nominal_values)

    # Progress dialog
    progress = QtGui.QProgressDialog(
        "Running robustness analysis...", "Cancel", 0, len(variations)
    )
    progress.setWindowTitle("Robustness Analysis")
    progress.setWindowModality(QtCore.Qt.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    # Run test
    tester = RobustnessTester(doc)
    results = []

    def callback(index, total, result):
        progress.setValue(index + 1)
        status = result.status
        label = f"[{index+1}/{total}] {status}"
        if result.varied_param:
            label += f" ({result.varied_param})"
        progress.setLabelText(label)
        QtGui.QApplication.processEvents()
        if live_view:
            Gui.updateGui()
            try:
                Gui.ActiveDocument.ActiveView.redraw()
            except Exception:
                pass
        if progress.wasCanceled():
            tester.cancel()

    results = tester.run(variations, params_map, callback=callback)
    progress.close()

    if not results:
        QtGui.QMessageBox.information(None, "Cancelled", "Analysis was cancelled.")
        return

    # Compute metrics
    dep = analyze_dependencies(doc)
    metrics = dep["metrics"]

    # Generate report files. Prefer the model directory, but fall back to
    # the user's FreeCAD data dir for read-only example files or protected
    # locations such as Program Files.
    model_dir = os.path.dirname(doc.FileName) if doc.FileName else ""
    preferred_output_dir = os.path.join(model_dir, "results") if model_dir else ""

    report = None
    output_error = None

    if preferred_output_dir:
        try:
            report = generate_report(
                results, params_map, preferred_output_dir, metrics
            )
        except (PermissionError, OSError) as exc:
            output_error = exc

    if report is None:
        model_name = (
            os.path.splitext(os.path.basename(doc.FileName))[0]
            if doc.FileName else "unsaved_document"
        )
        fallback_output_dir = os.path.join(
            App.getUserAppDataDir(), "DesignProof", "results", model_name
        )
        report = generate_report(results, params_map, fallback_output_dir, metrics)

        if output_error is not None:
            App.Console.PrintWarning(
                "[DesignProof] Could not write results to model directory: "
                f"{output_error}\n"
                f"[DesignProof] Results saved to: {fallback_output_dir}\n"
            )

    # Show results dialog
    _show_results(results, params_map, metrics, report)


def _show_results(results, params_map, metrics, report):
    """Display results in a dialog."""
    total = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    warnings = sum(1 for r in results if r.status == "WARNING")
    rate = passed / total * 100 if total > 0 else 0

    if rate >= 90:
        rating, color = "EXCELLENT", "#2E7D32"
    elif rate >= 70:
        rating, color = "GOOD", "#558B2F"
    elif rate >= 50:
        rating, color = "MODERATE", "#E65100"
    elif rate >= 25:
        rating, color = "POOR", "#BF360C"
    else:
        rating, color = "CRITICAL", "#B71C1C"

    dlg = QtGui.QDialog(Gui.getMainWindow())
    dlg.setWindowTitle("Robustness Analysis Results")
    dlg.setMinimumSize(800, 600)
    layout = QtGui.QVBoxLayout(dlg)

    # Summary header
    summary_html = f"""
    <div style="text-align:center; padding:10px;">
        <h2>Robustness: <span style="color:{color}">{rating}</span></h2>
        <h3 style="color:{color}">{rate:.1f}%</h3>
        <p>Passed: {passed} | Failed: {failed} | Warnings: {warnings} | Total: {total}</p>
    </div>
    """
    summary_label = QtGui.QLabel(summary_html)
    summary_label.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(summary_label)

    # Tabs for details
    tabs = QtGui.QTabWidget()
    layout.addWidget(tabs)

    # Tab 1: Results table
    results_tab = QtGui.QWidget()
    results_layout = QtGui.QVBoxLayout(results_tab)

    results_table = QtGui.QTableWidget()
    results_table.setRowCount(len(results))
    results_table.setColumnCount(5)
    results_table.setHorizontalHeaderLabels([
        "Index", "Status", "Varied Param", "Volume", "Failed Features"
    ])
    results_table.setAlternatingRowColors(True)
    results_table.horizontalHeader().setStretchLastSection(True)

    for i, r in enumerate(results):
        results_table.setItem(i, 0, QtGui.QTableWidgetItem(str(r.index)))

        status_item = QtGui.QTableWidgetItem(r.status)
        if r.status == "PASS":
            status_item.setBackground(QtGui.QColor(200, 255, 200))
        elif r.status == "FAIL":
            status_item.setBackground(QtGui.QColor(255, 200, 200))
        else:
            status_item.setBackground(QtGui.QColor(255, 255, 200))
        results_table.setItem(i, 1, status_item)

        varied = r.varied_param or "(nominal)"
        results_table.setItem(i, 2, QtGui.QTableWidgetItem(varied))
        results_table.setItem(i, 3, QtGui.QTableWidgetItem(f"{r.volume:.0f}"))

        feats = ", ".join(n for n, _ in r.failed_features)
        results_table.setItem(i, 4, QtGui.QTableWidgetItem(feats))

    results_table.resizeColumnsToContents()
    results_layout.addWidget(results_table)
    tabs.addTab(results_tab, "Variations")

    # Tab 2: Failure analysis
    fail_tab = QtGui.QWidget()
    fail_layout = QtGui.QVBoxLayout(fail_tab)

    # Parameters causing failures
    param_fails = {}
    feature_fails = {}
    for r in results:
        if r.status != "FAIL":
            continue
        if r.varied_param:
            param_fails[r.varied_param] = param_fails.get(r.varied_param, 0) + 1
        for feat, _ in r.failed_features:
            feature_fails[feat] = feature_fails.get(feat, 0) + 1

    if param_fails:
        fail_layout.addWidget(QtGui.QLabel("<b>Parameters causing failures:</b>"))
        pf_table = QtGui.QTableWidget()
        pf_table.setRowCount(len(param_fails))
        pf_table.setColumnCount(3)
        pf_table.setHorizontalHeaderLabels(["Parameter", "Failures", "% of fails"])
        pf_table.horizontalHeader().setStretchLastSection(True)
        for i, (pid, count) in enumerate(
            sorted(param_fails.items(), key=lambda x: x[1], reverse=True)
        ):
            label = params_map[pid].label if pid in params_map else pid
            pf_table.setItem(i, 0, QtGui.QTableWidgetItem(label))
            pf_table.setItem(i, 1, QtGui.QTableWidgetItem(str(count)))
            pf_table.setItem(i, 2, QtGui.QTableWidgetItem(
                f"{count/failed*100:.0f}%" if failed > 0 else "0%"
            ))
        pf_table.resizeColumnsToContents()
        fail_layout.addWidget(pf_table)

    if feature_fails:
        fail_layout.addWidget(QtGui.QLabel("<b>Features that fail:</b>"))
        ff_table = QtGui.QTableWidget()
        ff_table.setRowCount(len(feature_fails))
        ff_table.setColumnCount(2)
        ff_table.setHorizontalHeaderLabels(["Feature", "Failure count"])
        ff_table.horizontalHeader().setStretchLastSection(True)
        for i, (feat, count) in enumerate(
            sorted(feature_fails.items(), key=lambda x: x[1], reverse=True)
        ):
            ff_table.setItem(i, 0, QtGui.QTableWidgetItem(feat))
            ff_table.setItem(i, 1, QtGui.QTableWidgetItem(str(count)))
        ff_table.resizeColumnsToContents()
        fail_layout.addWidget(ff_table)

    if not param_fails and not feature_fails:
        fail_layout.addWidget(QtGui.QLabel("No failures detected."))

    tabs.addTab(fail_tab, "Failure Analysis")

    # Tab 3: Metrics
    metrics_tab = QtGui.QWidget()
    metrics_layout = QtGui.QVBoxLayout(metrics_tab)
    metrics_table = QtGui.QTableWidget()
    metrics_table.setRowCount(len(metrics))
    metrics_table.setColumnCount(2)
    metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
    metrics_table.horizontalHeader().setStretchLastSection(True)
    for i, (key, val) in enumerate(metrics.items()):
        label = key.replace("_", " ").title()
        metrics_table.setItem(i, 0, QtGui.QTableWidgetItem(label))
        metrics_table.setItem(i, 1, QtGui.QTableWidgetItem(str(val)))
    metrics_table.resizeColumnsToContents()
    metrics_layout.addWidget(metrics_table)
    tabs.addTab(metrics_tab, "Model Metrics")

    # Bottom buttons
    btn_layout = QtGui.QHBoxLayout()
    csv_path = report.get("csv", "")
    open_csv_btn = QtGui.QPushButton(f"Open CSV ({os.path.basename(csv_path)})")
    open_csv_btn.clicked.connect(lambda: os.startfile(csv_path) if csv_path else None)
    btn_layout.addWidget(open_csv_btn)

    close_btn = QtGui.QPushButton("Close")
    close_btn.clicked.connect(dlg.close)
    btn_layout.addWidget(close_btn)
    layout.addLayout(btn_layout)

    dlg.exec_()
