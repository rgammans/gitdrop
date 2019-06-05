
import os
import sys
from .daemon import Daemon


if __name__ == "__main__":
    args = sys.argv[1:]
    print(args)
    if not args:
        args = [ os.getcwd() ]
    Daemon(*args).run()

