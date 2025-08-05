# main.py
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("🚨 FATAL: OPENAI_API_KEY environment variable is not set.")
    raise SystemExit("FATAL ERROR: OPENAI_API_KEY environment variable not found.")
else:
    print("✅ OpenAI API key loaded successfully.")

client = OpenAI(api_key=api_key)


# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str

class CountryData(BaseModel):
    country_code: str
    value: Optional[float]
    label: str


# --- Country Codes ---
# This list is fine, no changes needed here.
COUNTRY_CODES = { 'Afghanistan': 'AFG', 'Angola': 'AGO', 'Albania': 'ALB', 'United Arab Emirates': 'ARE', 'Argentina': 'ARG', 'Armenia': 'ARM', 'Australia': 'AUS', 'Austria': 'AUT', 'Azerbaijan': 'AZE', 'Belgium': 'BEL', 'Burkina Faso': 'BFA', 'Bangladesh': 'BGD', 'Bulgaria': 'BGR', 'Bosnia and Herzegovina': 'BIH', 'Belarus': 'BLR', 'Bolivia': 'BOL', 'Brazil': 'BRA', 'Canada': 'CAN', 'Switzerland': 'CHE', 'Chile': 'CHL', 'China': 'CHN', 'Cameroon': 'CMR', 'DR Congo': 'COD', 'Colombia': 'COL', 'Cuba': 'CUB', 'Germany': 'DEU', 'Denmark': 'DNK', 'Algeria': 'DZA', 'Ecuador': 'ECU', 'Egypt': 'EGY', 'Spain': 'ESP', 'Ethiopia': 'ETH', 'Finland': 'FIN', 'France': 'FRA', 'United Kingdom': 'GBR', 'Greece': 'GRC', 'Guatemala': 'GTM', 'Hungary': 'HUN', 'Indonesia': 'IDN', 'India': 'IND', 'Ireland': 'IRL', 'Iran': 'IRN', 'Iraq': 'IRQ', 'Iceland': 'ISL', 'Israel': 'ISR', 'Italy': 'ITA', 'Japan': 'JPN', 'Kenya': 'KEN', 'South Korea': 'KOR', 'Lebanon': 'LBN', 'Libya': 'LBY', 'Morocco': 'MAR', 'Mexico': 'MEX', 'Mali': 'MLI', 'Mongolia': 'MNG', 'Malaysia': 'MYS', 'Nigeria': 'NGA', 'Netherlands': 'NLD', 'Norway': 'NOR', 'New Zealand': 'NZL', 'Peru': 'PER', 'Philippines': 'PHL', 'Pakistan': 'PAK', 'Poland': 'POL', 'Portugal': 'PRT', 'Qatar': 'QAT', 'Romania': 'ROU', 'Russia': 'RUS', 'Saudi Arabia': 'SAU', 'Sudan': 'SDN', 'Sweden': 'SWE', 'Syria': 'SYR', 'Thailand': 'THA', 'Turkey': 'TUR', 'Ukraine': 'UKR', 'United States': 'USA', 'Venezuela': 'VEN', 'Vietnam': 'VNM', 'South Africa': 'ZAF', 'Zambia': 'ZMB', 'Zimbabwe': 'ZWE' }


# --- FastAPI Application Setup ---
# Your new, improved setup is integrated here.
app = FastAPI(
    title="DATAMAP",
    version="1.1",
    description="The best MAP DATA VISUALIZER"
)

# This wildcard CORS configuration is the key to fixing the error.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/api/query/", response_model=List[CountryData])
async def handle_query(req: QueryRequest):
    print(f"[INFO] Received query: '{req.query}'")
    # The rest of your handle_query function remains the same...
    prompt = f"""You are a world-class data scientist AI building a dataset for a global choropleth map. Your PRIMARY GOAL is to generate a comprehensive global dataset. The user's query is: "{req.query}". You must provide a response ONLY in a valid JSON object format with two keys: "label" and "data". "label" should be a short descriptive title. "data" should be a JSON list of objects, one for each country. For each country object, include "country_code" (the EXACT 3-letter ISO code) and "value" (your numeric estimate). Your response MUST include a large number of countries (at least 150 for broad topics) to cover the world map. Here are the valid country codes: {json.dumps(list(COUNTRY_CODES.values()))}"""
    try:
        response = client.chat.completions.create(model="gpt-4o", response_format={"type": "json_object"}, messages=[{"role": "system", "content": "You are a helpful data analysis AI that only responds with JSON for a world map."}, {"role": "user", "content": prompt}], temperature=0.2)
        response_content = response.choices[0].message.content
        ai_data = json.loads(response_content)
        final_response = [{"country_code": item.get("country_code"), "value": item.get("value"), "label": ai_data.get("label", "Estimated Value")} for item in ai_data.get("data", []) if item.get("country_code") in COUNTRY_CODES.values()]
        if not final_response: raise HTTPException(status_code=404, detail="The AI could not generate data for your query.")
        return final_response
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")