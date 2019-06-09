import os
import git
import username
import inotify.adapters
import asyncio
import logging

from . import inotify as gdi
from . import remote as gdr

logger = logging.getLogger(__name__)

class GitBackend:
    def __init__(self,daemon):
        self.d = daemon
    def add(self, *args):
        print ("git-add",args)
        args = ( os.path.relpath(x, start = self.d.path) for x in args )
        return self.d.gcmd.add(*args)
    def remove(self, *args):
        args = ( os.path.relpath(x, start = self.d.path) for x in args )
        print ("git-rm",args)
        return self.d.gcmd.rm('--ignore-unmatch',*args)
    def commit(self,):
        retv = self.d.gcmd.commit('-m',self.d.message)
        # We push to our own remote branch if possible; and 
        # merge to the remote branch on merge actions.
        if self.d.remote is not None:
            self.d.gcmd.push(self.d.remote, "HEAD:" + self.d._uniquename() )

        return retv

    def fetch(self,):
        """Returns true if the remote branch has moved"""
        old_commit = self.d.grepo.commit(self.d.tracking_branch)
        self.d.gcmd.fetch(self.d.remote,self.d.rembranch+":"+self.d.tracking_branch)
        new_commit = self.d.grepo.commit(self.d.tracking_branch)
        return  old_commit != new_commit

    def fast_forward_merge(self,):
        return self.d.gcmd.merge('--ff-only',self.d.tracking_branch)



class Daemon:
    def __init__(self, path, remote = None , branch = None , **kwargs ):
        self.path = path
        self.remote = remote
        self.rembranch = branch
        if not os.path.exists(os.path.join(path, '.git')):
            raise RuntimeError(path +" does not exist as git repo")

        self.gcmd  = git.cmd.Git(path)
        self.grepo = git.Repo(path)
        self.gitbackend = GitBackend(self)
        self.message = 'Autocommit'
        status = (self.gcmd.status().split("\n"))[0]
        if "detached" in  status:
            self.gcmd.checkout(['-b', 'gitdrop_'+ self._uniquename() ])

        if self.remote:
            self.gcmd.pull([self.remote,self.rembranch])

        self.iwatch = inotify.adapters.InotifyTree(path)
        self.finished= None
 
    @property
    def tracking_branch(self,):
        if self.rembranch:
            return "gitdrop_remote/"+self.rembranch
        return None


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
