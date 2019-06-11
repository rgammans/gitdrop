"""
The clever part of gitdrop.

This is the part of the code which merghe remote and local
changes  (if possible)
"""
import tempfile

def do_merge(daemon):
    if not daemon.gitbackend.fast_forward_merge():
        full_merge(daemon)


def full_merge(daemon):
    # Use tempdirectory to merge without worryiing about
    # racing with the users saves.
    with tempfile.TemporaryDirectory() as tmpdir:
        daemon.gitbackend.clone_to(tmpdir)
        daemon.gitbackend.merge_origin_on(tmpdir)
