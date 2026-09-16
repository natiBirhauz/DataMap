# api/index.py for Vercel Serverless Functions
import os
import json
import re
import urllib.request
import urllib.error
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Try to load local .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", ".env"))
except ImportError:
    pass

# Check available Free Tier API keys
DEFAULT_GEMINI_KEY = "AIzaSyBvp6NjTLuijuotTwNqc8gAw0QNAI6tIaA"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or DEFAULT_GEMINI_KEY
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Country Codes ---
COUNTRY_CODES_SET = {
    'AFG', 'AGO', 'ALB', 'ARE', 'ARG', 'ARM', 'AUS', 'AUT', 'AZE', 'BEL',
    'BFA', 'BGD', 'BGR', 'BIH', 'BLR', 'BOL', 'BRA', 'CAN', 'CHE', 'CHL',
    'CHN', 'CMR', 'COD', 'COL', 'CUB', 'DEU', 'DNK', 'DZA', 'ECU', 'EGY',
    'ESP', 'ETH', 'FIN', 'FRA', 'GBR', 'GRC', 'GTM', 'HUN', 'IDN', 'IND',
    'IRL', 'IRN', 'IRQ', 'ISL', 'ISR', 'ITA', 'JPN', 'KEN', 'KOR', 'LBN',
    'LBY', 'MAR', 'MEX', 'MLI', 'MNG', 'MYS', 'NGA', 'NLD', 'NOR', 'NZL',
    'PER', 'PHL', 'PAK', 'POL', 'PRT', 'QAT', 'ROU', 'RUS', 'SAU', 'SDN',
    'SWE', 'SYR', 'THA', 'TUR', 'UKR', 'USA', 'VEN', 'VNM', 'ZAF', 'ZMB', 'ZWE'
}


# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None

class CountryData(BaseModel):
    country_code: str
    value: Optional[float]

class AIResponse(BaseModel):
    label: str
    data: List[CountryData]


# --- Prompt Builder ---
def build_system_prompt(q: str) -> str:
    return (
        f'You are a world-class data scientist AI building a dataset for a global choropleth map. '
        f'The user\'s query is: "{q}". '
        f'You must provide a response ONLY as a valid JSON object with exactly two keys: "label" and "data". '
        f'"label" must be a concise, professional title for the dataset. '
        f'"data" must be a JSON list of objects, one for each country, with "country_code" (exact 3-letter ISO code) and "value" (numeric estimate). '
        f'Include as many countries as possible (at least 60-80) to cover the world map accurately with realistic, factual data. '
        f'Valid ISO country codes include: {json.dumps(list(COUNTRY_CODES_SET))}'
    )


# --- Tier 1: Google Gemini Free Tier ---
def call_gemini(query: str) -> Optional[str]:
    gemini_key = GEMINI_API_KEY
    if not gemini_key:
        return None

    prompt = build_system_prompt(query)
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json"
        }
    }

    # Verified working models in order of capability and availability
    models = ["gemini-2.5-flash", "gemini-flash-lite-latest", "gemini-3.5-flash"]
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        for attempt in range(2):
            try:
                print(f"--- Calling Google Gemini ({model}, attempt {attempt + 1}) [Free Tier] ---")
                with urllib.request.urlopen(req, timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    candidates = payload.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text", "").strip()
                            if text:
                                print(f"[OK] Google Gemini ({model}) responded successfully.")
                                return text
            except Exception as e:
                print(f"[WARN] Gemini ({model}) attempt {attempt + 1} error: {e}")
                if attempt == 0 and "503" in str(e):
                    time.sleep(1.5)
                    continue
                break
    return None


# --- Tier 2: Groq Free Tier ---
def call_groq(query: str) -> Optional[str]:
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return None

    prompt = build_system_prompt(query)
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    for model in models:
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a data analysis AI that only returns valid JSON for world choropleth maps."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {groq_key}"
            },
            method="POST"
        )
        try:
            print(f"--- Calling Groq ({model}) [Free Tier] ---")
            with urllib.request.urlopen(req, timeout=25) as response:
                payload = json.loads(response.read().decode("utf-8"))
                msg = payload.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if msg:
                    print(f"[OK] Groq ({model}) responded successfully.")
                    return msg
        except Exception as e:
            print(f"[WARN] Groq ({model}) error: {e}")
            continue
    return None


# --- Unified Multi-Tier Dispatcher ---
def query_free_llm(query: str) -> Optional[dict]:
    """Dispatches query through Free Tier LLMs (Gemini -> Groq). Returns validated real data or None."""
    # Tier 1: Google Gemini (Free Tier)
    raw_response = call_gemini(query)

    # Tier 2: Groq (Free Tier)
    if not raw_response:
        raw_response = call_groq(query)

    # Parse and validate response
    if raw_response:
        try:
            cleaned = re.sub(r'^```json\s*', '', raw_response.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r'```$', '', cleaned.strip(), flags=re.MULTILINE)
            parsed = json.loads(cleaned)
            validated = AIResponse(**parsed)
            return validated.model_dump()
        except Exception as e:
            print(f"[WARN] Failed to parse LLM JSON: {e}")

    return None


# --- FastAPI Application ---
app = FastAPI(
    title="DataMap API",
    version="2.0",
    description="The Best Free World Map Data Visualizer — Powered by Free-to-Use LLMs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/api/query/")
@app.options("/api/query")
@app.options("/query/")
@app.options("/query")
@app.options("/")
async def options_query(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "version": app.version,
        "llm_providers": {
            "gemini_free_tier": bool(GEMINI_API_KEY),
            "groq_free_tier": bool(GROQ_API_KEY)
        }
    }

@app.post("/api/query/")
@app.post("/api/query")
@app.post("/query/")
@app.post("/query")
@app.post("/")
async def handle_query(req: QueryRequest):
    q = (req.query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    print(f"\n--- Processing Query: '{q}' ---")
    result = query_free_llm(q)

    if not result:
        raise HTTPException(
            status_code=502,
            detail="AI data engine was unable to generate a dataset for this query. Please check connectivity or try a different topic."
        )

    label = result.get("label", q.capitalize())
    items = result.get("data", [])

    final_response = [
        {
            "country_code": item.get("country_code"),
            "value": item.get("value"),
            "label": label
        }
        for item in items
        if item.get("country_code") in COUNTRY_CODES_SET and item.get("value") is not None
    ]

    if not final_response:
        raise HTTPException(
            status_code=502,
            detail="No valid country data points could be parsed from the AI response. Please try rephrasing your query."
        )

    print(f"[OK] Returning {len(final_response)} real country data points for '{label}'.")
    return final_response
