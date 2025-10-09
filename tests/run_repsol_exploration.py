#!/usr/bin/env python3
"""
Test runner for Repsol exploration tests.
"""

import os
import sys
from pathlib import Path

# Set environment variables
os.environ['REPSOL_USERNAME'] = 'esdandreu@gmail.com'
os.environ['REPSOL_PASSWORD'] = 'ibpOb_KnCOA12Q2Rv0sk'

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Import and run the exploration test
from integration.adapters.costs_sources.test_repsol_explore import main

if __name__ == "__main__":
    main()
