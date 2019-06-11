## Modules for test
import unittest
import aiounittest
import unittest.mock
import asyncio
from custom_mocks import get_mock_daemon

# Real Dependencies need for mock introspection
import git.cmd
import tempfile

# Modules to be tested
import gitdrop.merge as mut


class Test_Mergingtools(unittest.TestCase):

    def setUp(self,):
        self.daemon = get_mock_daemon(loopcount = 4)

    def test_do_merge_attempts_a_fastforward_merge(self,):
        self.daemon.rembranch = "REMOTEBRANCH"
        mut.do_merge(self.daemon)
        self.daemon.gitbackend.fast_forward_merge.assert_called_once()

    def test_do_merge_attempts_a_automerge_and_commit_if_fastforward_fails(self,):
        self.daemon.gitbackend.fast_forward_merge.return_value = False
        with unittest.mock.patch('gitdrop.merge.full_merge') as gmfm:
            self.daemon.rembranch = "REMOTEBRANCH"
            mut.do_merge(self.daemon)
        gmfm.assert_called_once_with(self.daemon)

    def test_full_merge_clones_repo_into_a_new_directory(self,):
        tdir = unittest.mock.MagicMock()
        tempdir = unittest.mock.patch('tempfile.TemporaryDirectory', return_value = tdir)
        with tempdir:
            mut.full_merge(self.daemon)
        #tempdir.assert_called_once()
        tdir.__enter__.assert_called_once()
        tdir.__exit__.assert_called_once()

        self.daemon.gitbackend.clone_to.assert_called_once_with(tdir.__enter__.return_value)

    def test_full_merge_calls_backend_does_proper_merge(self,):
        tdir = unittest.mock.MagicMock()
        tempdir = unittest.mock.patch('tempfile.TemporaryDirectory', return_value = tdir)
        with tempdir:
            mut.full_merge(self.daemon)


        self.daemon.gitbackend.merge_origin_on.assert_called_once_with(tdir.__enter__.return_value)


    def test_full_merge_calls_backend_does_proper_merge_after_clone(self,):
        cloned = False
        merged = False
        tdir = unittest.mock.MagicMock()
        tempdir = unittest.mock.patch('tempfile.TemporaryDirectory', return_value = tdir)
 
        def clone_to(dest):
            nonlocal cloned
            cloned = True
            self.assertEqual(dest,tdir.__enter__.return_value)

        def merge_on(dest):
            nonlocal merged
            merged = True
            self.assertTrue(cloned)
            self.assertEqual(dest,tdir.__enter__.return_value)

        self.daemon.gitbackend.clone_to = clone_to
        self.daemon.gitbackend.merge_origin_on = merge_on
        with tempdir:
            mut.full_merge(self.daemon)
        self.assertTrue(merged)
