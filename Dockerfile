FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/usr/local/share/nltk_data \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .

# 1️⃣ Upgrade pip
# 2️⃣ Lock NumPy (avoid NumPy 2.x)
# 3️⃣ Force correct PyTorch CPU wheel
# 4️⃣ Install remaining deps
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

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
