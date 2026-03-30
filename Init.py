# DesignProof workbench - Init
# This file is loaded when FreeCAD starts (GUI and non-GUI mode)
# Note: FreeCAD exec()s this file, so __file__ is NOT available.

import os
import sys
import FreeCAD as App

# Find workbench directory via FreeCAD's API (since __file__ is not set)
_wb_dir = os.path.join(App.getUserAppDataDir(), "Mod", "DesignProof")
if not os.path.isdir(_wb_dir):
    _wb_dir = os.path.join(App.getHomePath(), "Mod", "DesignProof")

if os.path.isdir(_wb_dir) and _wb_dir not in sys.path:
    sys.path.insert(0, _wb_dir)
