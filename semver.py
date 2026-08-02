#!/usr/bin/env python3
"""Thin CLI shim for the semantic versioning workflow.

The implementation lives in vs_repo_tooling.versioning; this file exists so
`python ./semver.py` keeps working for consumers (e.g. build-dev-publish.sh)
that invoke it directly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src" / "python"))

from vs_repo_tooling.versioning.cli import main

if __name__ == "__main__":
    main()
