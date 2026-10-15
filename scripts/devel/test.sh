#!/usr/bin/env bash
# Run the KB4IT tests from this working tree with the runtime dependencies and pytest.
# Usage: test.sh [--python X.Y] [pytest arguments]   (default Python 3.11; also KB4IT_TEST_PYTHON)
set -euo pipefail
cd "$(dirname "$0")/../.."
python_version="${KB4IT_TEST_PYTHON:-3.11}"
if [[ "${1:-}" == "--python" ]]; then
    python_version="$2"
    shift 2
fi
exec uv run --no-project --python "$python_version" \
    --with pytest --with "Mako==1.3.12" --with "Markdown>=3.5" --with "PyYAML>=6.0" --with "Pygments>=2.15" \
    --with lxml --with "rich>=13.0" --with "textual>=0.47.0" --with "pymdown-extensions>=10.0" \
    python -m pytest "$@"
