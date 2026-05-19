# KB4IT container image.
# Multi-stage build: wheel is built in the first stage; runtime keeps only
# asciidoctor + Python + the wheel. Alpine/Debian-slim would also work, but
# asciidoctor pulls a large Ruby toolchain on Alpine, so we use debian:slim.

ARG PYTHON_VERSION=3.12

# ---------------------------------------------------------------------------
# Stage 1: build the wheel
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /src

RUN python -m pip install --no-cache-dir --upgrade pip build

COPY pyproject.toml README.rst LICENSE AUTHORS Changelog THANKS ./
COPY kb4it ./kb4it

RUN python -m build --wheel --outdir /wheels

# ---------------------------------------------------------------------------
# Stage 2: runtime image
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

LABEL org.opencontainers.image.title="KB4IT" \
      org.opencontainers.image.description="Static website generator based on Asciidoctor sources" \
      org.opencontainers.image.source="https://github.com/t00m/KB4IT" \
      org.opencontainers.image.licenses="GPL-3.0-or-later"

# Asciidoctor is a runtime dependency (called via subprocess).
# source-highlight and graphviz are commonly used by themes; install if
# users need them. Keep image lean: only asciidoctor by default.
RUN apt-get update \
 && apt-get install -y --no-install-recommends asciidoctor \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Non-root user. Mounted repos can be any UID; override with --user if needed.
RUN useradd --create-home --shell /bin/bash kb4it
USER kb4it
WORKDIR /home/kb4it

# Two well-known mountpoints:
#   /work   -> the KB4IT repo directory passed to `kb4it build`
#   /out    -> optional target directory
VOLUME ["/work", "/out"]

ENTRYPOINT ["kb4it"]
CMD ["--help"]
