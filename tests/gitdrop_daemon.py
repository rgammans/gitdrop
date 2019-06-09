## Modules for test
import unittest
import unittest.mock
import tempfile
import os
import asyncio
import threading
import aiounittest

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


class Tests_withDaemon_instances(unittest.TestCase):
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
        self.loop =None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self,):
        self.out.stop()
        self.tdir_cntxt.__exit__(None,None,None)
        if self.loop:
            self.loop.close()




class TestDaemon_instance_methods(Tests_withDaemon_instances):
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


    @unittest.skip('nyi')
    def test_run_handles_keyboard_interrupt_cleanly_and_singles_shutdown_everywhere_needed(self,):
        self.fail()

    #@unittest.skip("")
    def test_async_main_queues_the_remote_watch_co_routine(self,):
        mainloop = unittest.mock.MagicMock()
        with unittest.mock.patch('asyncio.create_task', return_value="branch_foo") as un ,\
             unittest.mock.patch.object(self.out, 'remote_watch' ,return_value=mainloop) ,\
             unittest.mock.patch.object(self.out, 'local_watch' ,return_value=None):
             self.out.async_main().send(None)

        un.assert_any_call(mainloop)


    def test_async_main_queues_the_local_watch_co_routine(self,):
        localloop = unittest.mock.MagicMock()
        with unittest.mock.patch('asyncio.create_task', return_value="branch_foo") as un ,\
             unittest.mock.patch.object(self.out, 'remote_watch' , return_value=None) ,\
             unittest.mock.patch.object(self.out, 'local_watch' ,return_value=localloop):

                self.out.async_main().send(None)

        un.assert_any_call(localloop)


    def test_localwatch_launches_a_thread_to_listen_for_inotify_changes(self,):
        ## I reconsidered inotify for a async looking at aionotify and butter
        #  but they didn't seem as well maintained so I decided to take
        # sub trhread appraoch. This means local_watch is a async function
        # which launches a thread; whcih pokes tasks into the loop.
        with unittest.mock.patch('asyncio.get_event_loop',
                                 return_value=unittest.mock.sentinel.LOOP) ,\
             unittest.mock.patch.object(self.out, 'run_inotify' ,return_value=None
                                       ) as thread_starter:
            #, \ self.assertRaises(StopIteration):
                asyncio.run(self.out.local_watch(), debug = True)

        thread_starter.assert_called_once_with(unittest.mock.sentinel.LOOP)


    def test_remotewatch_launches_the_remote_loop(self,):
        with unittest.mock.patch.object(mut.gdr, 'remote_watcher', return_value= aiounittest.futurized(None)) as remote:
             asyncio.run(self.out.remote_watch(), debug = True)

        remote.assert_called_once_with(self.out)


    def test_run_inotify_creates_a_thread_and_runs_it(self):
        async_loop = None
        async def run_async():
            nonlocal async_loop
            loop = asyncio.get_event_loop()
            async_loop = loop
            self.out.stop()
            self.out.run_inotify(loop)

        with unittest.mock.patch('gitdrop.inotify.WatchThread') as thread_obj_create:
            asyncio.run( run_async())

        thread_obj_create.assert_called_once_with(async_loop, self.out.iwatch)
        thread_obj_create.return_value.start.assert_called_once()


class TestDaemonClass_static_class_methods(unittest.TestCase):
    """ This si sort of a test for randomise; so is as yet unimplemented"""
    @unittest.skip('nyi')
    def test_uniqnue_name_appropriately_unique(self,):
        self.fail()



class TestDaemonClasses_gitbackend_attribute(Tests_withDaemon_instances):
    """ The git backend attribue is a co-instance which manages the 
    the command connection to the git subsystem.
    The aim of having our own subsystem is to remove the need to the 
    local and remote managment subsystem to need to marshall data (such 
    as a commit message) from the daemon to the git library themselves"""
    actual_git_backend_daemon_attribute = 'g'
    def setUp(self,):
        super().setUp()
        self.gitmock = unittest.mock.MagicMock()
        setattr(self.out,self.actual_git_backend_daemon_attribute,self.gitmock)

    def tearDown(self,):
        super().tearDown()

    def test_add_pass_call_to_add(self,):
        filenm = unittest.mock.sentinel.FILENAME
        self.out.path = unittest.mock.sentinel.BASEPATH
        with unittest.mock.patch('os.path.relpath', return_value = filenm ) as opr:
            self.out.gitbackend.add(filenm)

        opr.assert_called_once_with(unittest.mock.sentinel.FILENAME,start =unittest.mock.sentinel.BASEPATH)
        self.gitmock.add.assert_called_once_with(filenm)

    def test_remove_pass_call_to_rm_with_ignore_unmatched(self,):
        filenm = unittest.mock.sentinel.FILENAME
        self.out.path = unittest.mock.sentinel.BASEPATH
        with unittest.mock.patch('os.path.relpath', return_value = filenm ) as opr:
            self.out.gitbackend.remove(filenm)
        opr.assert_called_once_with(unittest.mock.sentinel.FILENAME,start =unittest.mock.sentinel.BASEPATH)
        self.gitmock.rm.assert_called_once_with('--ignore-unmatch',filenm)

    def test_commit_pass_call_to_commit_add_adds_messages(self,):
        self.out.message = unittest.mock.sentinel.MESSAGE
        self.out.gitbackend.commit()
        self.gitmock.commit.assert_called_once_with('-m',unittest.mock.sentinel.MESSAGE)

    def test_commit_follows_with_a_push_if_remote_not_none(self,):
        self.out.rembranch = unittest.mock.sentinel.BRANCH
        self.out.remote = unittest.mock.sentinel.REMOTE
        with unittest.mock.patch.object(self.out, '_uniquename' ,return_value= "mybranch") as un:
            self.out.gitbackend.commit()

        self.gitmock.push.assert_called_once_with(unittest.mock.sentinel.REMOTE,"HEAD:mybranch")

    def test_fetch_forwards_to_realbackend_withdaemon_remote_etc(self,):
        self.out.rembranch = "REMOTEBRANCH"
        self.out.remote = unittest.mock.sentinel.REMOTE
        self.out.gitbackend.fetch()

        self.gitmock.fetch.assert_called_once_with(unittest.mock.sentinel.REMOTE,"REMOTEBRANCH:gitdrop_remote/REMOTEBRANCH")


    def test_commit_follows_with_a_push(self,):
        self.out.rembranch = unittest.mock.sentinel.BRANCH
        self.out.remote = None
        with unittest.mock.patch.object(self.out, '_uniquename' ,return_value= "mybranch") as un:
            self.out.gitbackend.commit()

        self.assertEqual(self.gitmock.push.call_count,0)

       
