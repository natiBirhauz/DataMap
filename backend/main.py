# main.py
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# --- Setup and Initialization ---
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Critical check on application startup
if not api_key:
    # This will crash the server on startup if the key is missing, which is what we want.
    raise SystemExit("🚨 FATAL ERROR: OPENAI_API_KEY environment variable not found. The application cannot start.")
else:
    print("✅ OpenAI API key loaded successfully.")

client = OpenAI(api_key=api_key)


# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str

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

@app.get("/")
def read_root():
    return {"status": "ok", "version": app.version}


@app.post("/api/query/") # Note the trailing slash
async def handle_query(req: QueryRequest):
    q = req.query
    print("\n--- 1. NEW REQUEST RECEIVED ---")

    # The preliminary check for the key is already done on startup,
    # which is the best practice. The server wouldn't be running if it was missing.

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
        print(f"--- CRITICAL ERROR during OpenAI API call: {type(e).__name__} - {e} ---")
        # Check for specific OpenAI error codes like quota issues
        if "insufficient_quota" in str(e) or (hasattr(e, 'status_code') and e.status_code == 429):
             raise HTTPException(status_code=429, detail="OpenAI API quota exceeded. Please check your billing.")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred with the OpenAI API: {str(e)}")

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