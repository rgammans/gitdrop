
import os
import sys
from .daemon import Daemon
import argparse
import logging

rootlogger = logging.getLogger('gitdrop')
rootlogger.addHandler(logging.StreamHandler())

def get_parser( ):
    parser = argparse.ArgumentParser(
            description='Automatic git daemon for non-geeks')
    parser.add_argument('path', type=str, default='.')
    parser.add_argument('--remote-branch','-b', dest="branch",type = str, default=None)
    parser.add_argument('--remote','-r', dest="remote",type = str, default=None)
    parser.add_argument('--debug', action='store_const', const=True,)

    return  parser



if __name__ == "__main__":
    parser = get_parser()
    options = parser.parse_args()
    print (options)
    if options.debug:
        rootlogger.setLevel(logging.DEBUG)
    rootlogger.debug("Starting up..")
    Daemon(options.path, remote = options.remote, branch = options.branch).run()

