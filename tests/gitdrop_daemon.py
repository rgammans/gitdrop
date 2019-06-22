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
            d = mut.Daemon(self.tdir)
            status = g.status()
            self.assertFalse("detached" in status)
            un.assert_called_once()
            self.assertEqual(d.localbranch, "gitdrop_" + un.return_value)

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


    def test_daemon_sets_the_localbranch_variale_to_the_current_branch_of_master(self,):
        ## Create detached HEAD State.
        g = git.cmd.Git(self.tdir)
        g.init()
        with open(os.path.join(self.tdir,"a"),"w"):
            # Create empty file
            pass
        g.add(["a"])
        g.commit(["-m","Add a"])
        d = mut.Daemon(self.tdir)
        self.assertEqual(d.localbranch, "master")

    def test_daemon_sets_the_localbranch_variale_to_the_current_branch_even_if_not_master(self,):
        newbranchname= "Gobbledigook"
        ## Create detached HEAD State.
        g = git.cmd.Git(self.tdir)
        g.init()
        with open(os.path.join(self.tdir,"a"),"w"):
            # Create empty file
            pass
        g.add(["a"])
        g.commit(["-m","Add a"])
        g.checkout(["-b", newbranchname])
        d = mut.Daemon(self.tdir)
        self.assertEqual(d.localbranch, newbranchname)

    @unittest.skip('nyi')
    def test_triggers_a_fetch_from_remote_after_30secs_if_no_acrtions(self,):
        self.fail()


    @unittest.skip('nyi')
    def test_triggers_id_a_remote_fecths_is_nonempty_calls_merge_remote(self,):
        self.fail()


