#!/usr/bin/env python3
"""
Type checking script for the invoice automation system.

This script runs mypy type checking on the codebase to ensure proper typing.
"""

import subprocess
import sys
from pathlib import Path


def run_type_checking() -> int:
    """Run mypy type checking on the codebase."""
    print("🔍 Running type checking with mypy...")
    
    # Define the source directory
    src_dir = Path("src")
    
    if not src_dir.exists():
        print("❌ Source directory 'src' not found!")
        return 1
    
    # Run mypy with strict settings
    cmd = [
        "mypy",
        "--strict",
        "--show-error-codes",
        "--show-column-numbers",
        "--pretty",
        str(src_dir)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Type checking passed! All types are correct.")
            return 0
        else:
            print("❌ Type checking failed!")
            print("\nSTDOUT:")
            print(result.stdout)
            print("\nSTDERR:")
            print(result.stderr)
            return result.returncode
            
    except FileNotFoundError:
        print("❌ mypy not found! Please install it with: pip install mypy")
        return 1
    except Exception as e:
        print(f"❌ Error running type checking: {e}")
        return 1


def main() -> int:
    """Main entry point."""
    print("🚀 Invoice Automation System - Type Checking")
    print("=" * 50)
    
    return run_type_checking()


if __name__ == "__main__":
    sys.exit(main())


