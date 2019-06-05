## Modules for test
import unittest
import unittest.mock
import tempfile
import os
import threading
import contextlib
import sys

# Real Dependencies need for mock introspection
import asyncio
import inotify.adapters
import aiounittest

# Modules to be tested
import gitdrop.inotify as mut

class TestIntofyThreadClass_class_methods(unittest.TestCase):
    
    def test_watch_thread_is_contructed_with_a_loop_argument(self,):
        ## This needs to be syncronised with the damon test:
        #
        # TestDaemon_instance_methods.test_localwatch_launches_a_thread_to_listen_for_inotify_changes
        x = mut.WatchThread(unittest.mock.sentinel.LOOP, unittest.mock.sentinel.NOTIFIER)
        self.assertEqual(x.loop,unittest.mock.sentinel.LOOP)
        self.assertEqual(x.notifier,unittest.mock.sentinel.NOTIFIER)

class TestIntofyThreadClass_class_methods(unittest.TestCase):

    def setUp(self,):
        self.loop = unittest.mock.MagicMock()
        self.notify = unittest.mock.MagicMock()
        self.out = mut.WatchThread(self.loop, self.notify)
        #mut.rotate_changes()

    def tearDown(self,):
        pass

    def test_run_method_waits_on_event_generator_and_calls_process_event_with_the_output(self,):
        max_value = 10
        def looper():
            """ A finite deterministic generator used to generate a test sequence
            We should be able to subistite this for pretty much any generator.
            """
            for i in range(max_value):
                yield i

        self.notify.event_gen.return_value = iter(looper())
        with unittest.mock.patch.object(self.out,'process_event') as pe:
            self.out.run()
        self.notify.event_gen.assert_any_call()
        pe.assert_has_calls([ unittest.mock.call(x) for x in looper()])

    #def test_thread_stopswhen_needed(self,):pass
    #def test_thread_forks_correctlt(self,):pass

    def test_process_event_queues_enqueues_add_event(self,):
        mockpartial = unittest.mock.sentinel.ENQ_CHANGE
        change_data = ( unittest.mock.sentinel.CHANGEDATA,)

        with unittest.mock.patch('functools.partial',return_value = mockpartial) as fp:
            self.out.process_event( change_data)

        fp.assert_called_once_with(mut.enqueue_change, *change_data)
        self.loop.call_soon_threadsafe.assert_called_once_with( mockpartial )



class TestChangeset_instance_methods(unittest.TestCase):
    
    def setUp(self,):
        self.out = mut.ChangeSet()
        self.out.add( mut.Change(mut.ChangeType.ADD_FILE,"add"))
        self.out.add( mut.Change(mut.ChangeType.REMOVE_FILE,"remove"))

    def test_changset_contains_is_true_for_items_in_the_set(self,):
        ## We test this two ways to be sure
        self.assertIn(mut.Change(mut.ChangeType.ADD_FILE,"add"),self.out)
        self.assertTrue(mut.Change(mut.ChangeType.ADD_FILE,"add") in self.out)
        self.assertIn(mut.Change(mut.ChangeType.REMOVE_FILE,"remove"),self.out)
        self.assertTrue(mut.Change(mut.ChangeType.REMOVE_FILE,"remove") in self.out)

    def test_changeset_len_lists_the_numbers_of_items_stored(self,):
        self.assertEqual(len(self.out),2)

    def test_adding_an_add__of_an_already_added_file_to_a_changeset_make_no_difference(self,):
        cur = len(self.out)
        self.out.add( mut.Change(mut.ChangeType.ADD_FILE,"add"))
        self.assertEqual(len(self.out),cur)

    def test_adding_a_remove__of_an_already_removed_file_to_a_changeset_make_no_difference(self,):
        cur = len(self.out)
        self.out.add( mut.Change(mut.ChangeType.REMOVE_FILE,"remove"))
        self.assertEqual(len(self.out),cur)

    def test_adding_a_add__of_an_already_removed_file_to_a_changet_removes_the_remove_but_leaves_anythingelse(self,):
        self.out.add( mut.Change(mut.ChangeType.ADD_FILE,"remove"))
        self.assertNotIn( mut.Change(mut.ChangeType.REMOVE_FILE,"remove"), self.out)
        self.assertIn( mut.Change(mut.ChangeType.ADD_FILE,"remove"), self.out)
        self.assertIn( mut.Change(mut.ChangeType.ADD_FILE,"add"), self.out)



    def test_adding_a_remove__of_an_already_added_file_to_a_changet_removes_the_remove_but_leaves_anythingelse(self,):
        self.out.add( mut.Change(mut.ChangeType.REMOVE_FILE,"add"))
        self.assertNotIn( mut.Change(mut.ChangeType.ADD_FILE,"add"), self.out)
        self.assertIn( mut.Change(mut.ChangeType.REMOVE_FILE,"add"), self.out)
        self.assertIn( mut.Change(mut.ChangeType.REMOVE_FILE,"remove"), self.out)


    def test_apply_makes_git_backend_calls_in_turn_then_commits(self,):
        gitbackend = unittest.mock.MagicMock()
        self.out.apply(gitbackend)
        gitbackend.add.assert_called_once_with('add')
        gitbackend.remove.assert_called_once_with('remove')
        gitbackend.commit.assert_called_once_with()  ##FIXME: Should have a comment here.

