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
    while True:
        r_conn = None
        try:
            print(os.getpid(), "before connect")
            r_conn = await aioredis.create_connection('redis://redis/0')
            print(os.getpid(), "before pubsub")
            p_recv = aioredis.pubsub.Receiver()
            print(os.getpid(), "before subscribe")
            await r_conn.subscribe(p_recv.channel("mth-live"))
            print(os.getpid(), "before listen")
            async for channel, message in p_recv.listen():
                print("Message", os.getpid(), message)
                if message["type"] == "message":
                    await app.ctx.fanout.trigger(message["data"].decode())
        except:
            import traceback
            bt = traceback.format_exc()
            prf = str(os.getpid()) + ": "
            print(prf + ("\n"+prf).join(bt.splitlines()))
            await asyncio.sleep(1)
        finally:
            if r_conn:
                r_conn.close()
