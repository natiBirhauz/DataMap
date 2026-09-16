# main.py
import os
import json
import re
import urllib.request
import urllib.error
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

# --- Setup and Initialization ---
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

# Check available Free Tier API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if GEMINI_API_KEY:
    print("[OK] Google Gemini API key loaded (Primary Free Tier).")
if GROQ_API_KEY:
    print("[OK] Groq API key loaded (High-speed Free Tier).")
if OPENROUTER_API_KEY:
    print("[OK] OpenRouter API key loaded (Multi-model Free Tier).")
if not (GEMINI_API_KEY or GROQ_API_KEY or OPENROUTER_API_KEY):
    print("[WARN] No Free Tier API key configured! Please set GEMINI_API_KEY in Render Environment Variables.")


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
def call_gemini(query: str) -> tuple[Optional[str], Optional[str]]:
    gemini_key = GEMINI_API_KEY
    if not gemini_key:
        return None, "GEMINI_API_KEY is not set"

    import time
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
    last_err = None
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
                                return text, None
            except urllib.error.HTTPError as e:
                try:
                    err_json = json.loads(e.read().decode("utf-8"))
                    last_err = err_json.get("error", {}).get("message", str(e))
                except Exception:
                    last_err = f"HTTP Error {e.code}: {e.reason}"
                print(f"[WARN] Gemini ({model}) attempt {attempt + 1} error: {last_err}")
                if attempt == 0 and e.code == 503:
                    time.sleep(1.5)
                    continue
                break
            except Exception as e:
                last_err = str(e)
                print(f"[WARN] Gemini ({model}) attempt {attempt + 1} error: {last_err}")
                break
    return None, last_err


# --- Tier 2: Groq Free Tier ---
def call_groq(query: str) -> tuple[Optional[str], Optional[str]]:
    groq_key = GROQ_API_KEY
    if not groq_key:
        return None, "GROQ_API_KEY is not set"

    prompt = build_system_prompt(query)
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    last_err = None

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
                    return msg, None
        except urllib.error.HTTPError as e:
            try:
                err_json = json.loads(e.read().decode("utf-8"))
                last_err = err_json.get("error", {}).get("message", str(e))
            except Exception:
                last_err = f"HTTP Error {e.code}: {e.reason}"
            print(f"[WARN] Groq ({model}) error: {last_err}")
            continue
        except Exception as e:
            last_err = str(e)
            print(f"[WARN] Groq ({model}) error: {last_err}")
            continue
    return None, last_err


# --- Tier 3: OpenRouter Free Tier ---
def call_openrouter(query: str) -> tuple[Optional[str], Optional[str]]:
    or_key = OPENROUTER_API_KEY
    if not or_key:
        return None, "OPENROUTER_API_KEY is not set"

    prompt = build_system_prompt(query)
    models = ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.2-3b-instruct:free"]
    last_err = None

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
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {or_key}"
            },
            method="POST"
        )
        try:
            print(f"--- Calling OpenRouter ({model}) [Free Tier] ---")
            with urllib.request.urlopen(req, timeout=25) as response:
                payload = json.loads(response.read().decode("utf-8"))
                msg = payload.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if msg:
                    print(f"[OK] OpenRouter ({model}) responded successfully.")
                    return msg, None
        except urllib.error.HTTPError as e:
            try:
                err_json = json.loads(e.read().decode("utf-8"))
                last_err = err_json.get("error", {}).get("message", str(e))
            except Exception:
                last_err = f"HTTP Error {e.code}: {e.reason}"
            print(f"[WARN] OpenRouter ({model}) error: {last_err}")
            continue
        except Exception as e:
            last_err = str(e)
            print(f"[WARN] OpenRouter ({model}) error: {last_err}")
            continue
    return None, last_err


# --- Unified Multi-Tier Dispatcher ---
def query_free_llm(query: str) -> tuple[Optional[dict], Optional[str]]:
    """Dispatches query through Free Tier LLMs (Gemini -> Groq -> OpenRouter)."""
    raw_response = None
    last_err = None

    if GEMINI_API_KEY:
        raw_response, last_err = call_gemini(query)

    if not raw_response and GROQ_API_KEY:
        raw_response, last_err = call_groq(query)

    if not raw_response and OPENROUTER_API_KEY:
        raw_response, last_err = call_openrouter(query)

    if not (GEMINI_API_KEY or GROQ_API_KEY or OPENROUTER_API_KEY):
        return None, "No LLM API key configured on Render. Please add GEMINI_API_KEY in Render Dashboard -> Environment."

    if raw_response:
        try:
            cleaned = re.sub(r'^```json\s*', '', raw_response.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r'```$', '', cleaned.strip(), flags=re.MULTILINE)
            parsed = json.loads(cleaned)
            validated = AIResponse(**parsed)
            return validated.model_dump(), None
        except Exception as e:
            print(f"[WARN] Failed to parse LLM JSON: {e}")
            return None, f"Failed to parse LLM response: {e}"

    return None, last_err


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
            "groq_free_tier": bool(GROQ_API_KEY),
            "openrouter_free_tier": bool(OPENROUTER_API_KEY)
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

    # 1. Try LLM if any API key is configured
    if GEMINI_API_KEY or GROQ_API_KEY or OPENROUTER_API_KEY:
        try:
            result, error_reason = query_free_llm(q)
            if result:
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
                if final_response:
                    print(f"[OK] Returning {len(final_response)} country data points from LLM.")
                    return final_response
            print(f"[INFO] LLM unavailable ({error_reason}). Falling back to Free World Data Engine.")
        except Exception as e:
            print(f"[WARN] LLM exception: {e}. Falling back to Free World Data Engine.")

    # 2. Free World Data Engine (Zero API Keys required, instant & authentic data)
    from dataset_catalog import search_world_data
    data = search_world_data(q)
    if data:
        print(f"[OK] Returning {len(data)} country data points from Free World Data Engine.")
        return data

    raise HTTPException(
        status_code=500,
        detail="Unable to process search. Please try rephrasing your topic."
    )