"""Compatibility wrapper for config."""
from __future__ import annotations

from coqui_xtts_app.app.config import *  # noqa: F401,F403

if __name__ == "__main__":  # pragma: no cover
    try:
        from coqui_xtts_app.app.config import main as _main
    except ImportError:
        pass
    else:
        _main()
