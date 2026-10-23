import os
import joblib
import pandas as pd
from Utils.feature_generation import generate_ml_features, FEATURES

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODELS_DIR = os.path.join(BASE_DIR, "models")

MODEL_PATH = os.path.join(
    MODELS_DIR,
    "startup_validator_random_forest.pkl"
)

PREPROCESSOR_PATH = os.path.join(
    MODELS_DIR,
    "startup_validator_preprocessor.pkl"
)

# Load Scikit-Learn Model & Preprocessor
model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)


def predict_startup_success(startup_description, failure_results=None, indian_startups=None):
    """
    Generates structured AI features based on the thesis and comparable data,
    passes them through the preprocessor, and calculates success/failure probability.
    """
    if not startup_description:
        raise ValueError("Startup description cannot be empty.")

    # 1. Generate realistic tabular features via Gemini
    feature_data = generate_ml_features(
        startup_description,
        failure_context=failure_results,
        competitor_context=indian_startups
    )

    # 2. Structure DataFrame input
    df_input = pd.DataFrame([feature_data], columns=FEATURES)

    # 3. Transform via trained ColumnTransformer pipeline
    X_processed = preprocessor.transform(df_input)

    # 4. Predict
    prediction = int(model.predict(X_processed)[0])
    probabilities = model.predict_proba(X_processed)[0]
    classes = list(model.classes_)

    prob_map = {int(c): float(p) for c, p in zip(classes, probabilities)}

    return {
        "prediction": prediction,
        "status": "Likely Successful" if prediction == 1 else "Likely to Fail",
        "success_probability": round(prob_map.get(1, 0.0) * 100, 2),
        "failure_probability": round(prob_map.get(0, 0.0) * 100, 2),
        "features_inferred": feature_data
    }