"""
AquaSentinel - End-to-End Workflow Verification Suite
Validates all Flask endpoints, file uploading, computer vision pipeline execution,
telemetry persistence, and results visualization.
"""

import os
import json
import io
from app import app, HISTORY_FILE, PROCESSED_FOLDER, UPLOAD_FOLDER

def run_tests():
    print("=" * 60)
    print("  AquaSentinel - Running Comprehensive End-to-End Tests")
    print("=" * 60)

    client = app.test_client()

    # Test 1: GET /
    print("\n[Test 1] GET / (Home Page)...")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"AquaSentinel" in res.data
    assert b"Autonomous" in res.data
    print("   -> PASSED: Home page rendered with status 200.")

    # Test 2: GET /dashboard
    print("\n[Test 2] GET /dashboard...")
    res = client.get("/dashboard")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"Sonar Research Dashboard" in res.data
    print("   -> PASSED: Dashboard rendered with status 200.")

    # Test 3: GET /upload
    print("\n[Test 3] GET /upload...")
    res = client.get("/upload")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"Drag & drop side-scan sonar image here" in res.data
    assert b"Instant Demonstration Samples" in res.data
    print("   -> PASSED: Upload page and demo samples shelf rendered with status 200.")

    # Test 4: POST /analyze with Demo Sample (Shipwreck)
    print("\n[Test 4] POST /analyze with Demo Sample 'sonar_shipwreck_debris.jpg'...")
    res = client.post("/analyze", data={"demo_sample": "sonar_shipwreck_debris.jpg"}, follow_redirects=False)
    assert res.status_code == 302, f"Expected redirect (302), got {res.status_code}"
    results_url = res.headers["Location"]
    print(f"   -> Redirected to: {results_url}")

    # Test 5: GET /results/<analysis_id>
    print("\n[Test 5] GET results page from redirect...")
    res = client.get(results_url)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"Sonar Scan: sonar_shipwreck_debris.jpg" in res.data
    assert b"Heuristic Anomaly Index" in res.data
    assert b"Identified Candidate Anomaly Regions" in res.data
    print("   -> PASSED: Results page rendered correctly with bounding boxes and metrics.")

    # Test 6: POST /analyze with Direct File Upload
    print("\n[Test 6] POST /analyze with Direct File Upload ('sonar_pipeline_net.jpg')...")
    sample_file_path = os.path.join("sample_images", "sonar_pipeline_net.jpg")
    with open(sample_file_path, "rb") as f:
        file_bytes = f.read()

    res = client.post(
        "/analyze",
        data={"sonar_file": (io.BytesIO(file_bytes), "my_custom_sonar_scan.jpg")},
        content_type="multipart/form-data",
        follow_redirects=False
    )
    assert res.status_code == 302, f"Expected redirect (302), got {res.status_code}"
    pipeline_results_url = res.headers["Location"]
    print(f"   -> Redirected to: {pipeline_results_url}")

    res = client.get(pipeline_results_url)
    assert res.status_code == 200
    assert b"my_custom_sonar_scan.jpg" in res.data
    print("   -> PASSED: Custom file upload processed and visualized successfully.")

    # Test 7: GET /history
    print("\n[Test 7] GET /history...")
    res = client.get("/history")
    assert res.status_code == 200
    assert b"Stored Telemetry Logs" in res.data
    assert b"sonar_shipwreck_debris.jpg" in res.data
    assert b"my_custom_sonar_scan.jpg" in res.data
    print("   -> PASSED: Detection history shows both recorded scans.")

    # Test 8: GET /presentation
    print("\n[Test 8] GET /presentation (Academic Defense Guide)...")
    res = client.get("/presentation")
    assert res.status_code == 200
    assert b"AquaSentinel: Project Defense Guide" in res.data
    assert b"Problem Statement" in res.data
    assert b"Image Processing Methodology" in res.data
    print("   -> PASSED: Academic presentation view rendered successfully.")

    # Test 9: Verify JSON storage integrity
    print("\n[Test 9] Verifying JSON storage file...")
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"   -> Total records logged: {len(data)}")
    assert len(data) >= 2, "Expected at least 2 records in history"
    for r in data:
        print(f"      Record ID: #{r['id']} | File: {r['original_filename']} | Candidates: {r['candidate_count']} | Score: {r['heuristic_score']} | Status: {r['status']}")

    print("\n" + "=" * 60)
    print("  ALL 9 INTEGRATION & WORKFLOW TESTS PASSED CLEANLY!  ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
