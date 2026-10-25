# Architecture

The public API forwards requests asynchronously to the private controller using
AFB request subcalls. `pass_events` preserves subscriptions for the originating
client. It does not set `api_session`, so clients do not share a subscription
session. Clients must reconnect, subscribe again and retrieve a fresh snapshot;
the supplied example reconnects without replaying commands.

Internal dependency/call graph is acyclic:

- API -> controller (settings, snapshots, subscriptions)
- API -> sensor (test controls only, opt-in)
- Controller -> sensor (read) and fan (apply)
- Sensor -> fan (read applied duty for thermal simulation)
- Fan -> no other API

The three implementation APIs are loaded with the binder `private:` prefix.
They remain callable by the public facade and other internal bindings, but are
not directly accessible over the public HTTP/WebSocket server. This is not an
isolation boundary between untrusted plugins within the same process.

Periodic work uses AFB scheduled jobs, not blocking sleeps or a polling thread.
A new job is posted 100 ms after each iteration; elapsed time is measured with
CLOCK_MONOTONIC. This gives a nominal rate near 10 Hz, not a fixed deadline.
Requests and jobs share state through mutexes; cross-API calls occur unlocked.
The service graph and synchronously available local providers are assumptions
of this version. Network provider timeouts require additional asynchronous work
before these bindings can be used across machines without blocking a worker.

All four modules run in one binder process. Sensor timestamps are comparable
because CLOCK_MONOTONIC belongs to the same host. For multiple hosts, add adapter
freshness tracking using sequence numbers and receipt timestamps instead of
comparing raw source clocks.

## Physics

Ambient 20 °C. Normal heat 0.18 °C/s; `heat: 1.2` is the disturbance scenario.
Thermal equation:

`dT/dt = heat - (0.015 + 0.12 × applied_duty / 100) × (T - 20)`.

The temperature update is an analytical solution over each interval using the
current sampled fan duty. Applied duty has a 0.6 s time constant; speed has a
0.8 s time constant toward 40 × applied duty RPM. The fan uses the exact coupled
solution for constant command intervals, splitting at watchdog expiration.
Fan state advances lazily on read/apply, evaluated at current monotonic time.
Paused publication freezes sensor sample value/sequence/timestamp while the
underlying thermal model keeps running. Invalidity is published immediately.

## Future changes

Extract the simulator behind a shared provider contract when implementing the
other stacks; add hardware providers, UI adapters, packaging and authorization.
Keep settings/control behavior identical across stacks. Add a separate simulator
clock and matched numerical integration before claiming bitwise/numerical
comparability with the existing UI-only demonstrations.

Shutdown cancels pending jobs; modules and events have process lifetime.
Live dlclose/hot replacement and independent service restart are not supported.
Restart the binder for recovery tests; accepted settings reset to OFF/25 °C.
