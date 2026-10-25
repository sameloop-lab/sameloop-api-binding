#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import argparse
import asyncio
import json
from afb_ws import Client

async def main(a):
    if a.verb != 'subscribe':
        async with Client(a.url) as c:
            print(json.dumps(await c.call('sameloop-api', a.verb, json.loads(a.json)), indent=2))
        return
    while True:
        try:
            async with Client(a.url) as c:
                print(json.dumps(await c.call('sameloop-api', 'subscribe')), flush=True)
                while True:
                    # Missing events also count as unavailable: reconnect and refresh.
                    event = await asyncio.wait_for(c.events.get(), timeout=2)
                    print(json.dumps(event), flush=True)
        except (OSError, ConnectionError, TimeoutError) as error:
            print(f'Disconnected/stale: {error}; reconnecting in 1 s', flush=True)
            await asyncio.sleep(1)

p = argparse.ArgumentParser()
p.add_argument('verb', choices=['get','settings','subscribe','unsubscribe','fault'])
p.add_argument('json', nargs='?', default='{}')
p.add_argument('--url', default='ws://127.0.0.1:1234/api')
try:
    asyncio.run(main(p.parse_args()))
except KeyboardInterrupt:
    pass
