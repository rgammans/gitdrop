## Modules for test
import unittest
import aiounittest
import unittest.mock
import asyncio

# Real Dependencies need for mock introspection
import git.cmd

# Modules to be tested
import gitdrop.remote as mut

def get_mock_daemon(loopcount=0):
        class MockDaemon:
            def __init__(self,):
                class Watch:
                    def event_gen(self,):
                        yield (1,"","","")

                self.iwatch = Watch()
                self.gitbackend = unittest.mock.MagicMock()
                self.count = 0
            @property
            def is_running(self,):
                self.count += 1
                return self.count <= loopcount

        return MockDaemon()

class RemoteWatcherLoop(unittest.TestCase):

    def setUp(self,):
        self.loop =None
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


    def test_remote_watcher_loop_calls_git_fetch_periodically(self,):
        daemon = get_mock_daemon(loopcount = 4)
        async def nowaiting(*args):pass
        with unittest.mock.patch('asyncio.sleep', new = nowaiting) as sleep:
            asyncio.run(mut.remote_watcher(daemon))
        self.assertEqual(daemon.gitbackend.fetch.call_count,4)

    def test_remote_watcher_loop_calls_fetch_only_after_a_delay(self,):
        daemon = get_mock_daemon(loopcount = 4)
        sleep_call_count = 0
        async def nowaiting(*args):
            nonlocal sleep_call_count
            self.assertEqual(args[0],mut.FETCH_PERIOD)
            sleep_call_count += 1

        with unittest.mock.patch('asyncio.sleep', new = nowaiting) as sleep:
            asyncio.run(mut.remote_watcher(daemon))
        self.assertEqual(sleep_call_count,4)

