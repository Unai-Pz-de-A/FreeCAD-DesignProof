# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.

import freecad.DesignProof as module
from importlib.resources import as_file, files


_resources = files(module) / 'Resources'
_icons = _resources / 'icons'


def asIcon(name: str) -> str:
    """Resolve an icon name (without .svg) to its filesystem path."""
    icon = _icons / f'{name}.svg'
    with as_file(icon) as path:
        return str(path)
