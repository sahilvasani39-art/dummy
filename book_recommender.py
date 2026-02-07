# book_recommender.py
from huggingface_hub import hf_hub_download
import sqlite3
import numpy as np
import pickle

def load_assets():
    db_path = hf_hub_download(
        repo_id="dummy9016/book-recommender-assets",
        filename="books.db",
        repo_type="model"
    )

    embeddings_path = hf_hub_download(
        repo_id="dummy9016/book-recommender-assets",
        filename="book_embeddings.npy",
        repo_type="model"
    )

    metadata_path = hf_hub_download(
        repo_id="dummy9016/book-recommender-assets",
        filename="books_metadata.pkl",
        repo_type="model"
    )

    return db_path, embeddings_path, metadata_path


def parse_query(query: str):
    # 👉 paste your existing parse_query logic here
    return query
