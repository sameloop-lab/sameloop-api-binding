# SameLoop AFB bindings — 0.1.0

**Bind & Seek — Same Control Loop, Different Embedded Stacks**

Four independent C11/Meson projects implementing the SameLoop temperature/fan
control demo using AFB binding API v4. This source bundle can be split into the
four requested Git repositories without changing their build files.

| Project | AFB API | Role |
|---|---|---|
| sameloop-api-binding | sameloop-api | Public facade, commands, subscription forwarding |
| sameloop-sensor-binding | sameloop-sensor | Temperature and thermal simulator |
| sameloop-controller-binding | sameloop-controller | OFF/AUTO, setpoint, regulation and alarms |
| sameloop-fan-binding | sameloop-fan | Fan command, inertia, speed and command watchdog |

## Quick start

Prerequisites: GCC/Clang, Meson >=0.61, Ninja, pkg-config, `json-c` development
files >=0.13, `afb-binding` headers >=4.2, and an AFB v4 capable `afb-binder`.
Tested dependency revisions and actual validation results: [VALIDATION.md](docs/VALIDATION.md).

On a Fedora host, install the generic tools:

```sh
sudo dnf install gcc meson ninja-build pkgconf-pkg-config json-c-devel python3
```

Install `afb-binding-devel` and `afb-binder` from your configured redpesk
repositories/builds. Do not assume these two packages exist in stock Fedora.
Check that `pkg-config --modversion afb-binding json-c` succeeds.
If using a custom prefix, set `PKG_CONFIG_PATH` and the runtime library search
path accordingly.

```sh
./scripts/build-all.sh
./scripts/run-demo.py
```

No sudo or installation needed to launch the four built modules.
The launcher prints and writes a generated binder config under `run/`, loads
three modules privately, and listens only on `127.0.0.1:1234`.
Use `--port 1235` for another instance. Terminate with Ctrl+C.

## Use the public API

```sh
curl -s http://127.0.0.1:1234/api/sameloop-api/get
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"mode":"AUTO","setpoint":25}' \
  http://127.0.0.1:1234/api/sameloop-api/settings
```

For events and the integration test, install the test-only Python dependency:

```sh
python3 -m venv .venv
.venv/bin/pip install -r tests/requirements.txt
.venv/bin/python tools/ws-client.py subscribe
```

In another terminal, change the settings. The subscriber displays
`sameloop-controller/state` events and exits on Ctrl+C. Requests are sent to
`sameloop-api`; the event retains its controller namespace intentionally.

## Fault injection and integration tests

Stop the normal instance, then launch explicitly with test controls enabled:

```sh
./scripts/run-demo.py --test-controls
```

In another terminal:

```sh
.venv/bin/python tests/integration.py
```

Or let the suite start and stop its own disposable instances:

```sh
.venv/bin/python tests/run-suite.py
```

Tests change settings and inject simulation faults on a disposable demo instance.
They restore OFF, 25 °C and normal sensor settings at the end, but not the exact
initial thermal state. Restart the process to reset all simulation state.

Without `--test-controls`, `fault` is rejected. Internal APIs remain private
in both modes. The local demo does not implement viewer/operator authentication;
loopback binding is an exposure restriction, not role-based authorization.

## Behavior

- Startup OFF, setpoint 25 °C, initial simulated temperature 32.4 °C.
- AUTO: requested duty = clamp(20 × (temperature − setpoint), 0, 100).
- OFF or invalid/stale sensor: requested duty zero.
- Stale means a sample age of at least 1 second, using CLOCK_MONOTONIC.
- Overtemperature above 50 °C. On sensor loss retain its last known value and
  mark its quality unavailable. Startup value is not an all-clear until valid.
- Separate requested/applied duty and measured RPM; actuator feedback is floating
  point in this native API. A VSS adapter would round to integer signal types.
- Fan watchdog: command expires after one second without renewal; inertia
  remains, so feedback need not fall to zero immediately.
- Accepted settings apply on the next controller iteration. A settings reply
  acknowledges acceptance, not physical actuation.

The temperature model is initially embedded in the sensor binding and the fan
model in the fan binding. There is no dependency on a fifth `sameloop-plant`
project. [Architecture](docs/ARCHITECTURE.md) describes the future extraction.

The existing Flutter/LVGL 0.1.0 applications still use their local simulators.
This delivery provides their future backend; their network adapters are not
implemented here. The physical constants match those demos, but the integration
method here uses analytical interval solutions. Numerical equivalence with the
UI simulators has not been established.

## Repository layout and Git

Each project contains its sources, Meson build and MIT license. Bundle-level
scripts and documentation also live under `sameloop-api-binding/demo/` for
independent repository use. Example after publishing the repositories:

```sh
cd sameloop-api-binding
./demo/scripts/build-all.sh --workspace ..
./demo/scripts/run-demo.py --workspace ..
```

No remote repository is created or pushed by this archive. From each project:

```sh
git init -b main
git add .
git commit -m "Initial SameLoop AFB binding"
```

See [API contract](docs/API.md), [architecture](docs/ARCHITECTURE.md), and
[validation](docs/VALIDATION.md). MIT applies to these new sources, not to AFB.
