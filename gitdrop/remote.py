import asyncio
import logging

from . import merge

logger = logging.getLogger(__name__)


FETCH_PERIOD = 10 #seconds

async def remote_watcher(daemon):
    while daemon.is_running:
        await asyncio.sleep(FETCH_PERIOD)
        logger.debug('remoteloop: fetching')
        try:
            if daemon.gitbackend.fetch():
                merge.do_merge(daemon)
            logger.debug('remoteloop: fetched')
        except Exception as err:
            logger.warning("Git fetch failed:", exc_info=1)
