import unittest
import unittest.mock

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

