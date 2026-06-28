# main.py
import os
import json
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# --- Setup and Initialization ---
load_dotenv()
SERVER_API_KEY = os.getenv("OPENAI_API_KEY")

if SERVER_API_KEY:
    print("✅ Server-level OpenAI API key loaded (used as fallback).")
else:
    print("⚠️  No server-level OPENAI_API_KEY found. Users must supply their own key.")


# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str
    api_key: Optional[str] = None  # User-supplied OpenAI key (takes priority over server key)

class CountryData(BaseModel):
    country_code: str
    value: Optional[float]

# This is the model that the AI is expected to return
class AIResponse(BaseModel):
    label: str
    data: List[CountryData]


# --- Country Codes ---
COUNTRY_CODES_SET = {'AFG', 'AGO', 'ALB', 'ARE', 'ARG', 'ARM', 'AUS', 'AUT', 'AZE', 'BEL', 'BFA', 'BGD', 'BGR', 'BIH', 'BLR', 'BOL', 'BRA', 'CAN', 'CHE', 'CHL', 'CHN', 'CMR', 'COD', 'COL', 'CUB', 'DEU', 'DNK', 'DZA', 'ECU', 'EGY', 'ESP', 'ETH', 'FIN', 'FRA', 'GBR', 'GRC', 'GTM', 'HUN', 'IDN', 'IND', 'IRL', 'IRN', 'IRQ', 'ISL', 'ISR', 'ITA', 'JPN', 'KEN', 'KOR', 'LBN', 'LBY', 'MAR', 'MEX', 'MLI', 'MNG', 'MYS', 'NGA', 'NLD', 'NOR', 'NZL', 'PER', 'PHL', 'PAK', 'POL', 'PRT', 'QAT', 'ROU', 'RUS', 'SAU', 'SDN', 'SWE', 'SYR', 'THA', 'TUR', 'UKR', 'USA', 'VEN', 'VNM', 'ZAF', 'ZMB', 'ZWE'}


# --- FastAPI Application ---
app = FastAPI(
    title="DataMap API",
    version="1.2",
    description="The best MAP DATA VISUALIZER - now with enhanced logging"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicit CORS headers for preflight
@app.options("/api/query/")
async def options_query(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"status": "ok", "version": app.version}


@app.post("/api/query/") # Note the trailing slash
async def handle_query(req: QueryRequest):
    q = req.query
    print("\n--- 1. NEW REQUEST RECEIVED ---")

    # Resolve which API key to use: user-supplied takes priority over server key
    resolved_key = (req.api_key or "").strip() or SERVER_API_KEY
    if not resolved_key:
        raise HTTPException(
            status_code=400,
            detail="No OpenAI API key provided. Please add your API key in the settings."
        )

    client = OpenAI(api_key=resolved_key)
    key_source = "user-supplied" if (req.api_key or "").strip() else "server"
    print(f"--- Using {key_source} OpenAI API key ---")

    print(f"--- 2. Query received: '{q}' ---")

    # Define the system prompt for the AI
    SYSTEM_PROMPT = f"""You are a world-class data scientist AI building a dataset for a global choropleth map. Your PRIMARY GOAL is to generate a comprehensive global dataset, NOT just a "top 10" list. The user's query is: "{q}". You must provide a response ONLY in a valid JSON object format with two keys: "label" and "data". "label" should be a short descriptive title. "data" should be a JSON list of objects, one for each country. For each country object, include "country_code" (the EXACT 3-letter ISO code) and "value" (your numeric estimate). Your response MUST include a large number of countries (at least 150 for broad topics) to cover the world map. Here are the valid country codes: {json.dumps(list(COUNTRY_CODES_SET))}"""

    try:
        print("--- 3. Preparing to call OpenAI API... ---")
        chat = client.chat.completions.create(
            model="gpt-4o-mini", # Using the more cost-effective model
            messages=[
                {"role": "system", "content": "You are a helpful data analysis AI that only responds with a valid JSON object designed to populate a world map."},
                {"role": "user", "content": SYSTEM_PROMPT} # Pass the full context as user content
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        print("--- 4. OpenAI API call FINISHED successfully. ---")
        response_content = chat.choices[0].message.content

    except Exception as e:
        error_str = str(e)
        print(f"--- CRITICAL ERROR during OpenAI API call: {type(e).__name__} - {error_str} ---")

        status_code = getattr(e, 'status_code', None)

        if status_code == 401 or "invalid_api_key" in error_str or "Incorrect API key" in error_str:
            raise HTTPException(status_code=401, detail="Invalid API key. Please check your OpenAI API key and try again.")
        if status_code == 429 or "insufficient_quota" in error_str or "quota" in error_str.lower():
            raise HTTPException(status_code=429, detail="OpenAI quota exceeded. Your API key has no credits — add billing at platform.openai.com.")
        if status_code == 403 or "permission" in error_str.lower():
            raise HTTPException(status_code=403, detail="API key does not have permission to use this model. Check your OpenAI plan.")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {error_str}")

    print("--- 5. RAW OPENAI RESPONSE ---")
    print(response_content)
    print("----------------------------")

    try:
        print("--- 6. Attempting to parse and validate JSON... ---")
        # The AI should return an object with 'label' and 'data' keys
        ai_response_obj = json.loads(response_content)
        
        # We use our Pydantic model to validate the structure
        validated_data = AIResponse(**ai_response_obj)

        # Prepare the final response for the frontend (as a list of CountryData)
        final_response = [
            {
                "country_code": item.country_code,
                "value": item.value,
                "label": validated_data.label
            }
            for item in validated_data.data if item.country_code in COUNTRY_CODES_SET
        ]
        
        print("--- 7. JSON parsed and validated successfully! Returning data. ---")
        return final_response
    
    except ValidationError as e:
        print(f"--- ERROR: Pydantic validation failed. The AI's response structure is incorrect. ---")
        print(f"Details: {e.errors()}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "The AI response structure does not match the expected format.",
                "validation_errors": e.errors(),
                "raw_response": response_content
            }
        )
    except Exception as e:
        print(f"--- ERROR: Failed to process response. Type: {type(e).__name__}, Details: {e} ---")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "An unexpected error occurred while processing the AI's response.",
                "raw_response": response_content
            }
        )