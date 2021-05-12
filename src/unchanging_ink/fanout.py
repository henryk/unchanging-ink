import asyncio
import os

import aioredis
from asyncio import wait_for
from typing import Any, Optional


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
            c = self._cond
            self._cond = asyncio.Condition()
            self._data = data
            c.notify_all()


async def redis_fanout(app):
    await asyncio.sleep(1)  # I don't know why I need this
    while True:
        redis = None
        try:
            redis = await aioredis.create_redis('redis://redis/0')
            channel, = await redis.subscribe("mth-live")
            while await channel.wait_message():
                message = await channel.get()
                await app.ctx.fanout.trigger(message.decode())
        except GeneratorExit:
            raise
        except:
            import traceback
            bt = traceback.format_exc()
            prf = str(os.getpid()) + ": "
            print(prf + ("\n"+prf).join(bt.splitlines()))
            await asyncio.sleep(1)
        finally:
            if redis:
                redis.close()
