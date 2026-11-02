from detector import SonarAnomalyDetector

detector = SonarAnomalyDetector()
test_images = [
    'sonar_shipwreck_debris.jpg',
    'sonar_pipeline_net.jpg',
    'sonar_clear_seabed.jpg'
]

print("=== Testing AquaSentinel Sonar Anomaly Detector ===")
for name in test_images:
    prefix = name.replace('.jpg', '')
    res = detector.process_image(f'sample_images/{name}', 'processed', prefix)
    print(f"File: {name:<26} | Candidates: {res['candidate_count']:<2} | Score: {res['heuristic_score']:<5} | Status: {res['status']:<18} | Time: {res['processing_time_ms']}ms")
    for cand in res['candidates']:
        print(f"   -> #{cand['id']} at ({cand['x']}, {cand['y']}), size {cand['width']}x{cand['height']}, area {cand['area']}px, type: {cand['type']}")
