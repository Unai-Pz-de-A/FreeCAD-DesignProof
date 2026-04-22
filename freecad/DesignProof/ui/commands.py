# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.
"""
FreeCAD Commands
================
Defines the GUI commands for the DesignProof workbench.
Each command is registered in init_gui.py.
"""

import FreeCAD as App
import FreeCADGui as Gui

from ..resources import asIcon


class CmdDetectParameters:
    """Command: Detect and configure parameters for robustness analysis."""

    def GetResources(self):
        return {
            "Pixmap": asIcon("detect_params"),
            "MenuText": "Detect Parameters",
            "ToolTip": "Scan model for dimensional parameters and configure variation ranges",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        from .param_panel import ParameterPanel
        panel = ParameterPanel()
        Gui.Control.showDialog(panel)


class CmdRunAnalysis:
    """Command: Run robustness analysis on the active model."""

    def GetResources(self):
        return {
            "Pixmap": asIcon("run_analysis"),
            "MenuText": "Run Analysis",
            "ToolTip": "Execute parameter variation test and generate robustness report",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        from .analysis_dialog import run_analysis_dialog
        run_analysis_dialog()


class CmdModelMetrics:
    """Command: Show model complexity metrics."""

    def GetResources(self):
        return {
            "Pixmap": asIcon("metrics"),
            "MenuText": "Model Metrics",
            "ToolTip": "Analyze feature dependencies and compute complexity metrics",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        from .metrics_dialog import show_metrics_dialog
        show_metrics_dialog()


class CmdFocusedAnalysis:
    """Command: Focused robustness analysis on selected parameters."""

    def GetResources(self):
        return {
            "Pixmap": asIcon("focused_analysis"),
            "MenuText": "Focused Analysis",
            "ToolTip": "Analyze robustness of selected parameters with dependency-aware variations",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        from .focused_panel import FocusedAnalysisPanel
        panel = FocusedAnalysisPanel()
        Gui.Control.showDialog(panel)
