import os
import git
import username
import inotify.adapters
import asyncio

class Daemon:
    def __init__(self, path, remote = None , branch = None , **kwargs ):
        self.remote = remote
        self.rembranch = branch
        if not os.path.exists(os.path.join(path, '.git')):
            raise RuntimeError(path +" doesn not exist")

        self.g = git.cmd.Git(path)
        status = (self.g.status().split("\n"))[0]
        if "detached" in  status:
            self.g.checkout(['-b', 'gitdrop_'+ self._uniquename() ])

        if self.remote:
            self.g.pull([self.remote,self.rembranch])

        self.iwatch = inotify.adapters.InotifyTree(path)
        self.finished= None

    @staticmethod
    def _uniquename(self,):
        pid = os.getpid()
        user = username()
        return f'%(user)s__%(pid)s'

    def run(self,):
        asyncio.run(self.async_main())
        self.iwatch = None
        print ("started")

    def stop(self,):
        if self.finished:
            self.finished.set_result(True)

        print ("stop")


    async def local_watch(self,):pass
    async def remote_watch(self,):pass

    async def async_main(self,):
        self.finished = asyncio.Future()
        remote_watcher = asyncio.create_task(self.remote_watch())
        local_watcher = asyncio.create_task(self.local_watch())
        await self.finished
        

pass
