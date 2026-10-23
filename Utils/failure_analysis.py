import os
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# =========================================================
# PATH CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_DIR = os.path.join(BASE_DIR, "models")

VECTORIZER_PATH = os.path.join(
    MODEL_DIR,
    "failure_tfidf_vectorizer.pkl"
)

TFIDF_MATRIX_PATH = os.path.join(
    MODEL_DIR,
    "failure_tfidf_matrix.pkl"
)

KNOWLEDGE_BASE_PATH = os.path.join(
    MODEL_DIR,
    "failure_knowledge_base.pkl"
)

# =========================================================
# LOAD ARTIFACTS
# =========================================================

vectorizer = joblib.load(VECTORIZER_PATH)
tfidf_matrix = joblib.load(TFIDF_MATRIX_PATH)
knowledge_base = joblib.load(KNOWLEDGE_BASE_PATH)

if isinstance(knowledge_base, pd.DataFrame):
    knowledge_base = knowledge_base.reset_index(drop=True)

# =========================================================
# EXTRACTORS
# =========================================================

def _get_name(item):
    if isinstance(item, pd.Series):
        for field in ["name", "startup_name", "company", "company_name"]:
            if field in item.index and pd.notna(item[field]):
                val = str(item[field]).strip()
                if val:
                    return val
        return "Historical Startup"

    if isinstance(item, dict):
        for field in ["name", "startup_name", "company", "company_name"]:
            if field in item and item[field] is not None:
                val = str(item[field]).strip()
                if val:
                    return val

    return "Historical Startup"


def _get_item(index):
    if isinstance(knowledge_base, pd.DataFrame):
        return knowledge_base.iloc[index]
    return knowledge_base[index]

# =========================================================
# RETRIEVAL FUNCTION
# =========================================================

def retrieve_similar_failures(startup_description, top_k=5):
    if not isinstance(startup_description, str):
        raise ValueError("startup_description must be a string.")

    startup_description = startup_description.strip()
    if not startup_description:
        return []

    query_vector = vectorizer.transform([startup_description])
    similarities = cosine_similarity(query_vector, tfidf_matrix)[0]

    top_k = min(max(int(top_k), 1), len(similarities))
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for index in top_indices:
        item = _get_item(index)
        score = float(similarities[index])
        results.append({
            "startup_name": _get_name(item),
            "similarity_score": round(score, 4),
            "similarity_percentage": round(score * 100, 2),
            "details": item.to_dict() if isinstance(item, pd.Series) else item
        })

    return results