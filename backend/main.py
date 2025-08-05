# main.py
import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# --- Use the new, recommended way to instantiate the OpenAI client ---
from openai import OpenAI

# 1. LOAD ENVIRONMENT and VERIFY API KEY
load_dotenv()

# --- THIS IS THE CORRECTED LINE ---
# It now looks for the VARIABLE NAME, not the value.
api_key = os.getenv("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") 

if not api_key:
    print("FATAL ERROR: OPENAI_API_KEY variable not found.")
    # In a real app, you would want to stop the server here.
else:
    print("OpenAI API Key loaded successfully from environment variable.")

client = OpenAI(api_key=api_key)


# --- Pydantic Models (Data Structures) ---
class QueryRequest(BaseModel):
    query: str

class CountryData(BaseModel):
    country_code: str
    value: Optional[float]
    label: str # The frontend needs this in each item


# --- VASTLY EXPANDED COUNTRY CODE LIST ---
COUNTRY_CODES = {
    'Afghanistan': 'AFG', 'Angola': 'AGO', 'Albania': 'ALB', 'United Arab Emirates': 'ARE', 'Argentina': 'ARG', 'Armenia': 'ARM', 'Antarctica': 'ATA', 'Australia': 'AUS', 'Austria': 'AUT', 'Azerbaijan': 'AZE',
    'Burundi': 'BDI', 'Belgium': 'BEL', 'Benin': 'BEN', 'Burkina Faso': 'BFA', 'Bangladesh': 'BGD', 'Bulgaria': 'BGR', 'Bahamas': 'BHS', 'Bosnia and Herzegovina': 'BIH', 'Belarus': 'BLR', 'Belize': 'BLZ',
    'Bolivia': 'BOL', 'Brazil': 'BRA', 'Brunei': 'BRN', 'Bhutan': 'BTN', 'Botswana': 'BWA', 'Central African Republic': 'CAF', 'Canada': 'CAN', 'Switzerland': 'CHE', 'Chile': 'CHL', 'China': 'CHN',
    'Ivory Coast': 'CIV', 'Cameroon': 'CMR', 'DR Congo': 'COD', 'Republic of the Congo': 'COG', 'Colombia': 'COL', 'Costa Rica': 'CRI', 'Cuba': 'CUB', 'Northern Cyprus': 'CYN', 'Cyprus': 'CYP', 'Czech Republic': 'CZE',
    'Germany': 'DEU', 'Djibouti': 'DJI', 'Denmark': 'DNK', 'Dominican Republic': 'DOM', 'Algeria': 'DZA', 'Ecuador': 'ECU', 'Egypt': 'EGY', 'Eritrea': 'ERI', 'Spain': 'ESP', 'Estonia': 'EST',
    'Ethiopia': 'ETH', 'Finland': 'FIN', 'Fiji': 'FJI', 'France': 'FRA', 'Gabon': 'GAB', 'United Kingdom': 'GBR', 'Georgia': 'GEO', 'Ghana': 'GHA', 'Guinea': 'GIN',
    'Gambia': 'GMB', 'Guinea-Bissau': 'GNB', 'Equatorial Guinea': 'GNQ', 'Greece': 'GRC', 'Greenland': 'GRL', 'Guatemala': 'GTM', 'Guyana': 'GUY', 'Honduras': 'HND', 'Croatia': 'HRV', 'Haiti': 'HTI',
    'Hungary': 'HUN', 'Indonesia': 'IDN', 'India': 'IND', 'Ireland': 'IRL', 'Iran': 'IRN', 'Iraq': 'IRQ', 'Iceland': 'ISL', 'Israel': 'ISR', 'Italy': 'ITA',
    'Jamaica': 'JAM', 'Jordan': 'JOR', 'Japan': 'JPN', 'Kazakhstan': 'KAZ', 'Kenya': 'KEN', 'Kyrgyzstan': 'KGZ', 'Cambodia': 'KHM', 'South Korea': 'KOR', 'Kosovo': 'KOS', 'Kuwait': 'KWT',
    'Laos': 'LAO', 'Lebanon': 'LBN', 'Liberia': 'LBR', 'Libya': 'LBY', 'Sri Lanka': 'LKA', 'Lesotho': 'LSO', 'Lithuania': 'LTU', 'Luxembourg': 'LUX', 'Latvia': 'LVA',
    'Morocco': 'MAR', 'Moldova': 'MDA', 'Madagascar': 'MDG', 'Mexico': 'MEX', 'Macedonia': 'MKD', 'Mali': 'MLI', 'Myanmar': 'MMR', 'Montenegro': 'MNE', 'Mongolia': 'MNG',
    'Mozambique': 'MOZ', 'Mauritania': 'MRT', 'Malawi': 'MWI', 'Malaysia': 'MYS', 'Namibia': 'NAM', 'New Caledonia': 'NCL', 'Niger': 'NER', 'Nigeria': 'NGA', 'Nicaragua': 'NIC',
    'Netherlands': 'NLD', 'Norway': 'NOR', 'Nepal': 'NPL', 'New Zealand': 'NZL', 'Oman': 'OMN', 'Pakistan': 'PAK', 'Panama': 'PAN', 'Peru': 'PER', 'Philippines': 'PHL',
    'Papua New Guinea': 'PNG', 'Poland': 'POL', 'Puerto Rico': 'PRI', 'North Korea': 'PRK', 'Portugal': 'PRT', 'Paraguay': 'PRY', 'Qatar': 'QAT', 'Romania': 'ROU', 'Russia': 'RUS',
    'Rwanda': 'RWA', 'Western Sahara': 'ESH', 'Saudi Arabia': 'SAU', 'Sudan': 'SDN', 'South Sudan': 'SSD', 'Senegal': 'SEN', 'Solomon Islands': 'SLB', 'Sierra Leone': 'SLE', 'El Salvador': 'SLV', 'Somaliland': 'SOM', 'Somalia': 'SOM', 'Republic of Serbia': 'SRB',
    'Suriname': 'SUR', 'Slovakia': 'SVK', 'Slovenia': 'SVN', 'Sweden': 'SWE', 'Swaziland': 'SWZ', 'Syria': 'SYR', 'Chad': 'TCD', 'Togo': 'TGO', 'Thailand': 'THA',
    'Tajikistan': 'TJK', 'Turkmenistan': 'TKM', 'East Timor': 'TLS', 'Trinidad and Tobago': 'TTO', 'Tunisia': 'TUN', 'Turkey': 'TUR', 'Taiwan': 'TWN', 'Tanzania': 'TZA', 'Uganda': 'UGA',
    'Ukraine': 'UKR', 'Uruguay': 'URY', 'United States': 'USA', 'Uzbekistan': 'UZB', 'Venezuela': 'VEN', 'Vietnam': 'VNM', 'Vanuatu': 'VUT', 'Yemen': 'YEM', 'South Africa': 'ZAF', 'Zambia': 'ZMB', 'Zimbabwe': 'ZWE'
}


