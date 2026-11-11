#!/usr/bin/env bash
set -euo pipefail

# Render's native Python runtime also supplies Node/npm. Versions are pinned in render.yaml.
# No migration, seed, provider synchronization or service creation occurs in this build.
python -m pip install --requirement requirements.txt
npx --yes pnpm@10.20.0 --dir frontend install --frozen-lockfile --prod=false
npx --yes pnpm@10.20.0 --dir frontend build