class Tests_withDaemon_instances(unittest.TestCase):
    """Base classes for other test suites"""
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
    actual_git_backend_daemon_attribute = 'gcmd'
    actual_git_repo_daemon_attribute = 'grepo'
    def setUp(self,):
        super().setUp()
        self.gitmock = unittest.mock.MagicMock()
        self.repomock = unittest.mock.MagicMock()
        setattr(self.out,self.actual_git_backend_daemon_attribute,self.gitmock)
        setattr(self.out,self.actual_git_repo_daemon_attribute,self.repomock)
        self.remotebranch_name = "REMOTEBRANCH"
        self.remote_trackingbranch_name = "gitdrop_remote/REMOTEBRANCH"

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
        self.out.rembranch = self.remotebranch_name
        self.out.remote = unittest.mock.sentinel.REMOTE
        with unittest.mock.patch.object(self.out, '_uniquename' ,return_value= "mybranch") as un:
            self.out.gitbackend.commit()

        self.gitmock.push.assert_called_once_with(unittest.mock.sentinel.REMOTE,"HEAD:mybranch")

    def test_fetch_forwards_to_realbackend_withdaemon_remote_etc(self,):
        rembranch = self.remotebranch_name
        tracking = self.remote_trackingbranch_name
        remote = unittest.mock.sentinel.REMOTE
        self.out.gitbackend._fetch(remote,rembranch,tracking)

        self.gitmock.fetch.assert_called_once_with(remote,rembranch+":"+tracking)

    def test_fetch_returns_false_if_remote_tracking_branch_doesnt_move(self,):
        rembranch = self.remotebranch_name
        tracking = self.remote_trackingbranch_name
        remote = unittest.mock.sentinel.REMOTE
        rv = self.out.gitbackend._fetch(remote,rembranch,tracking)
        self.gitmock.fetch.assert_called_once_with(unittest.mock.sentinel.REMOTE,self.remotebranch_name+":"+self.remote_trackingbranch_name)
        self.repomock.commit.assert_has_calls([unittest.mock.call(self.remote_trackingbranch_name) ] * 2)
        self.assertFalse(rv)

    def test_fetch_returns_true_if_remote_tracking_branch_does_move(self,):
        rembranch = self.remotebranch_name
        tracking = self.remote_trackingbranch_name
        remote = unittest.mock.sentinel.REMOTE
        self.repomock.commit.side_effect = [ unittest.mock.sentinel.COMMIT1 , unittest.mock.sentinel.COMMIT2 ]
        rv = self.out.gitbackend._fetch(remote,rembranch,tracking)

        self.gitmock.fetch.assert_called_once_with(unittest.mock.sentinel.REMOTE,self.remotebranch_name+":"+self.remote_trackingbranch_name)
        self.repomock.commit.assert_has_calls([unittest.mock.call(self.remote_trackingbranch_name) ] * 2)
        self.assertTrue(rv)


    def test_commit_follows_with_a_push(self,):
        self.out.rembranch = self.remotebranch_name
        self.out.remote = None
        with unittest.mock.patch.object(self.out, '_uniquename' ,return_value= "mybranch") as un:
            self.out.gitbackend.commit()

        self.assertEqual(self.gitmock.push.call_count,0)

    def test_fast_forward_merge_attempts_a_fast_forward_merge(self,):
        rv = self.out.gitbackend._fast_forward_merge(self.remote_trackingbranch_name)
        self.gitmock.merge.assert_called_once_with('--ff-only',self.remote_trackingbranch_name)

    def test_fast_forward_merge_returns_true_if_successful(self,):
        self.gitmock.merge.return_value = ""
        rv = self.out.gitbackend._fast_forward_merge(self.remote_trackingbranch_name)
        self.assertTrue(rv)

    def test_fast_forward_merge_returns_true_if_unsuccessful(self,):
        self.gitmock.merge.side_effect=git.cmd.GitCommandError(command="merge",status=1)
        rv = self.out.gitbackend._fast_forward_merge(self.remote_trackingbranch_name)
        self.assertFalse(rv)

    def test_clone_to_creates_new_clone_of_the_main_repo_in_the_passed_directory(self,):
        destination = unittest.mock.sentinel.DESTDIR
        rv = self.out.gitbackend.clone_to(destination)
        self.gitmock.clone.assert_called_once_with('.',destination)

    def test_merge_origin_on_merges_the_normal_branchnames_origin_tracking(self,):
        destination = unittest.mock.sentinel.DESTDIR
        self.out.rembranch = self.remotebranch_name
        with unittest.mock.patch('git.cmd.Git') as gc:
            rv = self.out.gitbackend.merge_origin_on(destination)
        gc.assert_called_once_with(destination)
        gc.return_value.merge.assert_called_once_with("remotes/origin/"+self.out.localbranch, "remotes/origin/"+self.remote_trackingbranch_name)



    def test_ff_merge_calls_under_ff_merge(self,):
        with unittest.mock.patch.object(self.out.__class__,'tracking_branch', new = unittest.mock.sentinel.TRACKING_BRANCH ) as x,\
             unittest.mock.patch.object(self.out.gitbackend,'_fast_forward_merge') as gm:
            rv = self.out.gitbackend.fast_forward_merge()

        gm.assert_called_once_with( unittest.mock.sentinel.TRACKING_BRANCH
        )


    def test_fetch_calls_under_fetch(self,):
        self.out.remote = unittest.mock.sentinel.REMOTE
        self.out.rembranch = unittest.mock.sentinel.REMOTE_BRANCH

        with unittest.mock.patch.object(self.out.__class__,'tracking_branch', new = unittest.mock.sentinel.TRACKING_BRANCH ) as x,\
             unittest.mock.patch.object(self.out.gitbackend,'_fetch', return_value = unittest.mock.sentinel.TESTVALUE) as gf:
            rv = self.out.gitbackend.fetch()

        gf.assert_called_once_with(
                unittest.mock.sentinel.REMOTE,
                unittest.mock.sentinel.REMOTE_BRANCH,
                unittest.mock.sentinel.TRACKING_BRANCH
        )
        self.assertEqual(rv, unittest.mock.sentinel.TESTVALUE)


    def test_try_merge_update_attempts_to_ff_merge_from_the_named_repo_and_returns_ff_merges_returnvalue(self,):
        destination = unittest.mock.sentinel.DESTDIR
        self.out.rembranch = self.remotebranch_name
        with unittest.mock.patch.object(self.out.gitbackend,'_fetch') as gf,\
             unittest.mock.patch.object( self.out.gitbackend,'get_new_branchname' , return_value = unittest.mock.sentinel.TMPBRANCH) as ggnb,\
             unittest.mock.patch.object(self.out.gitbackend,'_fast_forward_merge', return_value = unittest.mock.sentinel.TESTVALUE) as gm:
            rv = self.out.gitbackend.try_merge_update(destination)

        gf.assert_called_once_with(destination, self.remote_trackingbranch_name ,unittest.mock.sentinel.TMPBRANCH)
        gm.assert_called_once_with( unittest.mock.sentinel.TMPBRANCH)
        self.assertEqual(rv, unittest.mock.sentinel.TESTVALUE)

    def test_try_merge_update_attempts__returns_true_if_merge_succedds(self,):
        destination = unittest.mock.sentinel.DESTDIR
        self.out.rembranch = self.remotebranch_name
        self.gitmock.merge.return_value = ""
        with unittest.mock.patch.object(self.out.gitbackend,'_fetch') as gf,\
             unittest.mock.patch.object( self.out.gitbackend,'get_new_branchname' , return_value = unittest.mock.sentinel.TMPBRANCH) as ggnb:
            rv = self.out.gitbackend.try_merge_update(destination)

        gf.assert_called_once_with(destination, self.remote_trackingbranch_name ,unittest.mock.sentinel.TMPBRANCH)
        self.assertEqual(rv, True)


    def test_try_merge_update_attempts__returns_false_if_merge_fails(self,):
        destination = unittest.mock.sentinel.DESTDIR
        self.out.rembranch = self.remotebranch_name
        self.gitmock.merge.side_effect=git.cmd.GitCommandError(command="merge",status=1)
        with unittest.mock.patch.object(self.out.gitbackend,'_fetch') as gf,\
             unittest.mock.patch.object( self.out.gitbackend,'get_new_branchname' , return_value = unittest.mock.sentinel.TMPBRANCH) as ggnb:
            rv = self.out.gitbackend.try_merge_update(destination)

        gf.assert_called_once_with(destination, self.remote_trackingbranch_name ,unittest.mock.sentinel.TMPBRANCH)
        self.assertEqual(rv, False)




    def test_get_newbranchname_returns_a_nonzero_length_string(self,):
        x = self.out.gitbackend.get_new_branchname()
        self.assertEqual(type(x),str)
        self.assertGreater(len(x),0)

    def test_get_newbranchname_returns_a_name_which_isnt_a_standard_branch(self,):
        x = self.out.gitbackend.get_new_branchname()
        self.assertNotEqual(x,"master")
        self.assertNotEqual(x,"HEAD")
        self.assertNotEqual(x,self.out.rembranch)
        self.assertNotEqual(x,self.out.tracking_branch)

    def test_get_newbranchname_returns_something_different_each_call(self,):
        x = self.out.gitbackend.get_new_branchname()
        y = self.out.gitbackend.get_new_branchname()
        self.assertNotEqual(x,y)


