# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.

import FreeCADGui as Gui

from .resources import asIcon


class DesignProofWorkbench(Gui.Workbench):
    MenuText = "DesignProof"
    ToolTip = "Proof-test your parametric CAD models"
    Icon = asIcon("workbench")

    def Initialize(self):
        try:
            from .ui.commands import (
                CmdDetectParameters,
                CmdFocusedAnalysis,
                CmdModelMetrics,
                CmdRunAnalysis,
            )

            Gui.addCommand("DesignProof_DetectParameters", CmdDetectParameters())
            Gui.addCommand("DesignProof_RunAnalysis", CmdRunAnalysis())
            Gui.addCommand("DesignProof_FocusedAnalysis", CmdFocusedAnalysis())
            Gui.addCommand("DesignProof_ModelMetrics", CmdModelMetrics())

            self.appendToolbar("DesignProof", [
                "DesignProof_DetectParameters",
                "DesignProof_RunAnalysis",
                "DesignProof_FocusedAnalysis",
                "Separator",
                "DesignProof_ModelMetrics",
            ])

            self.appendMenu("DesignProof", [
                "DesignProof_DetectParameters",
                "DesignProof_RunAnalysis",
                "DesignProof_FocusedAnalysis",
                "Separator",
                "DesignProof_ModelMetrics",
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
