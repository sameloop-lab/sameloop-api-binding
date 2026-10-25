#!/usr/bin/env python3
"""Launch the four local modules; no global installation or shell interpolation."""
import argparse
import json
import os
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parents[1])
p.add_argument('--port', type=int, default=1234)
p.add_argument('--binder', default='afb-binder')
p.add_argument('--test-controls', action='store_true')
p.add_argument('--write-config-only', action='store_true')
a = p.parse_args()
if not 1024 <= a.port <= 65535:
    p.error('port must be between 1024 and 65535')
root = a.workspace.resolve()
bindings = []
for role in ('fan', 'sensor', 'controller', 'api'):
    module = root / f'sameloop-{role}-binding/build/sameloop-{role}-binding.so'
    if not module.is_file():
        p.error(f'missing module: {module}; run build-all.sh first')
    entry = {'path': ('public:' if role == 'api' else 'private:') + str(module)}
    if role == 'api':
        entry['config'] = {'test_controls': a.test_controls}
    bindings.append(entry)
run = root / 'run'
run.mkdir(exist_ok=True)
config = {'binding': bindings, 'interface': [f'tcp:127.0.0.1:{a.port}'],
          'rootapi': '/api', 'workdir': str(run), 'foreground': True,
          'name': 'sameloop-demo', 'log': 'error+warning+notice'}
path = run / f'binder-{a.port}.json'
path.write_text(json.dumps(config, indent=2) + '\n')
print(f'Config: {path}', flush=True)
print(f'API: http://127.0.0.1:{a.port}/api/sameloop-api/get', flush=True)
if not a.write_config_only:
    binder = shutil.which(a.binder)
    if not binder:
        p.error(f'binder not found: {a.binder}')
    os.execv(binder, [binder, '--config=' + str(path)])
