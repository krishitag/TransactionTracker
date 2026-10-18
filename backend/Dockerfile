# Backend API image (FastAPI + scoring model + embedding model). Build from the repo root:
#   docker build -t risk-backend ./backend
# Secrets (DATABASE_URL, GEMINI_API_KEY, ...) are passed in at run time, never baked into the image.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app
RUN useradd --create-home --uid 1000 app

# Packages first: Docker caches this layer, so code-only changes rebuild in seconds.
# CPU-only PyTorch: servers have no GPU, and the CPU build is far smaller.
COPY requirements.txt .
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Download the embedding model now, so the server never fetches it at startup.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Only what the API needs at run time (see .dockerignore: everything else is excluded).
COPY main.py ask.py embeddings.py features.py scoring.py ./
COPY models/ models/
RUN chown -R app:app /app

# Run as a normal user, and never try to reach Hugging Face from the running server.
USER app
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# Memory savers for the 512 MB tier (measured peak before these: 444 MiB):
# one PyTorch/BLAS thread is plenty for embedding one short question, and capping glibc's
# per-thread memory pools stops a long-running Python server slowly growing.
ENV OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MALLOC_ARENA_MAX=2

# Render sets PORT; locally it defaults to 8000. One worker keeps memory low (512 MB free tier).
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
