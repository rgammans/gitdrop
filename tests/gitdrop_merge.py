## Modules for test
import unittest
import aiounittest
import unittest.mock
import asyncio
from custom_mocks import get_mock_daemon

# Real Dependencies need for mock introspection
import git.cmd

# Modules to be tested
import gitdrop.merge as mut


class Test_Mergingtools(unittest.TestCase):


    def test_do_merge_attempts_a_fastforward_merge(self,):
        daemon = get_mock_daemon(loopcount = 4)
        daemon.rembranch = "REMOTEBRANCH"
        mut.do_merge(daemon)
        daemon.gitbackend.fast_forward_merge()
