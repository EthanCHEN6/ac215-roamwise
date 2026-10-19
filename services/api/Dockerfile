FROM ghcr.io/astral-sh/uv:0.8.22-python3.12-bookworm-slim@sha256:28df4bbd896cf66a224f2e0cb22240a9a2b9803a3a13519bcadf2e9fdd68c632
WORKDIR /app
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy ANONYMIZED_TELEMETRY=False TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2
COPY services/api/pyproject.toml services/api/uv.lock ./
RUN uv sync --frozen --no-dev
COPY roamwise ./roamwise
COPY config ./config
COPY frontend ./frontend
CMD ["uv","run","--frozen","--no-sync","uvicorn","roamwise.api:app","--host","0.0.0.0","--port","8000"]
