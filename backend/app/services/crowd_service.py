import os
import cv2
import time
import numpy as np
import torch
from app.core.config import settings

# Monkey patch torch.load to bypass weights_only check in PyTorch 2.6+ for YOLOv8 model loading
try:
    _original_load = torch.load
    def _patched_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return _original_load(*args, **kwargs)
    torch.load = _patched_load
except Exception as e:
    print(f"Torch load monkey patch warning: {e}")

CLASS_MAP = {
    0: {"name": "Person", "color": (0, 0, 255)},        # BGR Red
    1: {"name": "Bicycle", "color": (255, 0, 0)},       # BGR Blue
    2: {"name": "Car", "color": (0, 215, 255)},         # BGR Gold/Amber
    3: {"name": "Motorcycle", "color": (255, 0, 0)},    # BGR Blue
    5: {"name": "Bus", "color": (0, 215, 255)},         # BGR Gold/Amber
    7: {"name": "Truck", "color": (0, 215, 255)}        # BGR Gold/Amber
}

class CrowdService:
    def __init__(self):
        self.model = None
        self.yolo_available = False
        self.load_model()

    def load_model(self):
        try:
            from ultralytics import YOLO
            # Find the model in the workspace - prioritize yolov8m.pt for high accuracy crowd counting
            paths_to_check = [
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "yolov8m.pt"),
                os.path.join(os.path.dirname(__file__), "..", "..", "yolov8m.pt"),
                settings.YOLO_MODEL_PATH,
                os.path.join(os.path.dirname(__file__), "..", "..", "yolov8n.pt"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "yolov8n.pt"),
            ]
            
            selected_path = None
            for p in paths_to_check:
                if p and os.path.exists(p):
                    selected_path = p
                    break
            
            if selected_path:
                self.model = YOLO(selected_path)
                self.yolo_available = True
                print(f"YOLOv8 successfully loaded from: {selected_path}")
            else:
                # Attempt default load (will download)
                self.model = YOLO("yolov8m.pt")
                self.yolo_available = True
                print("YOLOv8 initialized with default yolov8m.pt")
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
        
        # Fast first pass to estimate baseline density of both people and vehicles
        first_pass_res = self.model.predict(img, conf=0.15, imgsz=640, classes=[0, 1, 2, 3, 5, 7], verbose=False)
        base_count = len(first_pass_res[0].boxes) if len(first_pass_res) > 0 else 0
        
        # Adaptive thresholds and slicing grid - high-sensitivity for dense crowd counting
        if confidence is None:
            if base_count < 5:
                conf_thresh = 0.20
                nms_iou = 0.40
                min_box_size = 15
                grid_size = 0
            elif base_count < 10:
                conf_thresh = 0.08
                nms_iou = 0.45
                min_box_size = 10
                grid_size = 2
            else:
                conf_thresh = 0.02
                nms_iou = 0.55
                min_box_size = 4
                grid_size = 4
        else:
            conf_thresh = confidence
            nms_iou = 0.50
            min_box_size = 6
            grid_size = 4
            
        candidate_boxes = []
        candidate_scores = []
        candidate_classes = []
        
        # Full frame base resolution run
        base_imgsz = max(640, min(1280, max(img_h, img_w)))
        base_imgsz = (base_imgsz // 32) * 32
        
        results_full = self.model.predict(img, conf=conf_thresh, imgsz=base_imgsz, classes=[0, 1, 2, 3, 5, 7], verbose=False)
        if len(results_full) > 0:
            for box in results_full[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                det_conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                if (x2 - x1) >= min_box_size and (y2 - y1) >= min_box_size:
                    candidate_boxes.append([x1, y1, x2, y2])
                    candidate_scores.append(det_conf)
                    candidate_classes.append(cls_id)
                    
        # Apply SAHI slicing
        if grid_size > 0 and (img_w >= 600 or img_h >= 600):
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
                res_crop = self.model.predict(crop, conf=conf_thresh, imgsz=crop_imgsz, classes=[0, 1, 2, 3, 5, 7], verbose=False)
                if len(res_crop) > 0:
                    for box in res_crop[0].boxes:
                        cx1, cy1, cx2, cy2 = map(int, box.xyxy[0].tolist())
                        det_conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        gx1, gy1 = cx1 + sx1, cy1 + sy1
                        gx2, gy2 = cx2 + sx1, cy2 + sy1
                        if (gx2 - gx1) >= min_box_size and (gy2 - gy1) >= min_box_size:
                            candidate_boxes.append([gx1, gy1, gx2, gy2])
                            candidate_scores.append(det_conf)
                            candidate_classes.append(cls_id)
                            
        # NMS Deduplication
        count = 0
        annotated_img = img.copy()
        if len(candidate_boxes) > 0:
            keep = self._nms_numpy(candidate_boxes, candidate_scores, iou_threshold=nms_iou)
            for idx in keep:
                x1, y1, x2, y2 = candidate_boxes[idx]
                det_conf = candidate_scores[idx]
                cls_id = candidate_classes[idx]
                
                meta = CLASS_MAP.get(cls_id, {"name": "Object", "color": (0, 255, 0)})
                label = f"{meta['name']} ({det_conf:.2f})"
                color = meta["color"]
                
                # Draw bounding box
                cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)
                # Add label tag with class-specific color background
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
                cv2.rectangle(annotated_img, (x1, max(y1 - text_h - 6, 0)), (x1 + text_w + 4, max(y1, text_h + 6)), color, -1)
                cv2.putText(annotated_img, label, (x1 + 2, max(y1 - 4, text_h + 2)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
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
        sim_count = np.random.randint(15, 85)
        
        # Draw bounding boxes for simulated verified persons and vehicles
        draw_count = min(sim_count, 35)
        for i in range(draw_count):
            bw = np.random.randint(20, 65)
            bh = np.random.randint(35, 100)
            bx1 = np.random.randint(0, w - bw)
            by1 = np.random.randint(0, h - bh)
            bx2 = bx1 + bw
            by2 = by1 + bh
            
            p = np.random.rand()
            if p < 0.25:
                cls_id = 0 # Person
            elif p < 0.85:
                cls_id = 2 # Car
            else:
                cls_id = 1 # Bicycle / two-wheelers
                
            meta = CLASS_MAP.get(cls_id, {"name": "Object", "color": (0, 255, 0)})
            label = f"SIM {meta['name']}"
            color = meta["color"]
            
            cv2.rectangle(annotated_img, (bx1, by1), (bx2, by2), color, 2)
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.3, 1)
            cv2.rectangle(annotated_img, (bx1, max(by1 - text_h - 6, 0)), (bx1 + text_w + 4, max(by1, text_h + 6)), color, -1)
            cv2.putText(annotated_img, label, (bx1 + 2, max(by1 - 4, text_h + 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
            
        _, encoded_img = cv2.imencode('.jpg', annotated_img)
        return encoded_img.tobytes(), sim_count

    def process_video_frames(self, video_path: str, sample_every: int = -1,
                             confidence: float = None, min_box_size: int = 8,
                             pace_fps: bool = False, render_frames: bool = True):
        """
        Generator that processes a video file frame-by-frame with YOLO person detection.
        Yields per-frame results for real-time streaming.

        Args:
            video_path: Path to the video file on disk.
            sample_every: Run detection every Nth frame (skip others for speed). If -1, dynamically defaults to video FPS (second-by-second).
            confidence: Override confidence threshold. None = adaptive.
            min_box_size: Minimum bounding box dimension to accept.
            pace_fps: Pace the yield of each frame according to the video's FPS.

        Yields:
            dict with: frame_idx, headcount, density, annotated_frame_bytes, is_last
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Video file not found or unreadable: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        vid_fps = int(cap.get(cv2.CAP_PROP_FPS))
        if vid_fps == 0:
            vid_fps = 24
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if sample_every == -1 or sample_every is None:
            sample_every = vid_fps

        frame_idx = 0
        last_count = 0
        last_annotated_bytes = None
        per_frame_counts = []
        target_frame_time = 1.0 / vid_fps

        last_boxes = []

        while cap.isOpened():
            start_time = time.time()
            ret, frame = cap.read()
            if not ret:
                break

            is_sample_frame = (frame_idx % sample_every == 0)

            if is_sample_frame:
                if self.yolo_available and self.model is not None:
                    # Run YOLO detection on this frame
                    annotated_frame, headcount, last_boxes = self._detect_single_frame(
                        frame, confidence=confidence, min_box_size=min_box_size
                    )
                else:
                    # Simulation fallback
                    annotated_frame, headcount = self._simulate_frame_detection(frame, frame_idx)
                    last_boxes = []
                last_count = headcount
            else:
                # Skipped frame: draw the cached boxes from the last sampled frame on the current frame
                if self.yolo_available and self.model is not None:
                    annotated_frame = self._draw_cached_boxes(frame, last_boxes)
                else:
                    # Simulation fallback
                    annotated_frame, _ = self._simulate_frame_detection(frame, frame_idx)

            if render_frames:
                # Downscale the output frame for highly optimized and smooth WebSocket transmission
                # preserving the aspect ratio. Target width is 640px.
                max_width = 640
                if width > max_width:
                    scale = max_width / width
                    target_height = int(height * scale)
                    web_frame = cv2.resize(annotated_frame, (max_width, target_height), interpolation=cv2.INTER_AREA)
                else:
                    web_frame = annotated_frame

                _, encoded = cv2.imencode('.jpg', web_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                last_annotated_bytes = encoded.tobytes()
            else:
                last_annotated_bytes = None

            per_frame_counts.append(last_count)
            density = self.get_density_category(last_count)

            yield {
                "frame_idx": frame_idx,
                "total_frames": total_frames,
                "headcount": last_count,
                "density": density,
                "fps": vid_fps,
                "width": width,
                "height": height,
                "annotated_frame_bytes": last_annotated_bytes,
                "is_last": False
            }

            frame_idx += 1

            if pace_fps:
                elapsed = time.time() - start_time
                sleep_time = target_frame_time - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        cap.release()

        # Final summary
        peak = max(per_frame_counts) if per_frame_counts else 0
        avg = int(np.mean(per_frame_counts)) if per_frame_counts else 0

        yield {
            "frame_idx": frame_idx,
            "total_frames": total_frames,
            "headcount": last_count,
            "density": self.get_density_category(avg),
            "fps": vid_fps,
            "width": width,
            "height": height,
            "annotated_frame_bytes": None,
            "is_last": True,
            "summary": {
                "total_frames_processed": frame_idx,
                "peak_headcount": peak,
                "average_headcount": avg,
                "crowd_density": self.get_density_category(avg),
                "per_frame_counts": per_frame_counts
            }
        }

    def process_video_complete(self, video_path: str, sample_every: int = 3,
                               confidence: float = None) -> dict:
        """
        Non-streaming wrapper: processes entire video and returns summary + annotated frames.
        """
        frames_data = []
        summary = None
        per_frame_counts = []

        for result in self.process_video_frames(video_path, sample_every=sample_every,
                                                confidence=confidence, render_frames=False):
            if result["is_last"]:
                summary = result.get("summary", {})
            else:
                per_frame_counts.append(result["headcount"])
                if result["annotated_frame_bytes"] is not None:
                    frames_data.append({
                        "frame_idx": result["frame_idx"],
                        "headcount": result["headcount"],
                    })

        if summary is None:
            summary = {
                "total_frames_processed": len(per_frame_counts),
                "peak_headcount": max(per_frame_counts) if per_frame_counts else 0,
                "average_headcount": int(np.mean(per_frame_counts)) if per_frame_counts else 0,
                "crowd_density": self.get_density_category(
                    int(np.mean(per_frame_counts)) if per_frame_counts else 0
                ),
                "per_frame_counts": per_frame_counts
            }

        return summary

    def _detect_single_frame(self, frame, confidence: float = None, min_box_size: int = 8):
        """
        Runs YOLO person and vehicle detection on a single video frame. Optimized for real-time
        performance by running a single high-resolution inference with adaptive thresholds.
        Returns (annotated_frame, headcount, detected_boxes).
        """
        img_h, img_w = frame.shape[:2]
        
        # 1. First pass at 640px to assess basic density (both people and vehicles)
        first_pass_res = self.model.predict(frame, conf=0.15, imgsz=640, classes=[0, 1, 2, 3, 5, 7], verbose=False)
        base_count = len(first_pass_res[0].boxes) if len(first_pass_res) > 0 else 0
        
        # 2. Adaptive thresholding based on estimated density
        if confidence is None:
            if base_count < 5:
                conf_thresh = 0.15
                mbs = 12
                # Standard resolution for light scenes
                base_imgsz = 640
            elif base_count < 15:
                conf_thresh = 0.08
                mbs = 8
                # Moderate upscale
                base_imgsz = 800
            else:
                conf_thresh = 0.04
                mbs = 4
                # High resolution upscale to detect small objects without slicing delay
                base_imgsz = 1024
        else:
            conf_thresh = confidence
            mbs = min_box_size
            base_imgsz = 800
            
        base_imgsz = (base_imgsz // 32) * 32
        
        # 3. Single-pass high-resolution inference (Fast & Accurate!)
        results = self.model.predict(frame, conf=conf_thresh, imgsz=base_imgsz, classes=[0, 1, 2, 3, 5, 7], verbose=False)
        
        annotated = frame.copy()
        count = 0
        detected_boxes = []

        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                det_conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                bw, bh = x2 - x1, y2 - y1

                if bw < mbs or bh < mbs:
                    continue

                count += 1
                detected_boxes.append((x1, y1, x2, y2, det_conf, cls_id))
                
                meta = CLASS_MAP.get(cls_id, {"name": "Object", "color": (0, 255, 0)})
                label = f"{meta['name']} ({det_conf:.2f})"
                color = meta["color"]

                # Draw bounding box and label
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
                cv2.rectangle(annotated, (x1, max(y1 - text_h - 6, 0)),
                              (x1 + text_w + 4, max(y1, text_h + 6)), color, -1)
                cv2.putText(annotated, label, (x1 + 2, max(y1 - 4, text_h + 2)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

        # HUD overlay
        cv2.rectangle(annotated, (10, 10), (360, 50), (15, 23, 42), -1)
        cv2.putText(annotated, f"OBJECTS DETECTED: {count} | SURVEILLANCE ACTIVE",
                    (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)

        return annotated, count, detected_boxes

    def _draw_cached_boxes(self, frame, boxes):
        """
        Draws cached bounding boxes from the last sampled frame on the current frame.
        """
        annotated = frame.copy()
        count = len(boxes)

        for box_data in boxes:
            # Handle cases where box_data might be a 5-tuple (old version) or 6-tuple (new version)
            if len(box_data) == 6:
                x1, y1, x2, y2, det_conf, cls_id = box_data
            else:
                x1, y1, x2, y2, det_conf = box_data
                cls_id = 0 # Default to person class

            meta = CLASS_MAP.get(cls_id, {"name": "Object", "color": (0, 255, 0)})
            label = f"{meta['name']} ({det_conf:.2f})"
            color = meta["color"]

            # Draw bounding box and label
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
            cv2.rectangle(annotated, (x1, max(y1 - text_h - 6, 0)),
                          (x1 + text_w + 4, max(y1, text_h + 6)), color, -1)
            cv2.putText(annotated, label, (x1 + 2, max(y1 - 4, text_h + 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

        # HUD overlay
        cv2.rectangle(annotated, (10, 10), (360, 50), (15, 23, 42), -1)
        cv2.putText(annotated, f"OBJECTS DETECTED: {count} | SURVEILLANCE ACTIVE",
                    (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)

        return annotated

    def _simulate_frame_detection(self, frame, frame_idx: int):
        """
        Simulation fallback for video frame detection when YOLO is unavailable.
        """
        h, w = frame.shape[:2]
        annotated = frame.copy()
        np.random.seed((frame_idx * 7 + int(time.time())) % 10000)
        sim_count = np.random.randint(8, 45)

        draw_count = min(sim_count, 20)
        for _ in range(draw_count):
            bw = np.random.randint(15, 50)
            bh = np.random.randint(30, 90)
            bx1 = np.random.randint(0, max(1, w - bw))
            by1 = np.random.randint(0, max(1, h - bh))
            bx2, by2 = bx1 + bw, by1 + bh
            
            p = np.random.rand()
            if p < 0.25:
                cls_id = 0 # Person
            elif p < 0.85:
                cls_id = 2 # Car
            else:
                cls_id = 1 # Bicycle
                
            meta = CLASS_MAP.get(cls_id, {"name": "Object", "color": (0, 255, 0)})
            label = f"SIM {meta['name']}"
            color = meta["color"]

            cv2.rectangle(annotated, (bx1, by1), (bx2, by2), color, 2)
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.3, 1)
            cv2.rectangle(annotated, (bx1, max(by1 - text_h - 6, 0)),
                          (bx1 + text_w + 4, max(by1, text_h + 6)), color, -1)
            cv2.putText(annotated, label, (bx1 + 2, max(by1 - 4, text_h + 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

        cv2.rectangle(annotated, (10, 10), (360, 50), (15, 23, 42), -1)
        cv2.putText(annotated, f"OBJECTS DETECTED: {sim_count} | SIM MODE",
                    (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)

        return annotated, sim_count

crowd_service = CrowdService()