class TestInotify_module_level_functions(unittest.TestCase):

    def setUp(self,):
        self.loop =None
        self.tearDown()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        mut.quiet = None

    def tearDown(self,):
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:pass
        if loop:
            loop.close()
        if self.loop:
            self.loop.close()

    def test_event2change_converts_a_file_modification_event_to_a_file_add_change(self,):
        path,filename = "PATH","FILENAME"
        change = mut.event2change(
                                        unittest.mock.sentinel.DUMMY,
                                        [ 'IM_CLOSE_WRITE' ],
                                        path,filename
                                        )
        self.assertEqual(change.change_type,mut.ChangeType.ADD_FILE )
        self.assertEqual(change.path, os.path.join(path,filename ))

    def test_event2change_converts_a_file_add_event_to_a_file_add_change(self,):
        path,filename = "PATH","FILENAME"
        change = mut.event2change(
                                        unittest.mock.sentinel.DUMMY,
                                        [ 'IM_CREATE' ],
                                        path,filename
                                        )
        self.assertEqual(change.change_type,mut.ChangeType.ADD_FILE )
        self.assertEqual(change.path, os.path.join(path,filename ))

    def test_event2change_converts_a_file_delete_event_to_a_file_remove_change(self,):
        path,filename = "PATH","FILENAME"
        change = mut.event2change(
                                        unittest.mock.sentinel.DUMMY,
                                        [ 'IM_DELETE' ],
                                        path,filename
                                        )
        self.assertEqual(change.change_type,mut.ChangeType.REMOVE_FILE )
        self.assertEqual(change.path, os.path.join(path,filename ))



    def test_event2change_converts_a_movedfrom_event_to_a_file_remove_change(self,):
        path,filename = "PATH","FILENAME"
        change = mut.event2change(
                                        unittest.mock.sentinel.DUMMY,
                                        [ 'IM_MOVED_FROM' ],
                                        path,filename
                                        )
        self.assertEqual(change.change_type,mut.ChangeType.REMOVE_FILE )
        self.assertEqual(change.path, os.path.join(path,filename ))

    def test_event2change_converts_a_movedto_event_to_a_file_remove_change(self,):
        path,filename = "PATH","FILENAME"
        change = mut.event2change( 
                                        unittest.mock.sentinel.DUMMY,
                                        [ 'IM_MOVED_TO' ],
                                        path,filename
                                        )
        self.assertEqual(change.change_type,mut.ChangeType.ADD_FILE )
        self.assertEqual(change.path, os.path.join(path,filename ))



    def test_after_rotate_changes_there_is_future_which_to_indicate_when_a_queit_period_is_elapsed(self,):
        mut.rotate_changes()
        self.assertIsInstance(mut.quiet,asyncio.Future)


    def test_when_enqueue_change_call_extends_the_delay(self,):
        with unittest.mock.patch.object(mut, 'extend_quiet_delay' , return_value = unittest.mock.sentinel.QUIET) as ag, \
            unittest.mock.patch.object(mut.changes, 'add' , return_value = unittest.mock.sentinel.QUIET) as icsa,\
            unittest.mock.patch.object(mut, 'event2change' , return_value = unittest.mock.sentinel.CHANGE) as ice2c:
            mut.enqueue_change(1,2,3,4)


        ag.assert_called_once_with()


    def test_when_enqueue_change_call_enquenue_the_change_by_covnert_it_and_adding_it(self,):
        mut.rotate_changes()
        with unittest.mock.patch.object(mut, 'extend_quiet_delay' , return_value = unittest.mock.sentinel.QUIET) as ag, \
            unittest.mock.patch.object(mut.changes, 'add' , return_value = unittest.mock.sentinel.QUIET) as icsa,\
            unittest.mock.patch.object(mut, 'event2change' , return_value = unittest.mock.sentinel.CHANGE) as ice2c:
            mut.enqueue_change(1,2,3,4)

        ice2c.assert_called_once_with(1,2,3,4)
        icsa.assert_called_once_with(  unittest.mock.sentinel.CHANGE )


    def test_extends_quiet_delay_does_that(self,):
        """Extend quiet delay should replaxt the quiet future with oune which resolves
        no earlier than the current future and at least QUIET_GUARD_DELAY in the future"""
        q = mut.quiet
        with unittest.mock.patch('asyncio.gather' , return_value = unittest.mock.sentinel.QUIET_NEW) as ag,\
             unittest.mock.patch('asyncio.sleep' , return_value = unittest.mock.sentinel.QUIET_SUB) as asl:

            mut.extend_quiet_delay()

        ## These calls are simplest correct implementation.
        #  which makes this a bit of to much of a white box test for me.
        asl.assert_called_once_with(mut.QUIET_GUARD_DELAY/1000)
        ag.assert_called_once_with(q,unittest.mock.sentinel.QUIET_SUB)
        self.assertEqual(mut.quiet, unittest.mock.sentinel.QUIET_NEW)


    #@unittest.skip("das")
    def test_inotify_mainloop_processes_changeset_when_the_future_resolves(self,):
        ## Test need to run in async context so here a function for it.all
        gb = unittest.mock.MagicMock()
        class MockDaemon:
            def __init__(self,):
                class Watch:
                    def event_gen(self,):
                        yield (1,"","","")

                self.iwatch = Watch()
                self.gitbackend = gb
                self._count = 0
            @property
            def is_running(self,):
                self._count += 1
                return not (self._count -1)

        async def test():
            loop = asyncio.get_event_loop()
            done = loop.create_task(mut.action_loop( MockDaemon()))
            mut.quiet.set_result(None)
            await done
            # Await quiet to silence warnings
            #await mut.quiet

        mychanges = unittest.mock.MagicMock()
        mut.rotate_changes()
        with unittest.mock.patch('gitdrop.inotify.rotate_changes', return_value= mychanges) as ica:
            #test_co = next(asyncio.as_completed( [ test() ] ,timeout=10 ))
            self.loop.run_until_complete(test())
            pass
        ica.assert_called_once()
        mychanges.apply.assert_called_once()

    @aiounittest.async_test
    async def test_rotate_changes_replaces_the_quiet_future_and_the_changes_object(self,):
        ## actuall pretty syncronous l but we need the event loop
        with \
            unittest.mock.patch('gitdrop.inotify.quiet', new = unittest.mock.sentinel.QUIET ),\
            unittest.mock.patch('gitdrop.inotify.changes', new = unittest.mock.sentinel.CHANGES ):

            #mut.quiet = unittest.mock.sentinel.QUIET
            #mut.changes = unittest.mock.sentinel.CHANGES
            rv  = mut.rotate_changes()
            self.assertEqual(rv, unittest.mock.sentinel.CHANGES)
            self.assertNotEqual(mut.changes, unittest.mock.sentinel.CHANGES)
            self.assertNotEqual(mut.quiet, unittest.mock.sentinel.QUIET)


    def test_extending_wait_delays_rotate_being_invoked(self,):
        """
        It's possible that the quiet delay (and future)
        was extended while we the action loop was await-ing on a specific
        instance; this test checks this case is handled correctly.

        This is a race hazard test ;  Which make it a bit complex.abs

        We have a counting MockDaemon which is 'running' for 4 calls
        around the mainloop. Also mock rotatehcnages; and return a
        mockobject awith an apply which counts it's calls.abs

        Finally we have another async loop; this one can only be running
        if the action_loo()is currently suspended; and it only has a
        single await statement; so it must me be there. Which is perfect;
        so we check is_running has run since rotate_changes ; by tracking
        the phase and swap out quiet; and resolve the old one.

        We do this until the last time rounf the is_running loop would happen 
        and that time we resolve the quiet and leave it unreplaced.abs

        After theis the action_loop show complet as the daeomn reports not running
        and we can chance apply() has once been called once.

        """ 
        phase =None
        LOOPS_UNTIL_COMPLETE = 4

        gb = unittest.mock.MagicMock()
        class MockDaemon:
            def __init__(self,):
                class Watch:
                    def event_gen(self,):
                        return []

                self.iwatch = Watch()
                self.gitbackend = gb
                self.count = 0

            @property
            def is_running(self,):
                nonlocal phase
                if mut.quiet is None:
                    mut.quiet = asyncio.Future( )
                    asyncio.create_task(hack_quiet())
                phase = "ABOUT_TO_AWAIT"
                self.count += 1
                return self.count  < LOOPS_UNTIL_COMPLETE


        daemon = MockDaemon()
        async def hack_quiet():
            nonlocal phase
            while daemon.count < (LOOPS_UNTIL_COMPLETE-1):
                if phase == "ABOUT_TO_AWAIT":
                    # Actually becuase we are here;
                    # the system must have awaitEed
                    oldq = mut.quiet
                    # replace quiet
                    mut.quiet = asyncio.Future()
                    # and relase the old one
                    oldq.set_result(None)

                await asyncio.sleep(0)

            #Finally allow the loop on it mwrry way
            mut.quiet.set_result(None)


        called = 0
        class MockChanges(list):
            def apply(self,dummy):
                nonlocal called
                called += 1

        def rotate_changes_replacement():
            nonlocal phase
            phase = "AWAITED"
            return MockChanges()

        with unittest.mock.patch('gitdrop.inotify.rotate_changes',new=rotate_changes_replacement):
            asyncio.run(mut.action_loop(daemon))

        self.assertEqual(called,1)
