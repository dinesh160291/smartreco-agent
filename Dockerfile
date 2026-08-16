# SmartReco — single long-running process with a persistent disk.
#
# The stack is deliberately single-process: the relational store is embedded,
# the vector index is embedded, and the scheduler runs in-process. Do not add
# worker processes here — two workers on one vector-index directory is
# corruption, and the scheduler would fire its jobs once per worker.
# Concurrency comes from the server's thread pool, which is what the run
# ceiling in the policy catalog bounds.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first so a code change does not reinstall them.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The relational store is the system of record and is NOT re-derivable; the
# vector index is. Both live here, and this path must be a mounted volume.
ENV DATABASE_URL=sqlite:////data/smartreco.db \
    CHROMA_PATH=/data/chroma
VOLUME ["/data"]

EXPOSE 8000

# One worker, on purpose — see the note at the top of this file.
CMD ["uvicorn", "apps.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
