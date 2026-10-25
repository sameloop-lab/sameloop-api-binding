#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace=$(cd -- "$script_dir/.." && pwd)
if [[ ${1:-} == --workspace && $# == 2 ]]; then
    workspace=$(cd -- "$2" && pwd)
elif [[ $# != 0 ]]; then
    echo "Usage: $0 [--workspace DIRECTORY]" >&2
    exit 2
fi
for role in fan sensor controller api; do
    project="$workspace/sameloop-$role-binding"
    if [[ ! -f "$project/meson.build" ]]; then
        echo "Missing sibling project: $project" >&2; exit 1
    fi
    if [[ -f "$project/build/meson-private/coredata.dat" ]]; then
        meson setup --reconfigure "$project/build" "$project"
    else
        meson setup "$project/build" "$project" --buildtype=debugoptimized
    fi
    meson compile -C "$project/build"
    meson test -C "$project/build" --print-errorlogs
done
