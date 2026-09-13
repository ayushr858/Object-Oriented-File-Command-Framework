#!/usr/bin/env python3
"""Entry point: `python main.py` launches the interactive REPL."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from filecmd.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
