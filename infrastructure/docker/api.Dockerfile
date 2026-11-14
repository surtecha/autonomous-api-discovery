FROM python:3.12-slim AS build
WORKDIR /build
COPY pyproject.toml requirements.lock ./
COPY packages ./packages
COPY apps/api ./apps/api
COPY apps/__init__.py ./apps/__init__.py
RUN python -m pip wheel --wheel-dir=/wheels -r requirements.lock && python -m pip wheel --wheel-dir=/wheels --no-deps .
FROM python:3.12-slim
COPY --from=build /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index /wheels/* && rm -rf /wheels
WORKDIR /app
COPY packages ./packages
COPY apps/api ./apps/api
COPY apps/__init__.py ./apps/__init__.py
COPY alembic.ini ./
COPY experiments/configs ./experiments/configs
RUN mkdir -p /app/.runtime/artifacts && chown -R 65532:65532 /app/.runtime
USER 65532:65532
ENV PYTHONDONTWRITEBYTECODE=1
CMD ["uvicorn", "apps.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
