# Validation — 2026-10-24

Performed in an isolated Linux x86_64 environment, GCC 13.3.0, Meson 1.12.1,
JSON-C 0.17, Python 3.12 and websockets 16.0. This is not a Fedora target test.

## Results

- Four independent Meson builds: PASS, warnings treated as errors in project code.
  AFB dependency headers are classified as system includes.
- Three model test executables: PASS (thermal model, fan inertia/watchdog,
  controller clamping and freshness boundaries).
- Four DESTDIR installations: PASS.
- Real afb-binder loading and HTTP GET/POST: PASS.
- 11 WebSocket integration scenarios: PASS (see integration-results.txt).
- Normal profile rejects fault injection: PASS.
- Restart resets mode/setpoint to OFF/25: PASS.
- Internal APIs cannot be called from public WebSocket clients: PASS.
- Two concurrent client subscriptions and selective unsubscribe: PASS.

These are functional checks, not performance measurements, exhaustive coverage,
long-duration soak tests or a security certification. No GUI integration,
ARM hardware, SMACK/Cynagora policy, RPM or Yocto build has been tested here.

## Upstream revisions used

- [afb-binding](https://github.com/redpesk-core/afb-binding/tree/7dccf145476a0257c9b95f7341bc00699849f8af): `7dccf145476a0257c9b95f7341bc00699849f8af`
- [afb-libafb](https://github.com/redpesk-core/afb-libafb/tree/e8f6e32da7265f035e9ed33296ed76539ec27ae9): `e8f6e32da7265f035e9ed33296ed76539ec27ae9`
- [afb-binder](https://github.com/redpesk-core/afb-binder/tree/4f0ffde2d01a160233bb3e09bf919d1585f6af4a): `4f0ffde2d01a160233bb3e09bf919d1585f6af4a`
- [rp-lib-utils](https://github.com/redpesk-core/rp-lib-utils/tree/a8841ee324752a0b31ae6a3a33e48cadae19a465): `a8841ee324752a0b31ae6a3a33e48cadae19a465`

The test runtime was built with systemd, Cynagora, uuid and libmagic integration
disabled, HTTP enabled. Headers 4.3.0, libafb project 5.7.5 and binder 5.4.0.
The source build requires afb-binding >=4.2.0; compatibility with every older
binder implementing that header generation is not claimed. Use the revisions
above as the initial validated reference.

The archive contains only new MIT-licensed project sources, docs and scripts;
it does not redistribute the upstream libraries or the locally built executables.
