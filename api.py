from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import sqlite3
import numpy as np
import pickle
import pandas as pd
import os

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from huggingface_hub import hf_hub_download

from book_recommender import parse_query


# =========================
# APP INIT
# =========================
app = FastAPI(title="Book Recommendation System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# SERVE FRONTEND
# =========================
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def home():
    return FileResponse("frontend/index.html")


# =========================
# HF CONFIG
# =========================
HF_REPO_ID = "dummy9016/book-recommender-assets"
HF_TOKEN = os.getenv("HF_TOKEN")

MODEL_NAME = "all-MiniLM-L6-v2"

DB_FILE = "books.db"
EMBEDDINGS_FILE = "book_embeddings.npy"
METADATA_FILE = "books_metadata.pkl"


# =========================
# GLOBALS
# =========================
model = None
embeddings = None
df = None
DB_PATH = None


# =========================
# STARTUP
# =========================
@app.on_event("startup")
def load_assets():
    global model, embeddings, df, DB_PATH

    print("🚀 Loading assets from Hugging Face...")

    DB_PATH = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename=DB_FILE,
        token=HF_TOKEN
    )

    embeddings_path = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename=EMBEDDINGS_FILE,
        token=HF_TOKEN
    )

    metadata_path = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename=METADATA_FILE,
        token=HF_TOKEN
    )

    model = SentenceTransformer(MODEL_NAME)
    embeddings = np.load(embeddings_path)

    with open(metadata_path, "rb") as f:
        df = pickle.load(f)

    print("✅ Assets loaded successfully")


# =========================
# DB UTILS
# =========================
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# =========================
# REQUEST SCHEMA
# =========================
class DescriptionRequest(BaseModel):
    description: str


# =========================
# API ENDPOINTS
# =========================
@app.get("/book/isbn/{isbn}")
def get_book_by_isbn(isbn: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books WHERE ISBN = ?", (isbn,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return dict(row)


@app.post("/recommend")
def recommend_books(request: DescriptionRequest):
    text = request.description.strip()

    if len(text) < 3:
        raise HTTPException(status_code=400, detail="Description too short")

    parsed = parse_query(text)

    if isinstance(parsed, tuple):
        topic = parsed[0]
        k = parsed[1] if len(parsed) > 1 else 5
    else:
        topic = parsed
        k = 5

    query_vec = model.encode([topic])
    similarities = cosine_similarity(query_vec, embeddings)

    k = min(k, similarities.shape[1])
    top_indices = similarities[0].argsort()[-k:][::-1]

    results_df = df.iloc[top_indices]

    results = []
    for _, row in results_df.iterrows():
        results.append({
            "Acc_No": int(row["Acc_No"]) if not pd.isna(row["Acc_No"]) else None,
            "Title": str(row["Title"]),
            "Author_Editor": str(row["Author_Editor"]),
            "ISBN": str(row["ISBN"]),
            "Year": int(row["Year"]) if not pd.isna(row["Year"]) else None,
            "description": str(row["description"]),
            "image_url": str(row.get("image_url", ""))
        })

    return {
        "query": text,
        "results": results
    }


@app.get("/random")
def get_random_books():
    sample_df = df.sample(n=min(15, len(df)))
    return {
        "results": [
            {
                "Title": str(row["Title"]),
                "Author_Editor": str(row["Author_Editor"]),
                "description": str(row["description"]),
                "image_url": str(row.get("image_url", ""))
            }
            for _, row in sample_df.iterrows()
        ]
    }
