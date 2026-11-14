# conftest.py — disable langsmith pytest plugin (blocked DLL on this system)
# This prevents the xxhash DLL from being loaded during test collection.

import sys
from unittest.mock import MagicMock

# Mock xxhash before langsmith can import it
sys.modules["xxhash"] = MagicMock()

