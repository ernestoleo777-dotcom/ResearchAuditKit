"""Launch the Action-owned CLI without importing from the audited workspace."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

ACTION_ROOT = Path(__file__).resolve().parents[1]
ACTION_SOURCE = ACTION_ROOT / "src"
sys.path.insert(0, str(ACTION_SOURCE))
main = import_module("research_audit_kit.cli").main


if __name__ == "__main__":
    raise SystemExit(main())
