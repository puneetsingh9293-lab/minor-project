# AI Startup Validator

A Streamlit application for evaluating startup ideas. It combines a trained success-prediction model, retrieval over startup-failure data, Indian-startup similarity analysis, and Gemini-powered idea refinement to produce a practical validation report.

## Features

- Estimates startup success probability from structured business inputs.
- Finds similar historical startup failures and explains relevant risks.
- Retrieves comparable Indian startups for market context.
- Uses Google Gemini to generate an improved concept, risks, and an action plan.
- Produces a downloadable PDF report.

## Project structure

```text
app.py                 Streamlit application entry point
Utils/                 Prediction, retrieval, generative-AI, and PDF helpers
models/                Trained models and embedding artifacts
Datasets/              Source datasets used by the project
*.ipynb                Exploration and model-development notebooks
```

## Quick start

Requirements: Python 3.10 or later and a Google Gemini API key.

```bash
git clone https://github.com/puneetsingh9293-lab/minor-project.git
cd minor-project
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and replace the placeholder with your Gemini API key:

```env
GEMINI_API_KEY=your_google_gemini_api_key
```

Then start the application:

```bash
streamlit run app.py
```

Streamlit will display a local URL, usually `http://localhost:8501`.

## Data and models

The repository includes the trained model artifacts needed by the application, including a SentenceTransformer embedding model. The embedding weights are approximately 87 MB; GitHub accepts this file but recommends Git LFS for large binary assets.

## Security

The real `.env` file is intentionally excluded from Git. Keep API keys out of source code, notebooks, datasets, and commits. If a key is ever committed, revoke it and create a new one before publishing the repository.

## License

No license has been selected yet. Add one before sharing or accepting external contributions so the permitted use of the code is clear.
