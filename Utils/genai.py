import os
import json
import time
from functools import lru_cache
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

load_dotenv()

# =========================================================
# CONFIGURATION & SUPPORTED MODEL IDENTIFIERS
# =========================================================

PRIMARY_MODELS = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
]

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = genai.Client(api_key=API_KEY)


@lru_cache(maxsize=128)
def call_gemini_with_fallback(prompt: str) -> str:
    """
    Executes generate_content across valid model candidates with retry
    backoff to gracefully withstand 503 high-demand bursts.
    """
    config = types.GenerateContentConfig(
        temperature=0.3,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    last_error = None

    for model_name in PRIMARY_MODELS:
        # A long retry chain makes the UI feel frozen. Try each candidate once,
        # then retry it once after a short delay only for temporary overload.
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                if response and response.text:
                    return response.text.strip()
            except ServerError as e:
                # 503 temporary high demand - wait and retry
                last_error = e
                if attempt == 0:
                    time.sleep(1.0)
            except ClientError as e:
                # 404 or unsupported - skip immediately to next model
                last_error = e
                break
            except Exception as e:
                last_error = e
                if attempt == 0:
                    time.sleep(0.5)

    raise RuntimeError(f"All Gemini model candidates failed. Last error: {last_error}")


def format_failure_results(failure_results):
    if not failure_results:
        return "No similar historical startup failures were found."

    text = ""
    for i, result in enumerate(failure_results, start=1):
        details = result.get("details", {})
        startup_name = result.get("startup_name", "Unknown Startup")
        similarity = result.get("similarity_percentage", 0)
        dimension = details.get("dimension", "Not specified")
        description = details.get("description", "Not available")
        failure_reason = details.get("failure_reason", "Not available")

        text += f"""
Historical Failure {i}:
- Startup: {startup_name}
- Match: {similarity}%
- Primary Risk Dimension: {dimension}
- Profile: {description}
- Root Cause of Failure: {failure_reason}
"""
    return text


def format_indian_startups(indian_startups):
    if not indian_startups:
        return "No similar Indian startups were found."

    text = ""
    for i, result in enumerate(indian_startups, start=1):
        details = result.get("details", {})
        startup_name = result.get("startup_name", "Unknown Startup")
        similarity = result.get("similarity_percentage", 0)
        location = details.get("field_2", "Not available")
        founders = details.get("field_3", "Not available")
        industry = details.get("field_4", "Not available")
        description = details.get("field_5", "Not available")
        employees = details.get("field_6", "Not available")

        text += f"""
Active Ecosystem Precedent {i}:
- Startup: {startup_name}
- Match: {similarity}%
- Location: {location}
- Founders: {founders}
- Industry: {industry}
- Overview: {description}
- Team Size: {employees}
"""
    return text


def generate_concept_and_risks(startup_description, prediction_result, failure_results, indian_startups):
    """
    Phase 1 Output:
    - Enhanced concept description
    - Core problem identification & target users
    - Synthesized major risk factors (internally derived, without raw database dumps)
    """
    failures_summary = [
        f"{f.get('startup_name')}: {f.get('details', {}).get('failure_reason')} (Dimension: {f.get('details', {}).get('dimension')})"
        for f in (failure_results or [])[:5]
    ]
    competitor_summary = [
        f"{c.get('startup_name')} ({c.get('details', {}).get('field_2', 'India')}): {c.get('details', {}).get('field_5', '')}"
        for c in (indian_startups or [])[:4]
    ]

    prompt = f"""
You are an elite startup mentor and venture evaluator.
Analyze the user's venture idea below in light of comparative failure cases and active ecosystem precedents.

USER'S ORIGINAL IDEA:
{startup_description}

INTERNAL EVIDENCE (DO NOT list these raw records; synthesize insights from them):
- Past Failures in this domain: {failures_summary}
- Active Competitors in the ecosystem: {competitor_summary}
- ML Prediction Model Result: {prediction_result.get('status')} ({prediction_result.get('success_probability')}% success)

TASK:
Return a JSON object with this exact structure:
{{
  "enhanced_description": "A polished, compelling 2-3 sentence description defining the product mechanism, value proposition, and innovation angle.",
  "problems_identified": [
    "Specific problem 1 addressed",
    "Specific problem 2 addressed",
    "Specific problem 3 addressed"
  ],
  "target_users": [
    "Target user persona 1",
    "Target user persona 2",
    "Target user persona 3"
  ],
  "major_risks": [
    {{
      "title": "Risk Category Name (e.g. Differentiation, Platform Leakage, Unit Economics, or Competition)",
      "explanation": "Concrete explanation synthesized from the failure/competitor patterns of why this venture is vulnerable and how to prevent it."
    }},
    {{
      "title": "Second Major Risk Category",
      "explanation": "Concrete explanation..."
    }},
    {{
      "title": "Third Major Risk Category",
      "explanation": "Concrete explanation..."
    }}
  ]
}}

Return strictly raw JSON. No markdown backticks or conversational text.
"""
    raw = call_gemini_with_fallback(prompt)
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def generate_detailed_plan(startup_description, prediction_result, failure_results, indian_startups):
    """
    Phase 2 Deep Dive (If user clicks 'Yes, Explore Further'):
    - Recommended Roadmap
    - Required Technical & Business Skills table
    - Recommended Team roles and counts
    - Recommended Improvements table
    - Mermaid Flowchart
    """
    failures_summary = [f.get('details', {}).get('failure_reason') for f in (failure_results or [])[:4]]
    competitors = [c.get('startup_name') for c in (indian_startups or [])[:4]]

    prompt = f"""
You are an elite startup incubator director and product strategist.
The user wants to explore and build their venture idea in depth.

VENTURE CONCEPT:
{startup_description}
ML Prediction: {prediction_result.get('status')} ({prediction_result.get('success_probability')}% viability)
Known Market Pitfalls: {failures_summary}
Known Competitors: {competitors}

Generate a comprehensive implementation strategy in JSON format with these exact keys:
{{
  "roadmap_stages": [
    {{"phase": "Phase 1: Idea Validation", "details": "Specific actions to validate customer demand without coding."}},
    {{"phase": "Phase 2: MVP Development", "details": "Core features to launch in the leanest product."}},
    {{"phase": "Phase 3: Initial User Acquisition", "details": "First 100-1000 users acquisition channel strategy."}},
    {{"phase": "Phase 4: Product & Unit Economics Optimization", "details": "Retention loops and margin adjustments."}},
    {{"phase": "Phase 5: Scaling & Defensibility", "details": "Building a defensible moat against competitors."}}
  ],
  "required_skills": [
    {{"skill": "Skill name (e.g. Python & FastAPI, React Native, etc.)", "purpose": "Clear explanation of why it is needed."}},
    {{"skill": "Skill name 2", "purpose": "Why needed..."}},
    {{"skill": "Skill name 3", "purpose": "Why needed..."}},
    {{"skill": "Skill name 4", "purpose": "Why needed..."}},
    {{"skill": "Skill name 5", "purpose": "Why needed..."}}
  ],
  "recommended_team": [
    {{"role": "Role title (e.g. Full-Stack Lead)", "count": 1, "description": "Core responsibilities."}},
    {{"role": "Role title 2", "count": 1, "description": "Core responsibilities."}},
    {{"role": "Role title 3", "count": 1, "description": "Core responsibilities."}},
    {{"role": "Role title 4", "count": 1, "description": "Core responsibilities."}}
  ],
  "improvements": [
    {{"current": "Aspect of basic concept", "suggested": "Upgraded mechanism", "rationale": "Why this change makes the startup dramatically more viable."}},
    {{"current": "Aspect 2", "suggested": "Upgraded mechanism 2", "rationale": "Why it matters..."}},
    {{"current": "Aspect 3", "suggested": "Upgraded mechanism 3", "rationale": "Why it matters..."}},
    {{"current": "Aspect 4", "suggested": "Upgraded mechanism 4", "rationale": "Why it matters..."}}
  ],
  "flowchart": "graph TD\\n  A[Idea Concept] --> B{{Problem Validated?}}\\n  B -- Yes --> C[Build MVP]\\n  B -- No --> D[Pivot Thesis]\\n  C --> E{{Positive Retention?}}\\n  E -- Yes --> F[Scale GTM]\\n  E -- No --> G[Iterate Offer]"
}}

Return strictly valid raw JSON.
"""
    raw = call_gemini_with_fallback(prompt)
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def generate_validation_report(
    startup_description,
    prediction_result,
    failure_results=None,
    indian_startups=None
):
    if not startup_description:
        raise ValueError("Startup description cannot be empty.")

    if prediction_result is None:
        raise ValueError("Prediction result is required.")

    failure_results = failure_results or []
    indian_startups = indian_startups or []

    status = prediction_result.get("status", "Unknown")
    success_probability = prediction_result.get("success_probability", 0)
    failure_probability = prediction_result.get("failure_probability", 0)
    inferred_features = prediction_result.get("features_inferred", {})

    historical_failures = format_failure_results(failure_results)
    indian_startup_data = format_indian_startups(indian_startups)

    prompt = f"""
You are an executive startup validator and investment risk analyst.
Evaluate this venture thesis using ONLY the provided inputs and evidence.

====================================================
VENTURE THESIS
====================================================
{startup_description}

====================================================
RANDOM FOREST PREDICTION METRICS
====================================================
Predicted Status: {status}
Success Probability: {success_probability}%
Failure Risk: {failure_probability}%

Inferred Tabular Features:
- Primary Category: {inferred_features.get('category_code', 'N/A')}
- Estimated Capital: ${inferred_features.get('funding_total_usd', 'N/A')}
- Expected Funding Rounds: {inferred_features.get('funding_rounds', 'N/A')}
- Projected Milestones: {inferred_features.get('milestones', 'N/A')}

====================================================
SIMILAR HISTORICAL STARTUP FAILURES
====================================================
{historical_failures}

====================================================
SIMILAR ACTIVE INDIAN VENTURES
====================================================
{indian_startup_data}

====================================================
REPORT INSTRUCTIONS
====================================================
Write a rigorous, executive-level validation brief. 
Format using clean Markdown with bold headers:

## 1. Executive Assessment
Concise verdict on the viability, novelty, and execution barrier of the thesis.

## 2. Venture Thesis Decomposition
Break down:
- Core Problem Identified
- Proposed Solution Mechanics
- Target User Profile & Monetization Thesis

## 3. Machine Learning Viability Assessment
Interpret the {success_probability}% success probability vs. {failure_probability}% failure risk.
Clarify that this reflects historical training patterns of tech startup survivability from the Random Forest model.

## 4. Historical Failure Post-Mortem & Risk Dimensions
Directly reference the retrieved failure cases.
Detail what structural pitfalls (e.g. CAC/LTV, logistics overhead, competition) must be avoided.

## 5. Ecosystem Competitive Benchmarking
Compare the idea against the retrieved active startup precedents.
Explain how the venture can differentiate and build defensibility (moat).

## 6. Key Strengths (3-5 Bullet Points)

## 7. Critical Vulnerabilities & Threat Matrix (Ranked by severity)

## 8. 5-Stage Execution Roadmap
- Stage 1: Problem/Customer Validation
- Stage 2: Minimum Viable Product (MVP)
- Stage 3: Initial Traction & Cohort Retention
- Stage 4: Unit Economics Optimization
- Stage 5: Scaling & Defensive Moat

## 9. Final Investment Verdict
State one of:
- **HIGH POTENTIAL**
- **PROMISING BUT NEEDS VALIDATION**
- **MODERATE RISK**
- **HIGH RISK**
Include a definitive 2-3 sentence concluding rationale.
"""

    return call_gemini_with_fallback(prompt)


def generate_strategy_flowchart(
    startup_description,
    prediction_result,
    failure_results=None,
    indian_startups=None
):
    failure_results = failure_results or []
    indian_startups = indian_startups or []

    top_failure = failure_results[0].get("startup_name", "Historical Failure") if failure_results else "Execution Risk"
    top_competitor = indian_startups[0].get("startup_name", "Market Competitors") if indian_startups else "Incumbents"

    prompt = f"""
You are a startup systems architect.
Construct an actionable, valid Mermaid.js flowchart (graph TD) mapping the validation gates, execution milestones, and risk checkpoints for this startup.

Venture:
{startup_description}

Model Status: {prediction_result.get('status')} ({prediction_result.get('success_probability')}%)
Primary Historical Risk Case: Avoid pitfalls of {top_failure}
Primary Competitor to Outposition: {top_competitor}

Rules:
1. Start directly with ```mermaid
2. Use valid graph TD syntax.
3. Include decision gates with diamond braces: Node{{Decision?}}
4. Include concrete steps: Problem Discovery -> MVP -> Unit Economics Test -> Competitor Moat -> Scaling.
5. Close directly with ```
6. Do not include conversational markdown before or after.
"""
    try:
        raw = call_gemini_with_fallback(prompt)
        if "```mermaid" not in raw:
            raw = f"```mermaid\n{raw}\n```"
        return raw
    except Exception:
        return """```mermaid
graph TD
    A[Venture Concept] --> B{Problem-Solution Fit?}
    B -- No --> C[Pivot Customer Thesis]
    B -- Yes --> D[Build Lean MVP]
    D --> E{Unit Economics Viable?}
    E -- Negative Margins --> F[Restructure Cost & Pricing]
    E -- Positive LTV/CAC --> G[Outposition Competitors]
    G --> H[Sustainable Scale & Moat]
```"""
