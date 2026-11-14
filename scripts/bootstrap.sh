#!/usr/bin/env bash
set -euo pipefail
conda run -n api-discovery-ai python --version
conda run -n api-discovery-ai python -c 'import sys; assert sys.version_info[:2] == (3, 12); assert sys.prefix.endswith("api-discovery-ai")'
conda run -n api-discovery-ai python -m pip --version
if [ -f requirements-dev.lock ]; then
  conda run -n api-discovery-ai python -m pip install --no-user -r requirements-dev.lock
  conda run -n api-discovery-ai python -m pip install --no-user --no-deps --no-build-isolation -e .
else
  conda run -n api-discovery-ai python -m pip install --no-user -e '.[dev]'
  conda run -n api-discovery-ai python -m scripts.lock_dependencies
fi
npm ci --prefix apps/web --ignore-scripts
