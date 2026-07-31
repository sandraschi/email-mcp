#!/usr/bin/env python3
"""Test runner for minimail-mcp."""

import os
import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run the test suite."""
    # Change to the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Run pytest
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    result = subprocess.run(cmd, capture_output=False)

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
