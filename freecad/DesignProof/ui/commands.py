# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.
"""
FreeCAD Commands
================
Defines the GUI commands for the DesignProof workbench.
Each command is registered in init_gui.py.
"""

import os
import FreeCAD as App
import FreeCADGui as Gui

ICON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "Resources", "icons"
)


class CmdDetectParameters:
    """Command: Detect and configure parameters for robustness analysis."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICON_DIR, "detect_params.svg"),
            "MenuText": "Detect Parameters",
            "ToolTip": "Scan model for dimensional parameters and configure variation ranges",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            from .param_panel import ParameterPanel
        except ImportError:
            from ui.param_panel import ParameterPanel
        panel = ParameterPanel()
        Gui.Control.showDialog(panel)


class CmdRunAnalysis:
    """Command: Run robustness analysis on the active model."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICON_DIR, "run_analysis.svg"),
            "MenuText": "Run Analysis",
            "ToolTip": "Execute parameter variation test and generate robustness report",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            from .analysis_dialog import run_analysis_dialog
        except ImportError:
            from ui.analysis_dialog import run_analysis_dialog
        run_analysis_dialog()


class CmdModelMetrics:
    """Command: Show model complexity metrics."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICON_DIR, "metrics.svg"),
            "MenuText": "Model Metrics",
            "ToolTip": "Analyze feature dependencies and compute complexity metrics",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            from .metrics_dialog import show_metrics_dialog
        except ImportError:
            from ui.metrics_dialog import show_metrics_dialog
        show_metrics_dialog()


class CmdFocusedAnalysis:
    """Command: Focused robustness analysis on selected parameters."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICON_DIR, "focused_analysis.svg"),
            "MenuText": "Focused Analysis",
            "ToolTip": "Analyze robustness of selected parameters with dependency-aware variations",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            from .focused_panel import FocusedAnalysisPanel
        except ImportError:
            from ui.focused_panel import FocusedAnalysisPanel
        panel = FocusedAnalysisPanel()
        Gui.Control.showDialog(panel)
