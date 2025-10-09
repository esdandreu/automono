#!/usr/bin/env python3
"""
Test runner for simple Repsol login test.
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

# Import and run the simple login test
from integration.adapters.costs_sources.test_repsol_simple_login import test_repsol_login

if __name__ == "__main__":
    success = test_repsol_login()
    if success:
        print("Simple login test completed successfully")
    else:
        print("Simple login test failed")
        sys.exit(1)
