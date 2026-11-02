"""
AquaSentinel - Realistic Synthetic Sonar Image Generator
Generates realistic side-scan sonar demo images with acoustic shadows, seabed texture,
and anomaly targets for testing and academic demonstrations without internet access.
"""

import os
import cv2
import numpy as np

def generate_seabed(w=800, h=600, mean_intensity=95, speckle_sigma=16):
    """Generates 2D acoustic seabed texture with realistic Perlin-like sand texture."""
    np.random.seed(42)
    # 2D low-frequency wave pattern (sand ripples)
    x = np.linspace(0, 12 * np.pi, w)
    y = np.linspace(0, 8 * np.pi, h)
    xv, yv = np.meshgrid(x, y)
    ripples = 12 * np.sin(xv * 0.4 + yv * 0.7) + 6 * np.cos(xv * 0.9 - yv * 0.3)
    
    # Natural illumination falloff from sonar altitude (lateral distance)
    # Center nadir or port/starboard falloff
    lateral_falloff = 10 * np.cos(np.linspace(-np.pi/3, np.pi/3, w))
    
    base = mean_intensity + ripples + lateral_falloff[np.newaxis, :]
    
    # Acoustic speckle noise
    speckle = np.random.normal(0, speckle_sigma, (h, w))
    seabed = np.clip(base + speckle, 20, 240).astype(np.uint8)
    # Slight Gaussian smoothing
    return cv2.GaussianBlur(seabed, (5, 5), 1.0)

def create_sample_sonar_images(output_dir="sample_images"):
    os.makedirs(output_dir, exist_ok=True)
    w, h = 800, 600

    # ==========================================
    # 1. Sample: Shipwreck / Large Debris Target
    # ==========================================
    sonar_1 = generate_seabed(w, h, mean_intensity=90, speckle_sigma=14)
    
    # Primary Target: Sunken ship hull / wreckage structure
    # Bright specular reflection highlight
    hull_pts = np.array([[260, 220], [380, 210], [420, 260], [350, 290], [250, 270]], np.int32)
    cv2.fillPoly(sonar_1, [hull_pts], 245)
    # Acoustic shadow directly behind the target (sound cannot penetrate the hull)
    shadow_pts = np.array([[380, 210], [540, 195], [590, 255], [420, 260]], np.int32)
    cv2.fillPoly(sonar_1, [shadow_pts], 15)
    
    # Secondary Target: Scattered container / cargo box
    cv2.rectangle(sonar_1, (560, 390), (630, 440), 240, -1) # highlight
    cv2.rectangle(sonar_1, (635, 390), (715, 440), 18, -1)  # acoustic shadow

    # Add realistic edge blur and acoustic blending
    sonar_1 = cv2.GaussianBlur(sonar_1, (3, 3), 0.8)
    cv2.imwrite(os.path.join(output_dir, "sonar_shipwreck_debris.jpg"), sonar_1)

    # ==========================================
    # 2. Sample: Submerged Pipeline & Ghost Net
    # ==========================================
    sonar_2 = generate_seabed(w, h, mean_intensity=85, speckle_sigma=13)
    
    # Submerged pipeline: continuous linear high-reflection acoustic pipe
    cv2.line(sonar_2, (80, 490), (720, 160), 245, 10)
    cv2.line(sonar_2, (92, 502), (732, 172), 15, 12) # parallel shadow
    
    # Ghost Net: Entangled fibrous mass snagged on seabed
    net_center = (360, 350)
    cv2.circle(sonar_2, net_center, 45, 230, -1)
    cv2.circle(sonar_2, (net_center[0] + 55, net_center[1] + 10), 50, 20, -1) # net shadow
    
    sonar_2 = cv2.GaussianBlur(sonar_2, (3, 3), 0.8)
    cv2.imwrite(os.path.join(output_dir, "sonar_pipeline_net.jpg"), sonar_2)

    # ==========================================
    # 3. Sample: Baseline Normal Seabed (No Debris)
    # ==========================================
    sonar_3 = generate_seabed(w, h, mean_intensity=95, speckle_sigma=12)
    cv2.imwrite(os.path.join(output_dir, "sonar_clear_seabed.jpg"), sonar_3)

    print(f"Generated 3 realistic sonar demo images in '{output_dir}/'")

if __name__ == "__main__":
    create_sample_sonar_images()
