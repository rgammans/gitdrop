## Modules for test
import unittest
import unittest.mock
import tempfile
import os
import asyncio
import threading

# Real Dependencies need for mock introspection
import git.cmd
import inotify.adapters


# Modules to be tested
import gitdrop.daemon as mut


class TestDaemonClass(unittest.TestCase):

    def setUp(self,):
        self.tdir_cntxt = tempfile.TemporaryDirectory()
        self.tdir =self.tdir_cntxt.__enter__()

    def tearDown(self,):
        self.tdir_cntxt.__exit__(None,None,None)

    def test_daemon_constructs_with_a_valid_path(self,):
        g = git.cmd.Git(self.tdir)
        g.init()
        mut.Daemon(self.tdir)


    def test_daemon_raises_and_execption_on_construction_with_an_inavalid_path(self):
        with self.assertRaises(RuntimeError):
            mut.Daemon("/nosuch-path")



    def test_daemon_raises_and_execption_on_construction_with_an_valid_path_wiht_no_dotgit_dir(self):
        with self.assertRaises(RuntimeError):
            mut.Daemon(self.tdir)

    def test_daemon_raises_and_execption_on_construction_if_the_repo_branchs_cant_be_configured(self):
        ## The daemon should make the checked out branch track a remote branch
        # - so this is null; and we have other need underneat
        pass

    def test_daemon_creates_a_uniquely_named_brnch_if_the_repo_is_on_a_detached_head(self):
        ## Create detached HEAD State.
        g = git.cmd.Git(self.tdir)
        g.init()
        with open(os.path.join(self.tdir,"a"),"w"):
            # Create empty file
            pass
        g.add(["a"])
        g.commit(["-m","Add a"])
        g.checkout(["--detach"])

        ## Now start gitdrop cless
        with unittest.mock.patch('gitdrop.daemon.Daemon._uniquename', return_value="branch_foo") as un:
            mut.Daemon(self.tdir)
            status = g.status()
            self.assertFalse("detached" in status)
            un.assert_called_once()

    @unittest.skip("nyi")
    def test_daemon_raises_and_execption_on_construction_if_the_provided_remote_is_inreachable(self):
        ## We only care about this at startup; as a sort of sanity check
        #  if the remote goes unreachable during operation; thjat's fine although
        # the use needs to be alerted
        self.fail()

    def test_daemon_does_and_initial_remote_pull(self,):
        remote = unittest.mock.sentinel.REMOTE
        branch = unittest.mock.sentinel.BRANCH
        g = git.cmd.Git(self.tdir)
        g.init()
        try:
            git.cmd.Git.pull = unittest.mock.MagicMock(inotify.adapters.InotifyTree)
            mut.Daemon(self.tdir, remote, branch)
            git.cmd.Git.pull.assert_called_once_with([remote,branch])
        finally:
            del git.cmd.Git.pull


    def test_daemon_starts_an_inotify_watcher_on_the_directory(self,):
        g = git.cmd.Git(self.tdir)
        g.init()
        x = unittest.mock.MagicMock(inotify.adapters.InotifyTree)
        with unittest.mock.patch('inotify.adapters.InotifyTree', return_value=x) as un:
            mut.Daemon(self.tdir)
        un.assert_called_once()


   
    @unittest.skip('nyi')
    def test_triggers_a_fetch_from_remote_after_30secs_if_no_acrtions(self,):
        self.fail()


    @unittest.skip('nyi')
    def test_triggers_id_a_remote_fecths_is_nonempty_calls_merge_remote(self,):
        self.fail()

    @unittest.skip('nyi')
    def test_after_a_local_change_amonstable_timer_is_reset(self,):
        self.fail()

    @unittest.skip('nyi')
    def test_after_a_the_monostable_timer_completes_changes_are_added_and_commited_to_git_and_a_remote_uipdate_cylce(self,):
        ## Eg check calls to the local commit; and remote udpate fumctiosn
        self.fail()


class TestDaemon_istance_methods(unittest.TestCase):
    def setUp(self,):
        self.tdir_cntxt = tempfile.TemporaryDirectory()
        tdir =self.tdir_cntxt.__enter__()
        g = git.cmd.Git(tdir)
        g.init()
        with open(os.path.join(tdir,"a"),"w"):
            # Create empty file
            pass
        g.add(["a"])
        g.commit(["-m","Add a"])
        self.out = mut.Daemon(tdir)

    def tearDown(self,):
        self.out.stop()
        self.tdir_cntxt.__exit__(None,None,None)


    def test_run_with_no_asyncio_event_loop_starts_an_event_loop(self,):
        mainloop = unittest.mock.MagicMock()
        with unittest.mock.patch('asyncio.run', return_value="branch_foo") as un ,\
             unittest.mock.patch.object(self.out, 'async_main' ,return_value=mainloop) as ml:
            self.out.run()
        un.assert_called_once()

    def test_run_starts_the_main_async_task(self,):
        mainloop = unittest.mock.MagicMock()
        with unittest.mock.patch('asyncio.run', return_value="branch_foo") as un ,\
             unittest.mock.patch.object(self.out, 'async_main' ,return_value=mainloop) as ml:
            self.out.run()

        un.assert_called_once_with(mainloop)

    def test_async_main_queues_the_remote_watch_co_routine(self,):
        mainloop = unittest.mock.MagicMock()
        with unittest.mock.patch('asyncio.create_task', return_value="branch_foo") as un ,\
             unittest.mock.patch.object(self.out, 'remote_watch' ,return_value=mainloop) ,\
             unittest.mock.patch.object(self.out, 'local_watch' ,return_value=None):
             self.out.async_main().send(None)

        un.assert_any_call(mainloop)


    def test_async_main_queues_the_local_watch_co_routine(self,):
        mainloop = unittest.mock.MagicMock()
        with unittest.mock.patch('asyncio.create_task', return_value="branch_foo") as un ,\
             unittest.mock.patch.object(self.out, 'remote_watch' ,return_value=None) ,\
             unittest.mock.patch.object(self.out, 'local_watch' ,return_value=mainloop):
             self.out.async_main().send(None)

        un.assert_any_call(mainloop)



class TestDaemonClass_satic_class_methods(unittest.TestCase):
    """ This si sort of a test for randomise; so is as yet unimplemented"""
    @unittest.skip('nyi')
    def test_uniqnue_name_apprporirately_unique(self,):
        self.fail()
