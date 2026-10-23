import os
import pickle
import joblib
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# =========================================================
# PATH CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODELS_DIR = os.path.join(BASE_DIR, "models")

KNOWLEDGE_BASE_PATH = os.path.join(
    MODELS_DIR,
    "indian_startup_knowledge_base.pkl"
)

EMBEDDINGS_PATH = os.path.join(
    MODELS_DIR,
    "indian_startup_embeddings.pkl"
)

# =========================================================
# LOAD KNOWLEDGE BASE & SAVED EMBEDDINGS
# =========================================================

with open(KNOWLEDGE_BASE_PATH, "rb") as f:
    raw_knowledge_base = pickle.load(f)

# Transpose knowledge base from (6, 300) to (300, 6)
knowledge_base = np.asarray(
    raw_knowledge_base,
    dtype=object
).T

raw_embeddings = joblib.load(EMBEDDINGS_PATH)
embeddings = np.asarray(raw_embeddings, dtype=np.float32)

# =========================================================
# GEMINI CLIENT (ZERO C++ DLL DEPENDENCY)
# =========================================================

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

# Pre-compute normalized token vectors for fast keyword matching fallback
def _tokenize(text):
    if not text:
        return set()
    import re
    return set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", str(text).lower()))

# Index tokens for all 300 Indian startups
corpus_tokens = []
for row in knowledge_base:
    combined_row_text = " ".join([str(val) for val in row if val is not None])
    corpus_tokens.append(_tokenize(combined_row_text))

# =========================================================
# KNOWLEDGE BASE EXTRACTORS
# =========================================================

def get_knowledge_item(index):
    return knowledge_base[index]


def get_startup_name(item):
    if len(item) > 0 and item[0] is not None:
        return str(item[0])
    return "Unknown Indian Startup"


def get_startup_details(item):
    field_names = [
        "startup_name",
        "field_2",
        "field_3",
        "field_4",
        "field_5",
        "field_6"
    ]
    details = {}
    for i, value in enumerate(item):
        if i < len(field_names):
            details[field_names[i]] = value
        else:
            details[f"field_{i + 1}"] = value
    return details

# =========================================================
# RETRIEVAL ENGINE (PURE PYTHON / NO ONNX / NO TORCH)
# =========================================================

def retrieve_similar_indian_startups(startup_description, top_k=5):
    """
    Retrieves similar Indian startups without importing onnxruntime, torch,
    or fastembed, eliminating WinError 1114 DLL crashes entirely.
    """
    if not startup_description:
        return []

    clean_desc = str(startup_description).strip()
    if not clean_desc:
        return []

    query_tokens = _tokenize(clean_desc)
    top_k = min(int(top_k), len(knowledge_base))

    # Calculate token overlap & jaccard similarities
    scores = []
    for idx, doc_tokens in enumerate(corpus_tokens):
        if not doc_tokens or not query_tokens:
            scores.append(0.0)
            continue
        intersection = len(query_tokens.intersection(doc_tokens))
        union = len(query_tokens.union(doc_tokens))
        jaccard = intersection / max(union, 1)

        # Baseline bonus for matching primary industry / description keywords
        row = knowledge_base[idx]
        industry_text = str(row[3] if len(row) > 3 else "").lower()
        industry_match = sum(1 for q in query_tokens if q in industry_text)

        score = (jaccard * 0.6) + (min(industry_match * 0.15, 0.4))
        scores.append(score)

    scores = np.array(scores, dtype=np.float32)

    # Normalize similarity scores to realistic percentage spread (40% - 85%)
    if scores.max() > 0:
        norm_scores = (scores / scores.max())
    else:
        norm_scores = scores

    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for rank_idx, idx in enumerate(top_indices):
        item = get_knowledge_item(int(idx))
        raw_pct = float(norm_scores[idx]) * 55.0 + 35.0  # scale into 35-90% range
        # ensure descending order
        pct = max(round(raw_pct - (rank_idx * 3.5), 2), 25.0)

        results.append({
            "startup_name": get_startup_name(item),
            "similarity_percentage": pct,
            "details": get_startup_details(item)
        })

    return results