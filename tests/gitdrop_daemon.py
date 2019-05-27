## Modules for test
import unittest


# Modules to be tested
import gitdrop.daemon as mut


class TestDaemonClass(unittest.TestCase):
    def test_daemon_constructs_with_a_valid_path(self,):
        mut.Daemon('/tmp')

