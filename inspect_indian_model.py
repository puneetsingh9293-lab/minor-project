import os
import pickle
import joblib
import numpy as np


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODELS_DIR = os.path.join(
    BASE_DIR,
    "models"
)


# =========================================================
# KNOWLEDGE BASE
# =========================================================

kb_path = os.path.join(
    MODELS_DIR,
    "indian_startup_knowledge_base.pkl"
)

print("=" * 70)
print("KNOWLEDGE BASE INSPECTION")
print("=" * 70)

with open(
    kb_path,
    "rb"
) as f:

    kb = pickle.load(f)


print("Type:")
print(type(kb))

print("\nShape:")
print(getattr(kb, "shape", "No shape"))

print("\nDtype:")
print(getattr(kb, "dtype", "No dtype"))

print("\nNumber of dimensions:")
print(getattr(kb, "ndim", "No ndim"))


print("\nFirst item:")
print(kb[0])


print("\nFirst item type:")
print(type(kb[0]))


# =========================================================
# EMBEDDINGS
# =========================================================

emb_path = os.path.join(
    MODELS_DIR,
    "indian_startup_embeddings.pkl"
)

print("\n" + "=" * 70)
print("EMBEDDINGS INSPECTION")
print("=" * 70)

embeddings = joblib.load(
    emb_path
)


print("Type:")
print(type(embeddings))

print("\nShape:")
print(getattr(
    embeddings,
    "shape",
    "No shape"
))

print("\nDtype:")
print(getattr(
    embeddings,
    "dtype",
    "No dtype"
))

print("\nFirst embedding:")
print(embeddings[0][:10])

print("\nFirst embedding type:")
print(type(embeddings[0]))


# =========================================================
# SUMMARY
# =========================================================

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(
    f"Knowledge base: {kb.shape}"
)

print(
    f"Embeddings:     {embeddings.shape}"
)

print("=" * 70)