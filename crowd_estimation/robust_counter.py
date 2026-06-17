import os
import cv2
import numpy as np
from ultralytics import YOLO

class RobustCrowdCounter:
    """
    Robust Crowd Counting Engine for CCTV and Traffic Surveillance.
    Implements multi-stage spatial and confidence filtering to eliminate
    false positives, duplicate boxes, and background noise.
    """
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        
    def _nms_numpy(self, boxes, scores, iou_threshold=0.45):
        """
        Pure NumPy implementation of Non-Maximum Suppression (NMS).
        Eliminates overlapping duplicate bounding boxes.
        """
        if len(boxes) == 0:
            return []
            
        boxes = np.array(boxes)
        scores = np.array(scores)
        
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            ovr = inter / (areas[i] + areas[order[1:]] - inter)
            inds = np.where(ovr <= iou_threshold)[0]
            order = order[inds + 1]
            
        return keep

    def get_density_category(self, count):
        """Maps final count to crowd density categories."""
        if count < 20:
            return "Low"
        elif count < 50:
            return "Medium"
        elif count < 100:
            return "High"
        else:
            return "Extreme"

    def count_crowd(self, img_path, min_conf=0.30, min_box_size=(15, 15), border_margin_pct=0.05, iou_threshold=0.45):
        """
        Processes a CCTV image, runs YOLOv8, and filters detections.
        
        Args:
            img_path (str): Path to input image file.
            min_conf (float): Minimum confidence threshold.
            min_box_size (tuple): Minimum width and height of a bounding box in pixels.
            border_margin_pct (float): Percentage of border margin to ignore detections.
            iou_threshold (float): Intersection-over-Union threshold for NMS.
            
        Returns:
            dict: Containing raw detections count, filtered boxes, final count, and density label.
        """
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"Image not found at {img_path}")
            
        img_h, img_w, _ = img.shape
        
        # Run raw inference (without class filtering in prediction step, to count raw model outputs)
        results = self.model.predict(img, verbose=False)[0]
        
        # 1. Calculate Raw Detections (all bounding boxes output by the model)
        raw_boxes_list = results.boxes.data.cpu().numpy()
        raw_detections = len(raw_boxes_list)
        
        # Lists to store pre-filtered boxes for custom NMS
        candidate_boxes = []
        candidate_scores = []
        
        # Define border boundary coordinates
        margin_w = int(img_w * border_margin_pct)
        margin_h = int(img_h * border_margin_pct)
        
        # 2. Apply Strict Filtering
        for box in results.boxes:
            # Filter A: Only Class 0 (Person)
            cls_id = int(box.cls[0].item())
            if cls_id != 0:
                continue
                
            # Filter B: Remove Low Confidence
            conf = float(box.conf[0].item())
            if conf < min_conf:
                continue
                
            # Get box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            box_w = x2 - x1
            box_h = y2 - y1
            
            # Filter C: Ignore Tiny Bounding Boxes
            if box_w < min_box_size[0] or box_h < min_box_size[1]:
                continue
                
            # Filter D: Ignore Detections near image borders
            # Checks if the bounding box center lies in the border margin zone
            cx = x1 + box_w // 2
            cy = y1 + box_h // 2
            if (cx < margin_w or cx > (img_w - margin_w) or 
                cy < margin_h or cy > (img_h - margin_h)):
                continue
                
            candidate_boxes.append([x1, y1, x2, y2])
            candidate_scores.append(conf)
            
        # Filter E: Apply Non-Maximum Suppression (NMS)
        keep_indices = self._nms_numpy(candidate_boxes, candidate_scores, iou_threshold)
        
        filtered_detections = []
        for idx in keep_indices:
            filtered_detections.append({
                "box": candidate_boxes[idx],
                "confidence": float(candidate_scores[idx])
            })
            
        final_crowd_count = len(filtered_detections)
        crowd_density = self.get_density_category(final_crowd_count)
        
        return {
            "raw_detections": raw_detections,
            "filtered_detections": filtered_detections,
            "final_crowd_count": final_crowd_count,
            "crowd_density": crowd_density,
            "image_dimensions": (img_w, img_h)
        }

# Simple self-test code block
if __name__ == "__main__":
    # Test on our newly generated photorealistic street crosswalk image
    test_img = "benchmark_data/blr_street_cctv_yolo.png"
    if os.path.exists(test_img):
        counter = RobustCrowdCounter()
        res = counter.count_crowd(test_img)
        print("\n=== Robust Crowd Counting Test Run ===")
        print(f"Image analyzed: {test_img}")
        print(f"Dimensions: {res['image_dimensions'][0]}x{res['image_dimensions'][1]}")
        print(f"Raw Model Detections (All Classes/Unfiltered): {res['raw_detections']}")
        print(f"Filtered Detections (Person Class Only + Filters): {len(res['filtered_detections'])}")
        print(f"Final Verified Crowd Count: {res['final_crowd_count']}")
        print(f"Crowd Density Classification: {res['crowd_density']}")
        print("======================================\n")
    else:
        print(f"Test image {test_img} not found. Please verify paths.")
