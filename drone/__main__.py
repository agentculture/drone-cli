"""Entry point for ``python -m drone``."""

from __future__ import annotations

import sys

from drone.cli import main

if __name__ == "__main__":
    sys.exit(main())
