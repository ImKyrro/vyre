import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vyre import bootstrap

if not bootstrap.ensure():
    print("Vyre could not install its requirements automatically.")
    print("Run:  pip install -r requirements.txt")
    sys.exit(1)

from vyre.app import run

if __name__ == "__main__":
    sys.exit(run())
