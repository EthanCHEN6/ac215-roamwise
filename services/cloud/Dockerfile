FROM ghcr.io/astral-sh/uv:0.8.22-python3.12-bookworm-slim@sha256:28df4bbd896cf66a224f2e0cb22240a9a2b9803a3a13519bcadf2e9fdd68c632
WORKDIR /app
ENV PYTHONUNBUFFERED=1 UV_LINK_MODE=copy ANONYMIZED_TELEMETRY=False TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 DATA_DIR=/app/data EVIDENCE_DIR=/tmp/evidence PORT=8080 HOME=/home/app
COPY services/api/pyproject.toml services/api/uv.lock ./
RUN uv sync --frozen --no-dev && useradd --create-home --uid 10001 app
COPY roamwise ./roamwise
COPY config ./config
COPY frontend ./frontend
COPY data/processed ./data/processed
RUN uv run --frozen --no-sync python -m roamwise.data_agent && uv run --frozen --no-sync python -m roamwise.index && chown -R app:app /app/data /home/app /tmp/evidence
USER app
EXPOSE 8080
CMD ["sh","-c","exec uv run --frozen --no-sync uvicorn roamwise.cloud:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --limit-concurrency 24"]
