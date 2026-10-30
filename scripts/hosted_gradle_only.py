#!/usr/bin/env python3
"""Fail closed for legacy local build task aliases (not a remote dispatcher)."""
import sys
print('HOSTED_GRADLE_ONLY: local Gradle disabled. Run ./devtoolw remote-debug-plan and then ./devtoolw remote-debug-build --yes after committing and pushing.',file=sys.stderr)
raise SystemExit(2)
