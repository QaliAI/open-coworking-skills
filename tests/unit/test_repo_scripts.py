"""Repo-script contract tests (audit addition).

AGENTS.md requires every script to support --help and return meaningful
exit codes; the original build never verified this mechanically.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = sorted((REPO / "scripts").glob("*.py"))


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_supports_help(script):
    r = subprocess.run([sys.executable, str(script), "--help"],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"{script.name} --help exited {r.returncode}: {r.stderr[:200]}"
    assert r.stdout.strip(), f"{script.name} --help produced no output"


def test_scripts_exist():
    assert len(SCRIPTS) >= 6
