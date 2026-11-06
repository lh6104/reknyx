FROM python:3.13.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.11 /uv /usr/local/bin/uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock /app/backend/
COPY backend/src /app/backend/src
COPY backend/alembic.ini /app/backend/alembic.ini
COPY backend/migrations /app/backend/migrations
COPY contracts/openapi.yaml /app/contracts/openapi.yaml
COPY scripts/contract_hashes.py /app/scripts/contract_hashes.py
RUN cd /app/backend && uv sync --frozen --no-dev && groupadd --gid 10001 reknyx && useradd --uid 10001 --gid 10001 --no-create-home reknyx && mkdir /var/lib/reknyx && chown reknyx:reknyx /var/lib/reknyx
USER 10001:10001
WORKDIR /app/backend
ENV PATH="/app/backend/.venv/bin:$PATH" REKNYX_ARTIFACT_ROOT=/var/lib/reknyx/artifacts REKNYX_REPOSITORY_ROOT=/app
EXPOSE 8000
CMD ["uvicorn", "reknyx.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
