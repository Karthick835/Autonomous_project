import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app

client = TestClient(app)

def test_api_status():
    res = client.get("/api/status")
    assert res.status_code == 200
    assert res.json()["status"] == "online"
    print("[OK] /api/status test passed!")

def test_list_sample_datasets():
    res = client.get("/api/sample-datasets")
    assert res.status_code == 200
    samples = res.json()["samples"]
    assert len(samples) > 0
    assert samples[0]["name"] == "sample_churn.csv"
    print(f"[OK] /api/sample-datasets test passed! Samples count: {len(samples)}")

def test_start_investigation_endpoint():
    res = client.post("/api/investigate", json={
        "csv_filename": "sample_churn.csv",
        "domain_context": "Customer Retention Audit"
    })
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert data["status"] == "running"
    print(f"[OK] /api/investigate test passed! Created session_id: {data['session_id']}")

if __name__ == "__main__":
    test_api_status()
    test_list_sample_datasets()
    test_start_investigation_endpoint()
    print("ALL TASK 4 FASTAPI ENDPOINT TESTS PASSED!")
