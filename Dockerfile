FROM python:3.11-slim

# -----------------------------
# Environment variables
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/usr/local/share/nltk_data \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

# -----------------------------
# Install dependencies
# -----------------------------
COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install numpy==1.26.4 \
 && pip install torch==2.4.1+cpu --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements.txt \
 && python - <<'PY'
import nltk
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("omw-1.4")
PY

# -----------------------------
# Copy application code
# -----------------------------
COPY . .

# -----------------------------
# Expose & run
# -----------------------------
EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
