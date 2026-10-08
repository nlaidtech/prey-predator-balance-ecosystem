"""Root launcher for Predator-Prey Wildlife Balance Ecosystem.

Allows running directly via:
    python main.py
or double-clicking main.py in File Explorer.
"""

import os
import sys

# Ensure root directory is on Python module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
