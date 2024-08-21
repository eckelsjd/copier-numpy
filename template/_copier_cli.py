"""Run copier CLI from its Python interface (copier is installed in .venv)"""
from copier.cli import CopierApp
import sys


_, retval = CopierApp.run(["copier"] + sys.argv[1:], exit=False)
if retval != 0:
    raise RuntimeError("Copier exited with non-zero status code")
