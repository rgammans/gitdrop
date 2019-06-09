"""
The clever part of gitdrop.

This is the part of the code which merghe remote and local
changes  (if possible)
"""


def do_merge(daemon):
    daemon.gitbackend.fast_forward_merge()

