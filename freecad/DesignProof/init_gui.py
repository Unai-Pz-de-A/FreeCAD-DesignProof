# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.

import os

import FreeCADGui as Gui


class DesignProofWorkbench(Gui.Workbench):
    MenuText = "DesignProof"
    ToolTip = "Proof-test your parametric CAD models"
    Icon = os.path.join(
        os.path.dirname(__file__), "Resources", "icons", "workbench.svg"
    )

    def Initialize(self):
        try:
            try:
                from .ui.commands import (
                    CmdDetectParameters,
                    CmdFocusedAnalysis,
                    CmdModelMetrics,
                    CmdRunAnalysis,
                )
            except ImportError:
                from ui.commands import (
                    CmdDetectParameters,
                    CmdFocusedAnalysis,
                    CmdModelMetrics,
                    CmdRunAnalysis,
                )

            Gui.addCommand("DP_DetectParameters", CmdDetectParameters())
            Gui.addCommand("DP_RunAnalysis", CmdRunAnalysis())
            Gui.addCommand("DP_FocusedAnalysis", CmdFocusedAnalysis())
            Gui.addCommand("DP_ModelMetrics", CmdModelMetrics())

            self.appendToolbar("DesignProof", [
                "DP_DetectParameters",
                "DP_RunAnalysis",
                "DP_FocusedAnalysis",
                "Separator",
                "DP_ModelMetrics",
            ])

            self.appendMenu("DesignProof", [
                "DP_DetectParameters",
                "DP_RunAnalysis",
                "DP_FocusedAnalysis",
                "Separator",
                "DP_ModelMetrics",
            ])
        except Exception as exc:
            import FreeCAD as App

            App.Console.PrintError(
                f"[DesignProof] Initialize error: {exc}\n"
            )

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(DesignProofWorkbench())