# --- FastAPI Application ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for simplicity, can be restricted later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
def read_root():
    return {"status": "ok"}


@app.post("/api/query", response_model=List[CountryData])
async def handle_query(req: QueryRequest):
    prompt = f"""
You are a world-class data scientist AI building a dataset for a global choropleth map.
Your PRIMARY GOAL is to generate a comprehensive global dataset, NOT just a "top 10" list.
The user's query is: "{req.query}"
You must provide a response ONLY in a valid JSON object format with two keys: "label" and "data".
1. "label": A short, descriptive title for the data (e.g., "Estimated Literacy Rate (%)").
2. "data": A JSON list of objects, one for each country.
Here is the mapping of country names to the required 3-letter codes: {json.dumps(list(COUNTRY_CODES.values()))}
CRITICAL INSTRUCTIONS:
- Your response MUST include a large number of countries to cover the world map. For broad topics like GDP, population, or birthrate, you should provide data for AT LEAST 150 countries.
- For each country object in the "data" list, you must include two keys:
  - "country_code": The EXACT 3-letter ISO code from the provided list.
  - "value": A numeric value representing your best estimate for the query.
- If a query is abstract (like "happiness"), assign a relative score from 1 to 100.
- Do NOT include countries for which you cannot find or estimate a value.
- Ensure your entire output is a single, valid JSON object and nothing else.
"""
    print(f"\n[DEBUG] Sending query to GPT-4o: '{req.query}'")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful data analysis AI that only responds with a valid JSON object designed to populate a world map."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        response_content = response.choices[0].message.content
        print(f"[DEBUG] GPT-4o responded with a JSON object.")
        
        ai_data = json.loads(response_content)
        
        final_response = [
            {
                "country_code": item.get("country_code"),
                "value": item.get("value"),
                "label": ai_data.get("label", "Estimated Value")
            }
            for item in ai_data.get("data", []) if item.get("country_code") in COUNTRY_CODES.values()
        ]
        
        if not final_response:
             raise HTTPException(status_code=404, detail="The AI could not generate data for your query.")

        return final_response

    except json.JSONDecodeError:
        print(f"[ERROR] Failed to decode JSON from AI response.")
        raise HTTPException(status_code=500, detail="The AI returned an invalid format. Please try again.")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please check the server logs.")