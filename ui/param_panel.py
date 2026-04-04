# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.
"""
Parameter Panel
===============
Task panel for detecting parameters, configuring ranges,
and selecting variation mode before running analysis.
"""

import os
import json
import FreeCAD as App
import FreeCADGui as Gui

from PySide import QtCore, QtGui

from core.parameter_detector import detect_parameters
from core.variation_engine import ParameterRange, estimate_space_size


class ParameterPanel:
    """FreeCAD Task Panel for parameter configuration."""

    def __init__(self):
        self.params = []
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Robustness Analyzer - Parameters")
        self._build_ui()
        self._detect_and_populate()

    def _build_ui(self):
        layout = QtGui.QVBoxLayout(self.form)

        # Info label
        self.info_label = QtGui.QLabel("Scanning model for parameters...")
        layout.addWidget(self.info_label)

        # Parameter table
        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Include", "Parameter", "Current", "Min", "Max", "Steps"
        ])
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QtGui.QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Mode selector
        mode_layout = QtGui.QHBoxLayout()
        mode_layout.addWidget(QtGui.QLabel("Mode:"))
        self.mode_combo = QtGui.QComboBox()
        self.mode_combo.addItems(["OAT (One-at-a-Time)", "Full Factorial", "Random Sampling"])
        self.mode_combo.currentIndexChanged.connect(self._update_estimate)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        # Random samples spinbox (only visible in random mode)
        self.samples_layout = QtGui.QHBoxLayout()
        self.samples_layout.addWidget(QtGui.QLabel("Samples:"))
        self.samples_spin = QtGui.QSpinBox()
        self.samples_spin.setRange(10, 10000)
        self.samples_spin.setValue(100)
        self.samples_spin.valueChanged.connect(self._update_estimate)
        self.samples_layout.addWidget(self.samples_spin)
        layout.addLayout(self.samples_layout)

        # Estimate label
        self.estimate_label = QtGui.QLabel("")
        self.estimate_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(self.estimate_label)

        # Margin preset buttons
        preset_layout = QtGui.QHBoxLayout()
        preset_layout.addWidget(QtGui.QLabel("Range preset:"))
        for pct in [10, 20, 30, 50]:
            btn = QtGui.QPushButton(f"+/-{pct}%")
            btn.clicked.connect(lambda checked, p=pct: self._apply_margin(p))
            preset_layout.addWidget(btn)
        layout.addLayout(preset_layout)

        # Save/Load config
        config_layout = QtGui.QHBoxLayout()
        self.save_btn = QtGui.QPushButton("Save Config")
        self.save_btn.clicked.connect(self._save_config)
        self.load_btn = QtGui.QPushButton("Load Config")
        self.load_btn.clicked.connect(self._load_config)
        config_layout.addWidget(self.save_btn)
        config_layout.addWidget(self.load_btn)
        layout.addLayout(config_layout)

        self._update_samples_visibility()

    def _detect_and_populate(self):
        """Detect parameters and fill the table."""
        doc = App.ActiveDocument
        if doc is None:
            self.info_label.setText("No active document!")
            return

        self.params = detect_parameters(doc)
        if not self.params:
            self.info_label.setText("No dimensional parameters found.")
            return

        self.info_label.setText(
            f"Found {len(self.params)} parameters in {doc.Label}"
        )

        self.table.setRowCount(len(self.params))
        for i, p in enumerate(self.params):
            # Checkbox
            cb = QtGui.QCheckBox()
            cb.setChecked(True)
            cb.stateChanged.connect(self._update_estimate)
            self.table.setCellWidget(i, 0, cb)

            # Parameter label
            label_item = QtGui.QTableWidgetItem(p.label)
            label_item.setFlags(label_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(i, 1, label_item)

            # Current value
            current_item = QtGui.QTableWidgetItem(f"{p.value:.2f}")
            current_item.setFlags(current_item.flags() & ~QtCore.Qt.ItemIsEditable)
            current_item.setBackground(QtGui.QColor(240, 240, 240))
            self.table.setItem(i, 2, current_item)

            # Min (editable)
            margin = max(p.value * 0.3, 1.0)
            min_val = max(0.1, p.value - margin)
            self.table.setItem(i, 3, QtGui.QTableWidgetItem(f"{min_val:.2f}"))

            # Max (editable)
            max_val = p.value + margin
            self.table.setItem(i, 4, QtGui.QTableWidgetItem(f"{max_val:.2f}"))

            # Steps
            self.table.setItem(i, 5, QtGui.QTableWidgetItem("5"))

        self.table.resizeColumnsToContents()
        self._update_estimate()

    def _get_selected_ranges(self):
        """Build ParameterRange list from the table."""
        ranges = []
        for i, p in enumerate(self.params):
            cb = self.table.cellWidget(i, 0)
            if not cb.isChecked():
                continue
            try:
                min_val = float(self.table.item(i, 3).text())
                max_val = float(self.table.item(i, 4).text())
                steps = int(self.table.item(i, 5).text())
                if min_val >= max_val or steps < 2:
                    continue
                ranges.append(ParameterRange(
                    p.id, min_val, max_val, steps, p.unit
                ))
            except (ValueError, AttributeError):
                continue
        return ranges

    def _get_mode(self):
        """Return the selected mode string."""
        idx = self.mode_combo.currentIndex()
        return ["oat", "factorial", "random"][idx]

    def _update_estimate(self, *args):
        """Update the variation count estimate."""
        ranges = self._get_selected_ranges()
        mode = self._get_mode()

        if not ranges:
            self.estimate_label.setText("No parameters selected")
            return

        size = estimate_space_size(ranges, mode)
        if mode == "random":
            size = min(self.samples_spin.value(), size)

        color = "#2E7D32" if size <= 100 else "#E65100" if size <= 1000 else "#B71C1C"
        time_est = size * 0.7  # ~0.7s per variation based on our tests
        time_str = f"{time_est:.0f}s" if time_est < 60 else f"{time_est/60:.1f}min"

        self.estimate_label.setText(
            f"<span style='color:{color}'>"
            f"Variations: {size} | Est. time: ~{time_str}"
            f"</span>"
        )
        self._update_samples_visibility()

    def _update_samples_visibility(self):
        """Show/hide random samples spinbox based on mode."""
        is_random = self._get_mode() == "random"
        self.samples_spin.setVisible(is_random)

    def _apply_margin(self, pct):
        """Apply a percentage margin to all parameter ranges."""
        for i, p in enumerate(self.params):
            if p.unit == "deg":
                margin = pct * 0.5  # degrees
            else:
                margin = max(p.value * pct / 100.0, 0.5)
            min_val = max(0.1, p.value - margin)
            max_val = p.value + margin
            self.table.item(i, 3).setText(f"{min_val:.2f}")
            self.table.item(i, 4).setText(f"{max_val:.2f}")
        self._update_estimate()

    def _get_config_path(self):
        """Path for saving/loading config alongside the model."""
        doc = App.ActiveDocument
        if doc and doc.FileName:
            base = os.path.splitext(doc.FileName)[0]
            return base + "_robustness_config.json"
        return None

    def _save_config(self):
        """Save current configuration to JSON."""
        path = self._get_config_path()
        if not path:
            return
        config = {
            "mode": self._get_mode(),
            "n_samples": self.samples_spin.value(),
            "parameters": [],
        }
        for i, p in enumerate(self.params):
            cb = self.table.cellWidget(i, 0)
            config["parameters"].append({
                "id": p.id,
                "included": cb.isChecked(),
                "min": self.table.item(i, 3).text(),
                "max": self.table.item(i, 4).text(),
                "steps": self.table.item(i, 5).text(),
            })
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        App.Console.PrintMessage(f"Config saved to {path}\n")

    def _load_config(self):
        """Load configuration from JSON."""
        path = self._get_config_path()
        if not path or not os.path.exists(path):
            App.Console.PrintWarning("No config file found.\n")
            return
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Apply mode
        modes = {"oat": 0, "factorial": 1, "random": 2}
        self.mode_combo.setCurrentIndex(modes.get(config.get("mode", "oat"), 0))
        self.samples_spin.setValue(config.get("n_samples", 100))

        # Apply parameter configs
        param_configs = {pc["id"]: pc for pc in config.get("parameters", [])}
        for i, p in enumerate(self.params):
            pc = param_configs.get(p.id)
            if pc:
                self.table.cellWidget(i, 0).setChecked(pc.get("included", True))
                self.table.item(i, 3).setText(str(pc.get("min", "")))
                self.table.item(i, 4).setText(str(pc.get("max", "")))
                self.table.item(i, 5).setText(str(pc.get("steps", "5")))

        self._update_estimate()
        App.Console.PrintMessage(f"Config loaded from {path}\n")

    # Task panel interface methods

    def accept(self):
        """Called when OK is pressed. Launches analysis."""
        ranges = self._get_selected_ranges()
        if not ranges:
            QtGui.QMessageBox.warning(
                self.form, "No Parameters",
                "Select at least one parameter with valid ranges."
            )
            return False

        mode = self._get_mode()
        n_samples = self.samples_spin.value()
        nominal_values = {p.id: p.value for p in self.params
                         if p.id in {r.param_id for r in ranges}}

        # Store config for the analysis dialog to pick up
        self.form.setProperty("ranges", ranges)
        self.form.setProperty("mode", mode)
        self.form.setProperty("n_samples", n_samples)
        self.form.setProperty("nominal_values", nominal_values)
        self.form.setProperty("params", self.params)

        # Save config automatically
        self._save_config()

        Gui.Control.closeDialog()

        # Launch analysis
        from ui.analysis_dialog import run_analysis_dialog
        params_map = {p.id: p for p in self.params}
        run_analysis_dialog(ranges, params_map, mode, n_samples, nominal_values)
        return True

    def reject(self):
        """Called when Cancel is pressed."""
        Gui.Control.closeDialog()
        return True

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
