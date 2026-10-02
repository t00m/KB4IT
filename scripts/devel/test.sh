#!/usr/bin/env bash
# Run the KB4IT tests from this working tree with the runtime dependencies and pytest.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec uv run --no-project --python 3.11 \
    --with pytest --with "Mako==1.3.12" --with "Markdown>=3.5" --with "PyYAML>=6.0" \
    --with lxml --with "rich>=13.0" --with "textual>=0.47.0" \
    python -m pytest "$@"
