#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Integration checks against a running disposable binder with --test-controls."""
import argparse
import asyncio
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from afb_ws import Client, AfbError

async def eventually(c, predicate, timeout=4):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = await c.call('sameloop-api','get')
        if predicate(state):
            return state
        await asyncio.sleep(.05)
    raise AssertionError(f'condition not reached: {state}')

async def rejects(c, api, verb, arg):
    try:
        await c.call(api,verb,arg)
    except AfbError:
        return
    raise AssertionError(f'Unexpectedly accepted {api}/{verb}: {arg}')

async def main(url):
    count = 0
    def passed(name):
        nonlocal count
        count += 1
        print(f'ok {count} - {name}', flush=True)
    async with Client(url) as c:
        try:
            await c.call('sameloop-api','fault',{'valid':True,'paused':False,'temperature':32.4,'heat':.18})
            await c.call('sameloop-api','settings',{'mode':'OFF','setpoint':25})
            await eventually(c,lambda s:s['temperature']['available'] and s['fan']['requested']==0)
            passed('OFF baseline and available sensor')
            for api,verb,arg in [('sameloop-fan','apply',{'duty':100}),
                                 ('sameloop-sensor','fault',{'valid':False}),
                                 ('sameloop-controller','settings',{'mode':'AUTO'})]:
                await rejects(c,api,verb,arg)
            passed('internal APIs hidden from the network')
            for arg in ({}, {'mode':'MANUAL'}, {'setpoint':41}, {'setpoint':'25'},
                        {'setpoint':True}, {'mode':'AUTO','setpoint':0}, {'extra':1},
                        {'mode':None}, [], {'mode':'AUTO','unknown':0}):
                await rejects(c,'sameloop-api','settings',arg)
                s=await c.call('sameloop-api','get')
                assert s['controller']=={'mode':'OFF','setpoint':25}
            passed('invalid settings rejected atomically')
            await c.call('sameloop-api','settings',{'mode':'AUTO','setpoint':25})
            s=await eventually(c,lambda s:s['fan']['requested']>0 and s['fan']['applied']>0 and s['fan']['rpm']>0)
            assert s['fan']['applied']<s['fan']['requested']
            passed('AUTO command, separate feedback and fan inertia')
            await c.call('sameloop-api','fault',{'valid':False})
            await eventually(c,lambda s:s['alarms']['sensor_unavailable'] and s['fan']['requested']==0)
            passed('invalid sensor suspends regulation')
            await c.call('sameloop-api','fault',{'valid':True,'temperature':32.4})
            await eventually(c,lambda s:s['temperature']['available'] and s['fan']['requested']>0)
            passed('fresh valid sensor resumes AUTO')
            await c.call('sameloop-api','fault',{'paused':True})
            await asyncio.sleep(.2)
            before=await c.call('sameloop-api','get')
            await eventually(c,lambda s:s['alarms']['sensor_unavailable'] and s['fan']['requested']==0)
            after=await c.call('sameloop-api','get')
            assert after['temperature']['sequence']==before['temperature']['sequence']
            passed('paused sample expires despite repeated successful reads')
            await c.call('sameloop-api','fault',{'paused':False,'temperature':55})
            await eventually(c,lambda s:s['alarms']['overtemperature'] and s['temperature']['available'])
            await c.call('sameloop-api','fault',{'valid':False})
            s=await eventually(c,lambda s:s['alarms']['sensor_unavailable'])
            assert s['alarms']['overtemperature'] and s['alarms']['overtemperature_quality']=='unavailable'
            passed('overtemperature retained with unavailable quality on sensor loss')
            await c.call('sameloop-api','fault',{'valid':True,'temperature':32.4})
            await eventually(c,lambda s:s['temperature']['available'])
            async with Client(url) as other:
                await c.call('sameloop-api','subscribe')
                await other.call('sameloop-api','subscribe')
                event=await asyncio.wait_for(c.events.get(),2)
                assert event[1]=='sameloop-controller/state'
                await asyncio.wait_for(other.events.get(),2)
                await c.call('sameloop-api','unsubscribe')
                await asyncio.sleep(.2)
                while not c.events.empty(): c.events.get_nowait()
                try:
                    await asyncio.wait_for(c.events.get(),.35)
                    raise AssertionError('events after unsubscribe')
                except TimeoutError:
                    pass
                await asyncio.wait_for(other.events.get(),2)
            passed('independent subscriptions and unsubscribe isolation')
            async with Client(url) as reconnected:
                snapshot=await reconnected.call('sameloop-api','subscribe')
                assert snapshot['schema']=='sameloop/1'
                await asyncio.wait_for(reconnected.events.get(),2)
            passed('fresh connection can resubscribe and obtain snapshot')
            await rejects(c,'sameloop-api','fault',{'valid':False,'heat':3})
            await eventually(c,lambda s:s['temperature']['available'])
            passed('invalid fault request does not partially invalidate sensor')
        finally:
            await c.call('sameloop-api','settings',{'mode':'OFF','setpoint':25})
            await c.call('sameloop-api','fault',{'valid':True,'paused':False,'heat':.18})
    print(f'1..{count}')

p=argparse.ArgumentParser()
p.add_argument('--url',default='ws://127.0.0.1:1234/api')
asyncio.run(main(p.parse_args().url))
