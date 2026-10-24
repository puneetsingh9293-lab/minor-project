import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

PRIMARY_MODELS = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
]

FEATURES = [
    "state_code", "latitude", "longitude",
    "age_first_funding_year", "age_last_funding_year",
    "age_first_milestone_year", "age_last_milestone_year",
    "relationships", "funding_rounds", "funding_total_usd",
    "milestones", "category_code",
    "has_VC", "has_angel", "has_roundA", "has_roundB",
    "has_roundC", "has_roundD", "avg_participants", "is_top500",
    "founded_year", "first_funding_year", "last_funding_year",
    "years_to_first_funding", "funding_period_years"
]

VALID_CATEGORIES = [
    "advertising", "analytics", "automotive", "biotech", "cleantech",
    "consulting", "ecommerce", "education", "enterprise", "fashion",
    "finance", "games_video", "hardware", "health", "manufacturing",
    "medical", "messaging", "mobile", "music", "network_hosting",
    "news", "other", "photo_video", "public_relations", "real_estate",
    "search", "security", "semiconductor", "social", "software",
    "sports", "transportation", "travel", "web"
]


def _get_fallback_features():
    return {
        "state_code": "CA",
        "latitude": 37.77,
        "longitude": -122.41,
        "age_first_funding_year": 1.2,
        "age_last_funding_year": 2.8,
        "age_first_milestone_year": 1.0,
        "age_last_milestone_year": 2.5,
        "relationships": 3,
        "funding_rounds": 2,
        "funding_total_usd": 750000,
        "milestones": 2,
        "category_code": "software",
        "has_VC": 1,
        "has_angel": 1,
        "has_roundA": 1,
        "has_roundB": 0,
        "has_roundC": 0,
        "has_roundD": 0,
        "avg_participants": 2.0,
        "is_top500": 0,
        "founded_year": 2024,
        "first_funding_year": 2025,
        "last_funding_year": 2026,
        "years_to_first_funding": 1.0,
        "funding_period_years": 1.0
    }


def generate_ml_features(startup_description, failure_context=None, competitor_context=None):
    if not client:
        return _get_fallback_features()

    context = f"""
STARTUP THESIS:
{startup_description}

SIMILAR HISTORICAL FAILURES DETECTED:
{json.dumps(failure_context or [], default=str)[:1000]}

SIMILAR ACTIVE COMPETITORS DETECTED:
{json.dumps(competitor_context or [], default=str)[:1000]}
"""

    prompt = f"""
You are a quantitative venture capital analyst and machine learning data extractor.
Analyze the startup description and comparative market evidence below.
Infer realistic quantitative and categorical feature values required by our Random Forest startup success model.

Valid options for 'category_code':
{VALID_CATEGORIES}

Extract or realistically infer these exact 25 fields and return ONLY a valid JSON object:
- "state_code": string (valid US state code where such tech clusters operate, default "CA")
- "latitude": float (e.g. 37.7749)
- "longitude": float (e.g. -122.4194)
- "age_first_funding_year": float (years between founding and first funding round, e.g. 0.8 to 2.5)
- "age_last_funding_year": float (years between founding and last funding round, e.g. 1.5 to 4.5)
- "age_first_milestone_year": float (years to 1st major product/customer milestone, e.g. 0.8 to 2.0)
- "age_last_milestone_year": float (years to latest milestone, e.g. 2.0 to 4.0)
- "relationships": integer (core network & advisor connections, 1 to 10)
- "funding_rounds": integer (total funding rounds needed for thesis, 1 to 4)
- "funding_total_usd": integer (estimated total capital needed based on industry competitors, e.g. 250000 to 5000000)
- "milestones": integer (expected operational milestones, 1 to 6)
- "category_code": string (MUST be strictly one from the valid list above)
- "has_VC": integer (0 or 1)
- "has_angel": integer (0 or 1)
- "has_roundA": integer (0 or 1)
- "has_roundB": integer (0 or 1)
- "has_roundC": integer (0 or 1)
- "has_roundD": integer (0 or 1)
- "avg_participants": float (average investors per round, e.g. 2.0)
- "is_top500": integer (0 or 1)
- "founded_year": integer (e.g. 2024)
- "first_funding_year": integer (e.g. 2025)
- "last_funding_year": integer (e.g. 2026)
- "years_to_first_funding": float (first_funding_year - founded_year)
- "funding_period_years": float (last_funding_year - first_funding_year)

{context}

Return strictly valid raw JSON. No markdown backticks, no conversational text.
"""
    config = types.GenerateContentConfig(
        temperature=0.2,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    for model_name in PRIMARY_MODELS:
        # Keep the interactive path responsive: one retry for a temporary
        # overload, then move to the next compatible model or safe fallback.
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                raw = response.text.strip()
                if raw.startswith("```"):
                    raw = raw.replace("```json", "").replace("```", "").strip()
                inferred = json.loads(raw)

                if inferred.get("category_code") not in VALID_CATEGORIES:
                    inferred["category_code"] = "software"

                fallback = _get_fallback_features()
                for key in FEATURES:
                    if key not in inferred:
                        inferred[key] = fallback[key]

                return inferred
            except ServerError:
                if attempt == 0:
                    time.sleep(1.0)
            except ClientError:
                break
            except Exception:
                if attempt == 0:
                    time.sleep(0.5)

    return _get_fallback_features()
