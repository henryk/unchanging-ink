import asyncio
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
    r_conn = aioredis.from_url("redis://redis/0")
    p_conn = r_conn.pubsub()
    await p_conn.subscribe("mth-live")
    async for message in p_conn.listen():
        if message["type"] != "message":
            continue
        await app.ctx.fanout.trigger(message["data"].decode())
