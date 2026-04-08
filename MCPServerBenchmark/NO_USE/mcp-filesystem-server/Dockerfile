FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir uv

COPY pyproject.toml .

RUN uv venv && \
    uv pip compile pyproject.toml -o requirements.txt && \
    uv pip install --no-cache -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /build/.venv /app/.venv

COPY server.py tools.py utils.py __init__.py ./

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
VOLUME ["/data"]

ENTRYPOINT ["python", "server.py"]
CMD ["--allowed-root", "/data", "--port", "8000"]