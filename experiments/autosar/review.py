"""Root reviewer wrapper. See README.md; no model calls are performed."""
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True
if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parent/'offline/verify.py'), run_name='__main__')
