FROM python:3.12-slim
WORKDIR /app
COPY targets/__init__.py targets/service.py ./targets/
USER 65532:65532
ENV PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["python", "-m", "targets.service"]
