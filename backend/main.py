# main.py
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv # Import the library

# --- THE DEFINITIVE LOCAL DEVELOPMENT API KEY LOADING LOGIC ---

# --- Setup and Initialization ---

print("📂 Current working directory:", os.getcwd())

if os.path.exists(".env"):
    print("✅ .env file FOUND")
else:
    print("❌ .env file NOT FOUND")

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

# בדיקה קריטית בזמן הטעינה של האפליקציה
if not api_key:
    print("🚨 FATAL: OPENAI_API_KEY environment variable is not set. The application cannot start properly.")
    # במצב אמיתי, אפשר אפילו לגרום לאפליקציה לקרוס כאן כדי למנוע ריצה במצב לא תקין
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


# --- Country Codes (abbreviated for clarity) ---
COUNTRY_CODES = { 'United States': 'USA', 'Canada': 'CAN', 'Mexico': 'MEX', # ... and so on ...
    'Afghanistan': 'AFG', 'Angola': 'AGO', 'Albania': 'ALB', 'United Arab Emirates': 'ARE', 'Argentina': 'ARG', 'Armenia': 'ARM', 'Antarctica': 'ATA', 'Australia': 'AUS', 'Austria': 'AUT', 'Azerbaijan': 'AZE',
    'Burundi': 'BDI', 'Belgium': 'BEL', 'Benin': 'BEN', 'Burkina Faso': 'BFA', 'Bangladesh': 'BGD', 'Bulgaria': 'BGR', 'Bahamas': 'BHS', 'Bosnia and Herzegovina': 'BIH', 'Belarus': 'BLR', 'Belize': 'BLZ',
    'Bolivia': 'BOL', 'Brazil': 'BRA', 'Brunei': 'BRN', 'Bhutan': 'BTN', 'Botswana': 'BWA', 'Central African Republic': 'CAF', 'Switzerland': 'CHE', 'Chile': 'CHL', 'China': 'CHN',
    'Ivory Coast': 'CIV', 'Cameroon': 'CMR', 'DR Congo': 'COD', 'Republic of the Congo': 'COG', 'Colombia': 'COL', 'Costa Rica': 'CRI', 'Cuba': 'CUB', 'Northern Cyprus': 'CYN', 'Cyprus': 'CYP', 'Czech Republic': 'CZE',
    'Germany': 'DEU', 'Djibouti': 'DJI', 'Denmark': 'DNK', 'Dominican Republic': 'DOM', 'Algeria': 'DZA', 'Ecuador': 'ECU', 'Egypt': 'EGY', 'Eritrea': 'ERI', 'Spain': 'ESP', 'Estonia': 'EST',
    'Ethiopia': 'ETH', 'Finland': 'FIN', 'Fiji': 'FJI', 'France': 'FRA', 'Gabon': 'GAB', 'United Kingdom': 'GBR', 'Georgia': 'GEO', 'Ghana': 'GHA', 'Guinea': 'GIN',
    'Gambia': 'GMB', 'Guinea-Bissau': 'GNB', 'Equatorial Guinea': 'GNQ', 'Greece': 'GRC', 'Greenland': 'GRL', 'Guatemala': 'GTM', 'Guyana': 'GUY', 'Honduras': 'HND', 'Croatia': 'HRV', 'Haiti': 'HTI',
    'Hungary': 'HUN', 'Indonesia': 'IDN', 'India': 'IND', 'Ireland': 'IRL', 'Iran': 'IRN', 'Iraq': 'IRQ', 'Iceland': 'ISL', 'Israel': 'ISR', 'Italy': 'ITA',
    'Jamaica': 'JAM', 'Jordan': 'JOR', 'Japan': 'JPN', 'Kazakhstan': 'KAZ', 'Kenya': 'KEN', 'Kyrgyzstan': 'KGZ', 'Cambodia': 'KHM', 'South Korea': 'KOR', 'Kosovo': 'KOS', 'Kuwait': 'KWT',
    'Laos': 'LAO', 'Lebanon': 'LBN', 'Liberia': 'LBR', 'Libya': 'LBY', 'Sri Lanka': 'LKA', 'Lesotho': 'LSO', 'Lithuania': 'LTU', 'Luxembourg': 'LUX', 'Latvia': 'LVA',
    'Morocco': 'MAR', 'Moldova': 'MDA', 'Madagascar': 'MDG', 'Macedonia': 'MKD', 'Mali': 'MLI', 'Myanmar': 'MMR', 'Montenegro': 'MNE', 'Mongolia': 'MNG',
    'Mozambique': 'MOZ', 'Mauritania': 'MRT', 'Malawi': 'MWI', 'Malaysia': 'MYS', 'Namibia': 'NAM', 'New Caledonia': 'NCL', 'Niger': 'NER', 'Nigeria': 'NGA', 'Nicaragua': 'NIC',
    'Netherlands': 'NLD', 'Norway': 'NOR', 'Nepal': 'NPL', 'New Zealand': 'NZL', 'Oman': 'OMN', 'Pakistan': 'PAK', 'Panama': 'PAN', 'Peru': 'PER', 'Philippines': 'PHL',
    'Papua New Guinea': 'PNG', 'Poland': 'POL', 'Puerto Rico': 'PRI', 'North Korea': 'PRK', 'Portugal': 'PRT', 'Paraguay': 'PRY', 'Qatar': 'QAT', 'Romania': 'ROU', 'Russia': 'RUS',
    'Rwanda': 'RWA', 'Western Sahara': 'ESH', 'Saudi Arabia': 'SAU', 'Sudan': 'SDN', 'South Sudan': 'SSD', 'Senegal': 'SEN', 'Solomon Islands': 'SLB', 'Sierra Leone': 'SLE', 'El Salvador': 'SLV', 'Somaliland': 'SOM', 'Somalia': 'SOM', 'Republic of Serbia': 'SRB',
    'Suriname': 'SUR', 'Slovakia': 'SVK', 'Slovenia': 'SVN', 'Sweden': 'SWE', 'Swaziland': 'SWZ', 'Syria': 'SYR', 'Chad': 'TCD', 'Togo': 'TGO', 'Thailand': 'THA',
    'Tajikistan': 'TJK', 'Turkmenistan': 'TKM', 'East Timor': 'TLS', 'Trinidad and Tobago': 'TTO', 'Tunisia': 'TUN', 'Turkey': 'TUR', 'Taiwan': 'TWN', 'Tanzania': 'TZA', 'Uganda': 'UGA',
    'Ukraine': 'UKR', 'Uruguay': 'URY', 'Uzbekistan': 'UZB', 'Venezuela': 'VEN', 'Vietnam': 'VNM', 'Vanuatu': 'VUT', 'Yemen': 'YEM', 'South Africa': 'ZAF', 'Zambia': 'ZMB', 'Zimbabwe': 'ZWE'
}


# --- FastAPI Application ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Specific for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/api/query", response_model=List[CountryData])
async def handle_query(req: QueryRequest):
    prompt = f"""
You are a world-class data scientist AI building a dataset for a global choropleth map. Your PRIMARY GOAL is to generate a comprehensive global dataset. The user's query is: "{req.query}". You must provide a response ONLY in a valid JSON object format with two keys: "label" and "data". "label" should be a short descriptive title. "data" should be a JSON list of objects, one for each country. For each country object, include "country_code" (the EXACT 3-letter ISO code) and "value" (your numeric estimate). Your response MUST include a large number of countries (at least 150 for broad topics) to cover the world map. Here are the valid country codes: {json.dumps(list(COUNTRY_CODES.values()))}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful data analysis AI that only responds with JSON for a world map."},
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
        raise HTTPException(status_code=500, detail="An internal error occurred.")