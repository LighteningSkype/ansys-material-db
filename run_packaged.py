"""Packaged entry point — used by PyInstaller to launch the app.

When frozen (compiled to exe), sys._MEIPASS points to the temp
directory where PyInstaller extracts bundled files.  We add the
`src` directory to sys.path so that `ansys_material_db` can
be imported normally.
"""

import os
import sys


def _setup_path() -> None:
    """Ensure the src package is importable in frozen & dev modes."""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        # Running from source
        base = os.path.dirname(os.path.abspath(__file__))

    src_dir = os.path.join(base, 'src')
    if os.path.isdir(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    elif base not in sys.path:
        sys.path.insert(0, base)


_setup_path()

from ansys_material_db.main import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())