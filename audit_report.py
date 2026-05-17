#!/usr/bin/env python3
"""
Thin shim for direct invocation: python3 audit_report.py [args]
The actual code lives in mfaudit/cli.py.
If you installed via pip, use the `mfaudit` command instead.
"""
from mfaudit.cli import main

if __name__ == "__main__":
    main()
