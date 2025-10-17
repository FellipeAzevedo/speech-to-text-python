"""Compatibility wrapper for text_utils."""
from __future__ import annotations

from coqui_xtts_app.app.text_utils import *  # noqa: F401,F403

if __name__ == "__main__":  # pragma: no cover
    try:
        from coqui_xtts_app.app.text_utils import main as _main
    except ImportError:
        pass
    else:
        _main()
