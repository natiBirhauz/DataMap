# backend/test_free_llm.py
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app, generate_fallback_data, query_free_llm, COUNTRY_CODES_SET

client = TestClient(app)

def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "llm_providers" in data
    print("[PASS] Root endpoint test passed.")

def test_fallback_engine():
    queries = [
        "GDP per capita in Europe",
        "Population density",
        "Life expectancy",
        "Renewable energy share",
        "Coffee consumption"
    ]
    for q in queries:
        result = generate_fallback_data(q)
        assert "label" in result and result["label"]
        assert "data" in result and len(result["data"]) >= 50
        for item in result["data"]:
            assert "country_code" in item
            assert item["country_code"] in COUNTRY_CODES_SET
            assert "value" in item
            assert isinstance(item["value"], (int, float))
    print(f"[PASS] Fallback engine passed across {len(queries)} query topics.")

def test_query_api_without_key():
    # User sends query without any api_key
    payload = {"query": "Life expectancy by country"}
    resp = client.post("/api/query/", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 30
    for item in data[:5]:
        assert "country_code" in item
        assert "value" in item
        assert "label" in item
    print(f"[PASS] Query API without key passed (returned {len(data)} countries).")

def test_options_preflight():
    resp = client.options("/api/query/")
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"
    print("[PASS] OPTIONS preflight test passed.")

if __name__ == "__main__":
    print("Running backend free LLM tests...")
    test_root_endpoint()
    test_fallback_engine()
    test_query_api_without_key()
    test_options_preflight()
    print("\nALL BACKEND TESTS PASSED SUCCESSFULLY!")
