# SPDX-License-Identifier: MIT
"""Small AFB WSJ1 client. No retries/replay of mutating calls."""
import asyncio
import json
import itertools
import websockets

class AfbError(Exception):
    pass

class Client:
    def __init__(self, url):
        self.url = url
        self.ids = itertools.count(1)
        self.pending = {}
        self.events = asyncio.Queue(maxsize=1000)

    async def __aenter__(self):
        self.ws = await websockets.connect(self.url, subprotocols=['x-afb-ws-json1'], open_timeout=5)
        self.reader = asyncio.create_task(self._read())
        return self

    async def __aexit__(self, *exc):
        await self.ws.close()
        self.reader.cancel()
        await asyncio.gather(self.reader, return_exceptions=True)

    async def _read(self):
        try:
            async for raw in self.ws:
                msg = json.loads(raw)
                if msg[0] in (3, 4):
                    future = self.pending.pop(str(msg[1]), None)
                    if future is not None and not future.done():
                        if msg[0] == 4:
                            future.set_exception(AfbError(str(msg[2])))
                        else:
                            future.set_result(msg[2].get('response', msg[2]))
                elif msg[0] == 5:
                    if self.events.full():
                        self.events.get_nowait()  # state snapshots: keep recent samples
                    self.events.put_nowait(msg)
        finally:
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(ConnectionError('AFB connection closed; command outcome may be unknown'))
            self.pending.clear()

    async def call(self, api, verb, args=None):
        ident = str(next(self.ids))
        future = asyncio.get_running_loop().create_future()
        self.pending[ident] = future
        try:
            await self.ws.send(json.dumps([2, ident, f'{api}/{verb}', {} if args is None else args], allow_nan=False))
            return await asyncio.wait_for(future, timeout=5)
        finally:
            self.pending.pop(ident, None)
