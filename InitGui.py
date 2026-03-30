import FreeCADGui as Gui


class DesignProofWorkbench(Gui.Workbench):
    import os
    import sys
    import FreeCAD

    _wb_dir = os.path.join(
        FreeCAD.getUserAppDataDir(), "Mod", "DesignProof"
    )

    MenuText = "DesignProof"
    ToolTip = "Proof-test your parametric CAD models"
    Icon = os.path.join(_wb_dir, "Resources", "icons", "workbench.svg")

    if _wb_dir not in sys.path:
        sys.path.insert(0, _wb_dir)

    def Initialize(self):
        try:
            from ui.commands import (
                CmdDetectParameters,
                CmdRunAnalysis,
                CmdModelMetrics,
            )

            Gui.addCommand("DP_DetectParameters", CmdDetectParameters())
            Gui.addCommand("DP_RunAnalysis", CmdRunAnalysis())
            Gui.addCommand("DP_ModelMetrics", CmdModelMetrics())

            self.appendToolbar("DesignProof", [
                "DP_DetectParameters",
                "DP_RunAnalysis",
                "Separator",
                "DP_ModelMetrics",
            ])

            self.appendMenu("DesignProof", [
                "DP_DetectParameters",
                "DP_RunAnalysis",
                "Separator",
                "DP_ModelMetrics",
            ])

            self.FreeCAD.Console.PrintMessage(
                "[DesignProof] Workbench initialized.\n"
            )
        except Exception as e:
            self.FreeCAD.Console.PrintError(
                f"[DesignProof] Initialize error: {e}\n"
            )

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(DesignProofWorkbench())
