FROM python:3.12-slim
COPY requirements-validator.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir -r /tmp/requirements.lock && rm /tmp/requirements.lock
USER 65532:65532
WORKDIR /artifacts
ENV PYTHONDONTWRITEBYTECODE=1
