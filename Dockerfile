FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates chromium fonts-liberation git \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system grna \
    && adduser --system --ingroup grna --home /app grna \
    && mkdir -p /data/workspaces /data/artifacts /data/jobs /data/logs \
    && chown -R grna:grna /app /data

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install ".[pdf]"

USER grna

EXPOSE 8080 8090

CMD ["python", "-m", "uvicorn", "grna.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
