FROM ghcr.io/astral-sh/uv:0.8.22-python3.12-bookworm-slim@sha256:28df4bbd896cf66a224f2e0cb22240a9a2b9803a3a13519bcadf2e9fdd68c632
WORKDIR /app
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY services/ingest/pyproject.toml services/ingest/uv.lock ./
RUN uv sync --frozen --no-dev
COPY roamwise ./roamwise
COPY config ./config
CMD ["uv", "run", "--frozen", "--no-sync", "python", "-m", "roamwise.ingest"]
