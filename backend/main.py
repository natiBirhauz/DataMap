# main.py
import os
import json
import uvicorn  # Import uvicorn to run from script if needed
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI

# --- THE DEFINITIVE API KEY LOADING LOGIC ---
# This is the most robust way to do it for production.
# It relies ONLY on the environment variables provided by the platform (Railway).
api_key = os.getenv("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")
if not api_key:
    # This will cause a hard crash with a very clear message in the logs.
    raise ValueError("FATAL ERROR: The OPENAI_API_KEY environment variable was not found or is empty in the Railway deployment.")
else:
    print("SUCCESS: OpenAI API Key was found in the environment.")

client = OpenAI(api_key=api_key)


# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str

class CountryData(BaseModel):
    country_code: str
    value: Optional[float]
    label: str


# --- Country Codes ---
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    # This lets us know the server is at least running
    return {"status": "DataMap Backend is running"}

@app.post("/api/query", response_model=List[CountryData])
async def handle_query(req: QueryRequest):
    # This prompt is confirmed to work well
    prompt = f"""
You are a world-class data scientist AI building a dataset for a global choropleth map.
Your PRIMARY GOAL is to generate a comprehensive global dataset, NOT just a "top 10" list.
The user's query is: "{req.query}"
You must provide a response ONLY in a valid JSON object format with two keys: "label" and "data".
1. "label": A short, descriptive title for the data (e.g., "Estimated Literacy Rate (%)").
2. "data": A JSON list of objects.
Here is the mapping of country names to the required 3-letter codes: {json.dumps(list(COUNTRY_CODES.values()))}
CRITICAL INSTRUCTIONS:
- Your response MUST include a large number of countries. For broad topics, provide data for AT LEAST 150 countries.
- For each country object in the "data" list, you must include two keys: "country_code" and "value".
- Ensure your entire output is a single, valid JSON object.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a data analysis AI that only responds with JSON for a world map."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        response_content = response.choices[0].message.content
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

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please check the server logs.")