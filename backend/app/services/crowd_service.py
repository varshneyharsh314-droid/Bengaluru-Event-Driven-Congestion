import os
import cv2
import time
import numpy as np
from app.core.config import settings

class CrowdService:
    def __init__(self):
        self.model = None
        self.yolo_available = False
        self.load_model()

    def load_model(self):
        try:
            from ultralytics import YOLO
            # Find the model in the workspace
            paths_to_check = [
                settings.YOLO_MODEL_PATH,
                os.path.join(os.path.dirname(__file__), "..", "..", "yolov8n.pt"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "yolov8n.pt"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "yolov8m.pt")
            ]
            
            selected_path = None
            for p in paths_to_check:
                if os.path.exists(p):
                    selected_path = p
                    break
            
            if selected_path:
                self.model = YOLO(selected_path)
                self.yolo_available = True
                print(f"YOLOv8 successfully loaded from: {selected_path}")
            else:
                # Attempt default load (will download)
                self.model = YOLO("yolov8n.pt")
                self.yolo_available = True
                print("YOLOv8 initialized with default yolov8n.pt")
        except Exception as e:
            print(f"Warning: Failed to load YOLOv8 model: {e}. Running in simulation mode.")
            self.model = None
            self.yolo_available = False

    def get_density_category(self, count: int) -> str:
        if count < 100:
            return "Low"
        elif count <= 500:
            return "Medium"
        elif count <= 2000:
            return "High"
        else:
            return "Extreme"

    def update_resources(self, base_congestion: str, crowd_count: int, priority: str = "Low", requires_road_closure: bool = False) -> dict:
        """
        Integrates crowd count into:
        - Congestion prediction updates
        - Police deployments
        - Barricades cordons
        """
        density = self.get_density_category(crowd_count)
        
        congestion_rank = {"Low": 1, "Medium": 2, "High": 3, "Extreme": 4}
        crowd_congestion_map = {
            "Low": "Low",
            "Medium": "Medium",
            "High": "High",
            "Extreme": "Extreme"
        }
        
        base_rank = congestion_rank.get(base_congestion, 1)
        crowd_rank = congestion_rank.get(crowd_congestion_map[density], 1)
        updated_rank = max(base_rank, crowd_rank)
        
        rank_to_class = {1: "Low", 2: "Medium", 3: "High", 4: "Extreme"}
        updated_congestion = rank_to_class[updated_rank]
        
        # Calculate Police Recommendations
        police_base = {"Low": 2, "Medium": 4, "High": 8, "Extreme": 15}
        police_req = police_base.get(updated_congestion, 2)
        
        if priority.upper() == "HIGH":
            police_req += 2
        if requires_road_closure:
            police_req += 4
            
        if density == "Medium":
            police_req += 3
        elif density == "High":
            police_req += 6
        elif density == "Extreme":
            police_req += 12
            
        max_police = 40 if density in ["High", "Extreme"] else 20
        police_req = min(max_police, police_req)
        
        # Calculate Barricade Recommendations
        barricade_base = {"Low": 2, "Medium": 6, "High": 12, "Extreme": 20}
        barricades_req = barricade_base.get(updated_congestion, 2)
        
        if requires_road_closure:
            barricades_req += 10
            
        if density == "Medium":
            barricades_req += 4
        elif density == "High":
            barricades_req += 8
        elif density == "Extreme":
            barricades_req += 16
            
        max_barricades = 50 if density in ["High", "Extreme"] else 30
        barricades_req = min(max_barricades, barricades_req)
        
        return {
            "crowd_count": crowd_count,
            "crowd_density": density,
            "base_congestion": base_congestion,
            "updated_congestion": updated_congestion,
            "police_recommended": police_req,
            "barricades_recommended": barricades_req
        }

    def detect_image_bytes(self, img_bytes: bytes, confidence: float = None) -> tuple:
        """
        Loads image bytes and runs adaptive SAHI inference or simulation.
        Returns: (annotated_image_bytes, count)
        """
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            # Fallback to a mock colored grid
            img = np.ones((400, 600, 3), dtype=np.uint8) * 200
            
        if not self.yolo_available:
            return self._simulate_detection(img)
            
        img_h, img_w, _ = img.shape
        
        # Fast first pass to estimate baseline density
        first_pass_res = self.model.predict(img, conf=0.15, imgsz=640, classes=[0], verbose=False)
        base_count = len(first_pass_res[0].boxes) if len(first_pass_res) > 0 else 0
        
        # Adaptive thresholds and slicing grid
        if confidence is None:
            if base_count < 12:
                conf_thresh = 0.20
                nms_iou = 0.40
                min_box_size = 15
                grid_size = 0
            elif base_count < 30:
                conf_thresh = 0.10
                nms_iou = 0.45
                min_box_size = 10
                grid_size = 2
            else:
                conf_thresh = 0.02
                nms_iou = 0.60
                min_box_size = 4
                grid_size = 4
        else:
            conf_thresh = confidence
            nms_iou = 0.50
            min_box_size = 8
            grid_size = 3
            
        candidate_boxes = []
        candidate_scores = []
        
        # Full frame base resolution run
        base_imgsz = max(640, min(1280, max(img_h, img_w)))
        base_imgsz = (base_imgsz // 32) * 32
        
        results_full = self.model.predict(img, conf=conf_thresh, imgsz=base_imgsz, classes=[0], verbose=False)
        if len(results_full) > 0:
            for box in results_full[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                if (x2 - x1) >= min_box_size and (y2 - y1) >= min_box_size:
                    candidate_boxes.append([x1, y1, x2, y2])
                    candidate_scores.append(conf)
                    
        # Apply SAHI slicing
        if grid_size > 0 and (img_w >= 800 or img_h >= 800):
            if grid_size == 2:
                slice_w = int(img_w * 0.55)
                slice_h = int(img_h * 0.55)
                slices = [
                    (0, 0, slice_w, slice_h),
                    (img_w - slice_w, 0, img_w, slice_h),
                    (0, img_h - slice_h, slice_w, img_h),
                    (img_w - slice_w, img_h - slice_h, img_w, img_h)
                ]
                crop_imgsz = 800
            else: # grid_size >= 3
                slice_w = int(img_w * 0.30)
                slice_h = int(img_h * 0.30)
                x_coords = [0, int(img_w * 0.23), int(img_w * 0.46), img_w - slice_w]
                y_coords = [0, int(img_h * 0.23), int(img_h * 0.46), img_h - slice_h]
                slices = [(xc, yc, xc + slice_w, yc + slice_h) for yc in y_coords for xc in x_coords]
                crop_imgsz = 1024
                
            for sx1, sy1, sx2, sy2 in slices:
                crop = img[sy1:sy2, sx1:sx2]
                res_crop = self.model.predict(crop, conf=conf_thresh, imgsz=crop_imgsz, classes=[0], verbose=False)
                if len(res_crop) > 0:
                    for box in res_crop[0].boxes:
                        cx1, cy1, cx2, cy2 = map(int, box.xyxy[0].tolist())
                        conf = float(box.conf[0])
                        gx1, gy1 = cx1 + sx1, cy1 + sy1
                        gx2, gy2 = cx2 + sx1, cy2 + sy1
                        if (gx2 - gx1) >= min_box_size and (gy2 - gy1) >= min_box_size:
                            candidate_boxes.append([gx1, gy1, gx2, gy2])
                            candidate_scores.append(conf)
                            
        # NMS Deduplication
        count = 0
        annotated_img = img.copy()
        if len(candidate_boxes) > 0:
            keep = self._nms_numpy(candidate_boxes, candidate_scores, iou_threshold=nms_iou)
            for idx in keep:
                x1, y1, x2, y2 = candidate_boxes[idx]
                conf = candidate_scores[idx]
                cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                count += 1
                
        _, encoded_img = cv2.imencode('.jpg', annotated_img)
        return encoded_img.tobytes(), count

    def _nms_numpy(self, boxes, scores, iou_threshold=0.45):
        if len(boxes) == 0:
            return []
        boxes, scores = np.array(boxes), np.array(scores)
        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
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
            w, h = np.maximum(0.0, xx2 - xx1), np.maximum(0.0, yy2 - yy1)
            inter = w * h
            ovr = inter / (areas[i] + areas[order[1:]] - inter)
            inds = np.where(ovr <= iou_threshold)[0]
            order = order[inds + 1]
        return keep

    def _simulate_detection(self, img) -> tuple:
        h, w, _ = img.shape
        annotated_img = img.copy()
        np.random.seed(int(time.time()) % 1000)
        sim_count = np.random.randint(15, 380)
        
        # Draw some mock rectangles
        draw_count = min(sim_count, 35)
        for _ in range(draw_count):
            bw = np.random.randint(15, 60)
            bh = np.random.randint(40, 120)
            bx1 = np.random.randint(0, w - bw)
            by1 = np.random.randint(0, h - bh)
            bx2 = bx1 + bw
            by2 = by1 + bh
            cv2.rectangle(annotated_img, (bx1, by1), (bx2, by2), (0, 255, 0), 2)
            
        _, encoded_img = cv2.imencode('.jpg', annotated_img)
        return encoded_img.tobytes(), sim_count

crowd_service = CrowdService()
