import os
from enum import Enum
from dataclasses import dataclass
import asyncio
import functools
import threading
import logging

logger = logging.getLogger(__name__)


QUIET_GUARD_DELAY=200 #milliseconds


async def action_loop( daemon ):
    """Main asynchrounous filewatcher loop"""
    thread = WatchThread( asyncio.get_event_loop(), daemon.iwatch )
    if not quiet:
        changes = rotate_changes()
        if len(changes) != 0:
            raise RuntimeError("Changes without async timer")
    thread.start()
    while daemon.is_running:
        logger.debug ("Localloop: waiting")
        await quiet
        ## It's possible that the quiet delay (and future)
        #  was extended while we were waiting on a specific
        #  instance; if so we go back and re-wait.
        if not quiet.done():
            logger.debug ("localloop: got temp unlock -relocking")
            continue

        logger.debug ("localloop: starting apply phase")
        try:
            changes = rotate_changes()
            changes.apply(daemon.gitbackend)
        except BaseException as error:
            logger.warning("igonring exception applying changes",exc_info=1)

class WatchThread(threading.Thread):
    """This class handles the blocking natures of inotify
    and decodes it to queuing event"""
    def __init__(self, *args, **kwargs):
#        import traceback
#        traceback.print_stack(limit=2)
        self.loop = args[0]
        self.notifier = args[1]
        args = args[2:]
        super().__init__(*args, **kwargs)

    def run(self,):
        for event in self.notifier.event_gen():
            if event is not None:
                # This is really noisy so log at half the usual 
                # debug level!
                logger.log(5,"notified: %s",event)
                self.process_event(event)

    def process_event(self, event, *args, **kwargs):
       self.loop.call_soon_threadsafe(functools.partial(enqueue_change, *event ))



class ChangeType(Enum):
    REMOVE_FILE = 0
    ADD_FILE = 1


@dataclass
class Change:
    """A single Change in the filesystem"""
    change_type: ChangeType
    path: str

class ChangeSet:
    """Manages a set of chnages to be commited

    This is almost, but not quite a singleton as 
    as mulitple commit's might be in-flight, but we try
    hard to prevent that.
    """
    def __init__(self,):
        self.q = [ ]
        self.applied = False
        self.anyadded = asyncio.Future()


    def add(self,change):
        """Adds a Change object to the list.
        This fucntion edits the list so that the appl list is the minimum
        set to record the final state.

        :param change Change: The change to add to the ChangeSet.
        """
        if self.applied:
            raise RuntimeError("Applied changeset should be considered immutable")

        logger.debug("change: %r",change)
        if change is None:
            return
        new_q = []
        ## Filter mulitple actions on a single path
        for prev in self.q:
            if (
                change.change_type == prev.change_type and
                change.path == prev.path
                ):
                #Nothing todo; this isn't a singificant change
                return
            elif change.path != prev.path:
                new_q.append(prev)
            #else:
            # if new_q is same path; but different action
            # it gets filtered out.

        self.q = new_q
        self.q.append(change)
        self.anyadded.set_result(None)

    def apply(self, gitbackend):
        """Sends the recorded set of changes to the Git Backend"""
        self.applied = True
        for change in self.q:
            logger.debug("applying %r",change)
            try:
                if change.change_type == ChangeType.ADD_FILE:
                    gitbackend.add(change.path)
                elif change.change_type == ChangeType.REMOVE_FILE:
                    gitbackend.remove(change.path)
            except Exception as error:
                logger.warning("ignoring exception applying change %r"%(change,),exc_info=1)

        gitbackend.commit()

    def __contains__(self,item):
        return item in self.q


    def __len__(self,):
        return len(self.q)


## Filewatcher / inotify singleton data elements and mutators.

quiet = None #'asyncio.Future()
changes = ChangeSet()

def rotate_changes():
    global quiet
    global changes
    rv , changes = changes, ChangeSet()
    quiet = changes.anyadded
    return rv


def event2change(dummy, evtypes, path,filename ):
    """Converts an inotify event to an Change to be recored in a ChangeSet"""
    fullpath = os.path.join(path,filename)
    evtypes = set(evtypes)
#    logger.debug ("Events %r",evtypes)
    if evtypes.intersection(["IN_CLOSE_WRITE","IN_CREATE","IN_MOVED_TO"]):
        typ = ChangeType.ADD_FILE
    elif evtypes.intersection(["IN_DELETE","IN_MOVED_FROM"]):
        typ = ChangeType.REMOVE_FILE
    else:
        return
    return Change(typ,fullpath)

def enqueue_change(*args):
    """Ands a event to a changeset and reset the monostable delay"""
    change =  event2change(*args)
    if change and not (( os.path.sep+'.git'+os.path.sep ) in change.path):
        changes.add(change)
        extend_quiet_delay()

def extend_quiet_delay():
    """Resets the quiet monostable"""
    global quiet
    delay = asyncio.sleep(QUIET_GUARD_DELAY / 1000 )
    quiet = asyncio.gather(quiet,delay)
