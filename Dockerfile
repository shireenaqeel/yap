# Hugging Face Spaces (Docker SDK) — runs the Streamlit app.
# HF no longer offers a native "streamlit" SDK, so we ship our own image.
FROM python:3.11-slim

# HF Spaces run the container as a non-root user (uid 1000). Set up a writable
# HOME so sentence-transformers can cache the embedding model at runtime.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR $HOME/app

# Install CPU-only torch FIRST so sentence-transformers doesn't pull the huge
# CUDA build (smaller image, faster, no GPU needed on free CPU Spaces).
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

# HF routes external traffic to the port declared as `app_port` in README.md.
EXPOSE 8501
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
