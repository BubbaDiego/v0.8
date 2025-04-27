# /tests/conftest.py

import sys
import os

# Automatically fix sys.path for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
