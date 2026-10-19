# KB4IT container image: the release wheel, with its extras, on python:<version>-slim,
# run as a non-root user.
#
# The build context is a folder holding only the KB4IT wheel: build.sh prepares it in
# dist/image/, and the publish workflow does the same with the wheel it uploads to PyPI,
# so the image runs exactly the published KB4IT.
#
# Usage:
#   docker run --rm -v "$PWD:/work" --user "$(id -u):$(id -g)" IMAGE build config/repo.json
#   docker run --rm -p 8642:8642 -v "$PWD:/work" IMAGE serve config/repo.json --host 0.0.0.0
#   podman run --rm -v "$PWD:/work:Z" IMAGE build config/repo.json

ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION}-slim

# Passed by build.sh and the publish workflow (texts from lib/common.sh).
ARG KB4IT_VERSION=""
ARG KB4IT_REVISION=""
ARG KB4IT_DESCRIPTION=""

LABEL org.opencontainers.image.title="KB4IT" \
      org.opencontainers.image.description="${KB4IT_DESCRIPTION}" \
      org.opencontainers.image.version="${KB4IT_VERSION}" \
      org.opencontainers.image.revision="${KB4IT_REVISION}" \
      org.opencontainers.image.source="https://github.com/t00m/KB4IT" \
      org.opencontainers.image.documentation="https://t00m.github.io/KB4IT/" \
      org.opencontainers.image.licenses="GPL-3.0-or-later"

COPY kb4it-*.whl /tmp/wheels/
RUN set -eux; \
    wheel="$(ls /tmp/wheels/kb4it-*.whl)"; \
    pip install --no-cache-dir --disable-pip-version-check "${wheel}[extras]"; \
    rm -rf /tmp/wheels; \
    useradd --uid 1000 --create-home --shell /usr/sbin/nologin kb4it; \
    install -d -o kb4it -g kb4it /work

# KB4IT_HOME in /tmp, so the image also runs with --user "$(id -u):$(id -g)": then the
# files it writes in /work belong to the person running it.
ENV KB4IT_HOME=/tmp/kb4it \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER kb4it
WORKDIR /work
EXPOSE 8642

ENTRYPOINT ["kb4it"]
CMD ["--help"]
