# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.
"""
Focused Analysis Panel
======================
Task panel for focused robustness analysis: select key parameter(s),
discover related parameters via the dependency graph, and control
depth, variation %, and steps with sliders.
"""

import FreeCAD as App
import FreeCADGui as Gui

from PySide import QtCore, QtGui

try:
    from ..core.parameter_detector import detect_parameters
    from ..core.variation_engine import ParameterRange, estimate_space_size
    from ..core.dependency_analyzer import (
        build_graph, find_related_parameters, depth_from_node,
    )
except ImportError:
    from core.parameter_detector import detect_parameters
    from core.variation_engine import ParameterRange, estimate_space_size
    from core.dependency_analyzer import (
        build_graph, find_related_parameters, depth_from_node,
    )


class FocusedAnalysisPanel:
    """FreeCAD Task Panel for focused parameter analysis."""

    def __init__(self):
        self.all_params = []
        self.params_map = {}
        self.graph = None
        self._related = []  # [(Parameter, distance, direction), ...]

        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Focused Analysis")
        self._detect_data()
        self._build_ui()
        self._populate_key_table()

    def _detect_data(self):
        """Detect parameters and build dependency graph."""
        doc = App.ActiveDocument
        if doc is None:
            return
        self.all_params = detect_parameters(doc)
        self.params_map = {p.id: p for p in self.all_params}
        self.graph = build_graph(doc)

    # ================================================================
    # UI Construction
    # ================================================================

    def _build_ui(self):
        layout = QtGui.QVBoxLayout(self.form)

        # Info label
        self.info_label = QtGui.QLabel("Select key parameter(s) for focused analysis:")
        layout.addWidget(self.info_label)

        # --- Key parameter selection table ---
        self.key_table = QtGui.QTableWidget()
        self.key_table.setColumnCount(4)
        self.key_table.setHorizontalHeaderLabels(
            ["Include", "Parameter", "Value", "Source"]
        )
        self.key_table.horizontalHeader().setStretchLastSection(True)
        self.key_table.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.key_table.verticalHeader().setVisible(False)
        layout.addWidget(self.key_table)

        # --- Analysis Controls ---
        controls_group = QtGui.QGroupBox("Analysis Controls")
        controls_layout = QtGui.QVBoxLayout()

        # Depth slider
        depth_row = QtGui.QHBoxLayout()
        depth_row.addWidget(QtGui.QLabel("Depth:"))
        self.depth_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.depth_slider.setRange(0, 0)
        self.depth_slider.setValue(0)
        self.depth_slider.setTickPosition(QtGui.QSlider.TicksBelow)
        self.depth_slider.setTickInterval(1)
        depth_row.addWidget(self.depth_slider)
        self.depth_label = QtGui.QLabel("[0]")
        self.depth_label.setMinimumWidth(30)
        depth_row.addWidget(self.depth_label)
        controls_layout.addLayout(depth_row)

        # Variation slider
        var_row = QtGui.QHBoxLayout()
        var_row.addWidget(QtGui.QLabel("Variation:"))
        self.var_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.var_slider.setRange(5, 50)
        self.var_slider.setValue(30)
        self.var_slider.setSingleStep(5)
        self.var_slider.setTickPosition(QtGui.QSlider.TicksBelow)
        self.var_slider.setTickInterval(5)
        var_row.addWidget(self.var_slider)
        self.var_label = QtGui.QLabel("[±30%]")
        self.var_label.setMinimumWidth(50)
        var_row.addWidget(self.var_label)
        controls_layout.addLayout(var_row)

        # Steps slider
        steps_row = QtGui.QHBoxLayout()
        steps_row.addWidget(QtGui.QLabel("Steps:"))
        self.steps_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.steps_slider.setRange(3, 10)
        self.steps_slider.setValue(5)
        self.steps_slider.setTickPosition(QtGui.QSlider.TicksBelow)
        self.steps_slider.setTickInterval(1)
        steps_row.addWidget(self.steps_slider)
        self.steps_label = QtGui.QLabel("[5]")
        self.steps_label.setMinimumWidth(30)
        steps_row.addWidget(self.steps_label)
        controls_layout.addLayout(steps_row)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # --- Related parameters ---
        self.related_group = QtGui.QGroupBox("Related Parameters Found (0)")
        related_layout = QtGui.QVBoxLayout()

        self.related_table = QtGui.QTableWidget()
        self.related_table.setColumnCount(4)
        self.related_table.setHorizontalHeaderLabels(
            ["Parameter", "Value", "Depth", "Direction"]
        )
        self.related_table.horizontalHeader().setStretchLastSection(True)
        self.related_table.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.related_table.verticalHeader().setVisible(False)
        self.related_table.setMaximumHeight(150)
        self.related_table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        related_layout.addWidget(self.related_table)
        self.related_group.setLayout(related_layout)
        layout.addWidget(self.related_group)

        # --- Live view checkbox ---
        self.live_view_cb = QtGui.QCheckBox("Update 3D view during analysis (slower)")
        self.live_view_cb.setChecked(False)
        layout.addWidget(self.live_view_cb)

        # --- Estimation label ---
        self.estimate_label = QtGui.QLabel("")
        self.estimate_label.setWordWrap(True)
        layout.addWidget(self.estimate_label)

        layout.addStretch()

        # --- Signals ---
        self.depth_slider.valueChanged.connect(self._on_depth_changed)
        self.var_slider.valueChanged.connect(self._on_variation_changed)
        self.steps_slider.valueChanged.connect(self._on_steps_changed)

    def _populate_key_table(self):
        """Fill the key parameter table with detected parameters."""
        if not self.all_params:
            self.info_label.setText("No parameters detected in this model.")
            return

        self.key_table.setRowCount(len(self.all_params))

        for i, p in enumerate(self.all_params):
            # Column 0: Checkbox
            cb = QtGui.QCheckBox()
            cb.setChecked(False)
            cb.stateChanged.connect(self._on_selection_changed)
            cb.stateChanged.connect(lambda state, idx=i: self._highlight_param(idx, state))
            self.key_table.setCellWidget(i, 0, cb)

            # Column 1: Parameter label (read-only)
            label_item = QtGui.QTableWidgetItem(p.label)
            label_item.setFlags(label_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.key_table.setItem(i, 1, label_item)

            # Column 2: Current value (read-only)
            val_str = f"{p.value:.2f} {p.unit}"
            val_item = QtGui.QTableWidgetItem(val_str)
            val_item.setFlags(val_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.key_table.setItem(i, 2, val_item)

            # Column 3: Source object (read-only)
            src_item = QtGui.QTableWidgetItem(p.source_name)
            src_item.setFlags(src_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.key_table.setItem(i, 3, src_item)

        self.key_table.resizeColumnsToContents()
        # Give more space to Parameter column
        self.key_table.setColumnWidth(1, 180)

    # ================================================================
    # Signal Handlers
    # ================================================================

    def _on_selection_changed(self):
        """Called when a key parameter checkbox changes."""
        self._update_depth_range()
        self._refresh_related()
        self._update_estimate()

    def _on_depth_changed(self, value):
        self.depth_label.setText(f"[{value}]")
        self._refresh_related()
        self._update_estimate()

    def _on_variation_changed(self, value):
        self.var_label.setText(f"[±{value}%]")
        self._update_estimate()

    def _on_steps_changed(self, value):
        self.steps_label.setText(f"[{value}]")
        self._update_estimate()

    # ================================================================
    # Core Logic
    # ================================================================

    def _get_selected_param_ids(self):
        """Return IDs of checked key parameters."""
        selected = []
        for i, p in enumerate(self.all_params):
            cb = self.key_table.cellWidget(i, 0)
            if cb and cb.isChecked():
                selected.append(p.id)
        return selected

    def _update_depth_range(self):
        """Update depth slider max based on selected params."""
        selected_ids = self._get_selected_param_ids()
        if not selected_ids or not self.graph:
            self.depth_slider.setRange(0, 0)
            return

        max_d = 0
        for pid in selected_ids:
            param = self.params_map.get(pid)
            if param:
                d = depth_from_node(self.graph, param.source_name)
                max_d = max(max_d, d)

        self.depth_slider.setRange(0, max(max_d, 0))
        if self.depth_slider.value() > max_d:
            self.depth_slider.setValue(max_d)

    def _refresh_related(self):
        """Find and display related parameters based on current selection + depth."""
        selected_ids = self._get_selected_param_ids()
        depth = self.depth_slider.value()

        if not selected_ids or not self.graph:
            self._related = []
            self.related_table.setRowCount(0)
            self.related_group.setTitle("Related Parameters Found (0)")
            return

        self._related = find_related_parameters(
            self.graph, self.all_params, selected_ids, depth
        )

        # Populate related table
        self.related_table.setRowCount(len(self._related))
        for i, (p, dist, direction) in enumerate(self._related):
            self.related_table.setItem(
                i, 0, QtGui.QTableWidgetItem(p.label)
            )
            self.related_table.setItem(
                i, 1, QtGui.QTableWidgetItem(f"{p.value:.2f} {p.unit}")
            )
            self.related_table.setItem(
                i, 2, QtGui.QTableWidgetItem(str(dist))
            )
            self.related_table.setItem(
                i, 3, QtGui.QTableWidgetItem(direction)
            )

        self.related_table.resizeColumnsToContents()
        self.related_group.setTitle(
            f"Related Parameters Found ({len(self._related)})"
        )

    def _select_mode(self, total_params):
        """Auto-select variation mode based on parameter count."""
        steps = self.steps_slider.value()

        if total_params <= 1:
            return "oat", None

        factorial_size = steps ** total_params
        if total_params <= 4 and factorial_size <= 1000:
            return "factorial", None

        if factorial_size <= 1000:
            return "factorial", None

        return "random", 500

    def _build_ranges(self):
        """Build ParameterRange for all included params (key + related)."""
        selected_ids = self._get_selected_param_ids()
        var_pct = self.var_slider.value() / 100.0
        steps = self.steps_slider.value()

        # Collect all params: selected + related
        all_param_ids = set(selected_ids)
        for p, _dist, _dir in self._related:
            all_param_ids.add(p.id)

        ranges = []
        for pid in all_param_ids:
            p = self.params_map.get(pid)
            if not p or p.value == 0:
                continue

            abs_val = abs(p.value)
            if p.unit == "deg":
                margin = abs_val * var_pct * 0.5
            else:
                margin = max(abs_val * var_pct, 1.0)

            min_val = p.value - margin
            max_val = p.value + margin

            if p.unit != "deg":
                min_val = max(0.1, min_val)

            if min_val >= max_val:
                continue

            ranges.append(ParameterRange(
                param_id=pid,
                min_val=round(min_val, 2),
                max_val=round(max_val, 2),
                steps=steps,
                unit=p.unit,
            ))

        return ranges

    def _update_estimate(self):
        """Update the estimation label with variation count and time."""
        selected_ids = self._get_selected_param_ids()
        if not selected_ids:
            self.estimate_label.setText("")
            return

        ranges = self._build_ranges()
        if not ranges:
            self.estimate_label.setText("No valid ranges.")
            return

        total_params = len(ranges)
        mode, n_samples = self._select_mode(total_params)

        size = estimate_space_size(ranges, mode)
        if mode == "random" and n_samples:
            size = min(n_samples, size)

        time_est = size * 0.3  # ~0.3s per variation average
        key_count = len(selected_ids)
        related_count = total_params - key_count

        mode_label = {"oat": "OAT", "factorial": "Factorial", "random": "Random"}.get(mode, mode)

        text = (
            f"<b>{total_params} params</b> "
            f"({key_count} key + {related_count} related) | "
            f"Mode: {mode_label} | "
            f"<b>{size} variations</b> | "
            f"Est: ~{time_est:.0f}s"
        )

        if size > 500:
            text = f'<span style="color: #cc6600;">{text}</span>'

        self.estimate_label.setText(text)

    # ================================================================
    # Task Panel Interface
    # ================================================================

    def accept(self):
        """Called when OK is pressed."""
        selected_ids = self._get_selected_param_ids()
        if not selected_ids:
            QtGui.QMessageBox.warning(
                self.form, "No Parameters",
                "Select at least one key parameter."
            )
            return False

        ranges = self._build_ranges()
        if not ranges:
            QtGui.QMessageBox.warning(
                self.form, "No Valid Ranges",
                "Could not build valid parameter ranges."
            )
            return False

        total_params = len(ranges)
        mode, n_samples = self._select_mode(total_params)

        # Nominal values = current values
        nominal_values = {}
        for r in ranges:
            p = self.params_map.get(r.param_id)
            if p:
                nominal_values[p.id] = p.value

        live_view = self.live_view_cb.isChecked()

        Gui.Control.closeDialog()

        try:
            from .analysis_dialog import run_analysis_dialog
        except ImportError:
            from ui.analysis_dialog import run_analysis_dialog
        run_analysis_dialog(
            ranges, self.params_map, mode,
            n_samples or 100, nominal_values,
            live_view=live_view,
        )
        return True

    def reject(self):
        """Called when Cancel is pressed."""
        Gui.Control.closeDialog()
        return True

    def getStandardButtons(self):
        return int(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )
