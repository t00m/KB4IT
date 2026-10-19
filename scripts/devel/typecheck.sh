#!/usr/bin/env bash
# Type-check the annotated seams of KB4IT with mypy --strict, as CI does (AR-06).
# Other modules are followed for their names only; they are not checked.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec uvx --from "mypy==2.4.0" --with "types-PyYAML==6.0.12.20260906" mypy --strict --python-version 3.11 \
    --follow-imports=silent --ignore-missing-imports \
    kb4it/core/paths.py kb4it/core/dates.py kb4it/core/documents.py kb4it/core/files.py \
    kb4it/services/themekit kb4it/services/pipeline.py "$@"
