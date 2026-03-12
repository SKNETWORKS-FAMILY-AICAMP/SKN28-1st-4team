"""Shared pytest bootstrap for backend tests.

Pytest imports this module before collecting tests under `be/tests`, which lets
the test process resolve application imports from `be/src`.
"""

import sys
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
