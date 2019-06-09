import os
import git
import username
import inotify.adapters
import asyncio

from . import inotify as gdi
from . import remote as gdr

class GitBackend:
    def __init__(self,daemon):
        self.d = daemon
    def add(self, *args):
        print ("git-add",args)
        args = ( os.path.relpath(x, start = self.d.path) for x in args )
        return self.d.g.add(*args)
    def remove(self, *args):
        args = ( os.path.relpath(x, start = self.d.path) for x in args )
        print ("git-rm",args)
        return self.d.g.rm('--ignore-unmatch',*args)
    def commit(self,):
        retv = self.d.g.commit('-m',self.d.message)
        # We push to our own remote branch if possible; and 
        # merge to the remote branch on merge actions.
        if self.d.remote is not None:
            self.d.g.push(self.d.remote, "HEAD:" + self.d._uniquename() )

        return retv

    def fetch(self,):
        return self.d.g.fetch(self.d.remote,self.d.rembranch+":gitdrop_remote/"+self.d.rembranch)


class Daemon:
    def __init__(self, path, remote = None , branch = None , **kwargs ):
        self.path = path
        self.remote = remote
        self.rembranch = branch
        if not os.path.exists(os.path.join(path, '.git')):
            raise RuntimeError(path +" does not exist as git repo")

        self.g = git.cmd.Git(path)
        self.gitbackend = GitBackend(self)
        self.message = 'Autocommit'
        status = (self.g.status().split("\n"))[0]
        if "detached" in  status:
            self.g.checkout(['-b', 'gitdrop_'+ self._uniquename() ])

        if self.remote:
            self.g.pull([self.remote,self.rembranch])

        self.iwatch = inotify.adapters.InotifyTree(path)
        self.finished= None


    @staticmethod
    def _uniquename():
        pid = os.getpid()
        user = username()
        return f'{user}__{pid}'

    def run(self,):
        try:
            asyncio.run(self.async_main())
        except KeyboardInterrupt:
            self.stop()

        self.iwatch = None
 


    @property
    def is_running(self,):
        return not (self.finished and self.finished.done())

    def stop(self,):
        if self.finished:
            self.finished.set_result(True)


    async def local_watch(self,):
        self.run_inotify(asyncio.get_event_loop())

    async def remote_watch(self,):
        await gdr.remote_watcher(self,)

    def run_inotify(self,loop):
        loop.create_task(gdi.action_loop(self))

    async def async_main(self,):
        self.finished = asyncio.Future()
        remote_watcher = asyncio.create_task(self.remote_watch())
        local_watcher = asyncio.create_task(self.local_watch())
        await self.finished


pass
