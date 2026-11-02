"""
AquaSentinel - Sonar Image Processing & Anomaly Detection Engine
Classical Computer Vision pipeline for underwater side-scan sonar image analysis.

8-Step OpenCV Pipeline:
1. Load image (BGR)
2. Convert image to grayscale
3. Gaussian Blur (acoustic speckle noise suppression)
4. CLAHE (Contrast Limited Adaptive Histogram Equalization)
5. Canny Edge Detection (high-frequency boundary extraction)
6. Dual-band Thresholding (acoustic highlight backscatter & shadow voids)
7. Morphological operations & Contour Detection (candidate localization)
8. Filtering noise & Bounding Box Annotation
"""

import os
import time
import cv2
import numpy as np

class SonarAnomalyDetector:
    def __init__(self, min_area=300, max_area_ratio=0.45, blur_kernel=(5, 5), clahe_clip=2.0, clahe_grid=(8, 8)):
        """
        Initialize detector with computer vision parameters.
        :param min_area: Minimum contour area in pixels to filter out acoustic noise.
        :param max_area_ratio: Maximum area fraction to filter out full-image background shifts.
        :param blur_kernel: Gaussian blur kernel size for speckle smoothing.
        :param clahe_clip: CLAHE contrast clip limit.
        :param clahe_grid: CLAHE tile grid size.
        """
        self.min_area = min_area
        self.max_area_ratio = max_area_ratio
        self.blur_kernel = blur_kernel
        self.clahe_clip = clahe_clip
        self.clahe_grid = clahe_grid

    def process_image(self, input_path, output_dir, file_prefix):
        """
        Runs the complete CV pipeline on the sonar image.
        Returns a dictionary containing metrics, intermediate file names, and candidate regions.
        """
        start_time = time.time()
        os.makedirs(output_dir, exist_ok=True)

        # 1. Load the uploaded image
        img_bgr = cv2.imread(input_path)
        if img_bgr is None:
            raise ValueError(f"Unable to decode image from path: {input_path}")

        h, w = img_bgr.shape[:2]
        total_pixels = h * w
        max_area = int(total_pixels * self.max_area_ratio)

        # 2. Convert to Grayscale
        if len(img_bgr.shape) == 3 and img_bgr.shape[2] == 3:
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_bgr.copy()

        # 3. Apply Gaussian Blur to reduce acoustic speckle noise
        blurred = cv2.GaussianBlur(gray, self.blur_kernel, sigmaX=1.2)

        # 4. Apply CLAHE to improve local acoustic contrast
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip, tileGridSize=self.clahe_grid)
        clahe_enhanced = clahe.apply(blurred)

        # 5. Apply Canny Edge Detection
        v = np.median(clahe_enhanced)
        lower_canny = int(max(0, 0.66 * v))
        upper_canny = int(min(255, 1.33 * v))
        canny_edges = cv2.Canny(clahe_enhanced, lower_canny, upper_canny)

        # 6. Apply Thresholding to identify suspicious acoustic regions
        # Underwater side-scan sonar highlights hard objects via strong acoustic reflections (bright)
        # and leaves acoustic shadows (dark) behind them.
        mean_val = float(np.mean(clahe_enhanced))
        std_val = float(np.std(clahe_enhanced))

        high_thresh = max(180, int(mean_val + 1.8 * std_val))
        low_thresh = min(45, int(mean_val - 1.8 * std_val))

        _, mask_bright = cv2.threshold(clahe_enhanced, high_thresh, 255, cv2.THRESH_BINARY)
        _, mask_dark = cv2.threshold(clahe_enhanced, low_thresh, 255, cv2.THRESH_BINARY_INV)
        raw_anomaly_mask = cv2.bitwise_or(mask_bright, mask_dark)

        # Morphological opening (remove tiny speckles) and closing (bridge small gaps)
        morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        opened_mask = cv2.morphologyEx(raw_anomaly_mask, cv2.MORPH_OPEN, morph_kernel)
        closed_mask = cv2.morphologyEx(opened_mask, cv2.MORPH_CLOSE, morph_kernel)

        # 7. Use Contour Detection to locate candidate regions
        contours, _ = cv2.findContours(closed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidate_regions = []
        annotated_img = img_bgr.copy()
        overlay = annotated_img.copy()

        total_anomaly_area = 0
        contour_id = 1

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filter extremely small noise or massive full-frame masks
            if area < self.min_area or area > max_area:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect_ratio = round(float(bw) / max(1.0, float(bh)), 2)
            region_crop = gray[y:y+bh, x:x+bw]
            region_mean_intensity = round(float(np.mean(region_crop)), 1)
            total_anomaly_area += area

            # Spatial quadrant designation
            loc_y = "Upper" if (y + bh / 2) < (h / 3) else ("Lower" if (y + bh / 2) > (2 * h / 3) else "Central")
            loc_x = "Port (Left)" if (x + bw / 2) < (w / 3) else ("Starboard (Right)" if (x + bw / 2) > (2 * w / 3) else "Nadir (Center)")
            location_label = f"{loc_y} {loc_x}"

            # Heuristic candidate description
            if aspect_ratio >= 2.8 or aspect_ratio <= 0.35:
                heuristic_type = "Linear Structure (Possible Cable / Pipe / Edge)"
            elif region_mean_intensity > (mean_val + 0.8 * std_val):
                heuristic_type = "High Backscatter Reflection (Hard Debris / Metallic)"
            elif region_mean_intensity < (mean_val - 0.8 * std_val):
                heuristic_type = "Acoustic Shadow Void (Depression or Target Shadow)"
            else:
                heuristic_type = "Acoustic Reflection Anomaly"

            candidate_regions.append({
                "id": contour_id,
                "x": int(x),
                "y": int(y),
                "width": int(bw),
                "height": int(bh),
                "area": int(area),
                "aspect_ratio": aspect_ratio,
                "mean_intensity": region_mean_intensity,
                "location": location_label,
                "type": heuristic_type
            })

            # 8. Draw Bounding Boxes around detected candidate regions
            # Semi-transparent highlight box
            cv2.rectangle(overlay, (x, y), (x + bw, y + bh), (255, 200, 0), -1)

            # Bright ocean cyan bounding box border (BGR: 255, 215, 0)
            cv2.rectangle(annotated_img, (x, y), (x + bw, y + bh), (255, 215, 0), 2)

            # Corner target crosshairs
            c_len = min(12, max(4, bw // 5), max(4, bh // 5))
            cv2.line(annotated_img, (x, y), (x + c_len, y), (0, 255, 255), 2)
            cv2.line(annotated_img, (x, y), (x, y + c_len), (0, 255, 255), 2)
            cv2.line(annotated_img, (x + bw, y + bh), (x + bw - c_len, y + bh), (0, 255, 255), 2)
            cv2.line(annotated_img, (x + bw, y + bh), (x + bw, y + bh - c_len), (0, 255, 255), 2)

            # Badge tag label
            label = f"#{contour_id} [Area: {int(area)}px]"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.45
            thickness = 1
            (lbl_w, lbl_h), _ = cv2.getTextSize(label, font, font_scale, thickness)
            
            badge_y1 = max(0, y - lbl_h - 8)
            badge_y2 = y
            cv2.rectangle(annotated_img, (x, badge_y1), (x + lbl_w + 8, badge_y2), (10, 20, 35), -1)
            cv2.rectangle(annotated_img, (x, badge_y1), (x + lbl_w + 8, badge_y2), (255, 215, 0), 1)
            cv2.putText(annotated_img, label, (x + 4, badge_y2 - 4), font, font_scale, (0, 255, 255), thickness, cv2.LINE_AA)

            contour_id += 1

        # Blend semi-transparent highlight layer
        annotated_img = cv2.addWeighted(overlay, 0.15, annotated_img, 0.85, 0)

        # 9. Compute Heuristic Anomaly Score (0 - 100)
        # Clearly documented as rule-based heuristic indicator, NOT deep learning confidence
        candidate_count = len(candidate_regions)
        area_coverage_pct = round((total_anomaly_area / total_pixels) * 100, 2)
        edge_pixels_pct = round((float(np.count_nonzero(canny_edges)) / total_pixels) * 100, 2)

        score_count_comp = min(40.0, candidate_count * 15.0)
        score_area_comp = min(35.0, area_coverage_pct * 4.0)
        score_edge_comp = min(25.0, edge_pixels_pct * 2.0)

        heuristic_score = round(min(100.0, score_count_comp + score_area_comp + score_edge_comp), 1)

        if candidate_count == 0:
            heuristic_score = 0.0
            status = "Nominal Seabed"
            status_desc = "Standard sonar backscatter profile. No significant acoustic anomalies or debris signatures detected."
            status_class = "success"
        elif heuristic_score >= 60.0:
            status = "High Suspicion"
            status_desc = f"Identified {candidate_count} prominent acoustic candidate region(s) with significant contrast deviations from seabed baseline."
            status_class = "danger"
        else:
            status = "Moderate Suspicion"
            status_desc = f"Identified {candidate_count} localized candidate region(s) requiring sonar operator review."
            status_class = "warning"

        # Save pipeline visual steps
        gray_file = f"{file_prefix}_1_gray.jpg"
        clahe_file = f"{file_prefix}_2_clahe.jpg"
        canny_file = f"{file_prefix}_3_canny.jpg"
        thresh_file = f"{file_prefix}_4_thresh.jpg"
        annotated_file = f"{file_prefix}_5_annotated.jpg"

        cv2.imwrite(os.path.join(output_dir, gray_file), gray)
        cv2.imwrite(os.path.join(output_dir, clahe_file), clahe_enhanced)
        cv2.imwrite(os.path.join(output_dir, canny_file), canny_edges)
        cv2.imwrite(os.path.join(output_dir, thresh_file), closed_mask)
        cv2.imwrite(os.path.join(output_dir, annotated_file), annotated_img)

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "success": True,
            "dimensions": {"width": w, "height": h},
            "candidate_count": candidate_count,
            "candidates": candidate_regions,
            "heuristic_score": heuristic_score,
            "score_breakdown": {
                "candidate_factor": round(score_count_comp, 1),
                "area_coverage_pct": area_coverage_pct,
                "edge_density_pct": edge_pixels_pct
            },
            "status": status,
            "status_desc": status_desc,
            "status_class": status_class,
            "processing_time_ms": elapsed_ms,
            "mean_background_intensity": round(mean_val, 1),
            "files": {
                "grayscale": gray_file,
                "clahe": clahe_file,
                "canny": canny_file,
                "threshold": thresh_file,
                "annotated": annotated_file
            }
        }
