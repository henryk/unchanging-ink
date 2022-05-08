import asyncio
import os
from asyncio import wait_for
from typing import Any, Optional

import aioredis


class Fanout:
    def __init__(self):
        self._data: Optional[Any] = None
        self._cond = asyncio.Condition()

    async def wait(self, timeout=None) -> Optional[Any]:
        async with self._cond:
            await wait_for(self._cond.wait(), timeout)
            return self._data

    async def trigger(self, data: Optional[Any] = None):
        async with self._cond:
            self._data = data
            self._cond.notify_all()


async def redis_fanout(app):
    await asyncio.sleep(1)  # I don't know why I need this
    while True:
        redis = None
        try:
            redis = await aioredis.from_url("redis://redis/0")
            pubsub = redis.pubsub()
            await pubsub.subscribe("mth-live")
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
                if message:
                    await app.ctx.fanout.trigger(message["data"].decode())
        except GeneratorExit:
            raise
        except:
            import traceback

            bt = traceback.format_exc()
            prf = str(os.getpid()) + ": "
            print(prf + ("\n" + prf).join(bt.splitlines()))
            await asyncio.sleep(1)
        finally:
            if redis:
                await redis.close()
