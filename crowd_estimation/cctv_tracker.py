import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import cv2
import numpy as np
from ultralytics import YOLO

class CCTVPedestrianTracker:
    """
    Advanced CCTV Pedestrian Tracker & Density Estimator.
    Combines YOLOv8m/l, high-resolution inference (imgsz=1280),
    and ByteTrack to achieve tight bounding boxes and stable counts.
    """
    def __init__(self, model_name="yolov8m.pt"):
        """
        Initializes the tracker with medium (yolov8m) or large (yolov8l) model.
        """
        self.model_name = model_name
        self.model = YOLO(model_name)
        print(f"Loaded high-accuracy model: {model_name}")

    def track_and_count(self, video_path, out_video_path="benchmark_results/tracked_cctv.mp4",
                        imgsz=1280, conf=0.35, iou=0.40, min_box_size=(20, 20)):
        """
        Tracks pedestrians across video frames using ByteTrack and filters results.
        
        Args:
            video_path (str): Path to input CCTV video.
            out_video_path (str): Path to save annotated output video.
            imgsz (int): Higher resolution scale for inference (keeps small details).
            conf (float): Higher confidence threshold to block false positives.
            iou (float): Lower IoU threshold for tighter duplicate box merging.
            min_box_size (tuple): Minimum width/height in pixels to ignore noise.
            
        Returns:
            dict: Containing total unique pedestrians tracked, current frame counts, and density stats.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Video file not found at {video_path}")
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps == 0:
            fps = 24
            
        os.makedirs(os.path.dirname(out_video_path), exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_video_path, fourcc, fps, (width, height))
        
        unique_track_ids = set()
        frame_idx = 0
        frame_counts = []
        
        print(f"Starting CCTV tracking: {video_path} -> {out_video_path}")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Run YOLOv8 tracking with ByteTrack
            # class 0 is person, persist=True keeps tracker states
            results = self.model.track(
                source=frame,
                imgsz=imgsz,
                conf=conf,
                iou=iou,
                classes=[0],
                tracker="bytetrack.yaml",
                persist=True,
                verbose=False
            )
            
            current_frame_count = 0
            annotated_frame = frame.copy()
            
            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                
                # Check if tracking IDs are assigned
                if boxes.id is not None:
                    track_ids = boxes.id.int().cpu().tolist()
                    xyxy_boxes = boxes.xyxy.int().cpu().tolist()
                    confidences = boxes.conf.cpu().tolist()
                    
                    for box, track_id, score in zip(xyxy_boxes, track_ids, confidences):
                        x1, y1, x2, y2 = box
                        box_w = x2 - x1
                        box_h = y2 - y1
                        
                        # Filter out tiny detections (pixel noise in deep background)
                        if box_w < min_box_size[0] or box_h < min_box_size[1]:
                            continue
                            
                        # Log unique pedestrians over the entire video sequence
                        unique_track_ids.add(track_id)
                        current_frame_count += 1
                        
                        # Draw tight bounding boxes & ID labels (Red for verified person tracking)
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        label = f"VERIFIED ID:{track_id} ({score:.2f})"
                        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                        cv2.rectangle(annotated_frame, (x1, max(y1 - text_h - 6, 0)), (x1 + text_w + 4, max(y1, text_h + 6)), (0, 0, 255), -1)
                        cv2.putText(annotated_frame, label, (x1 + 2, max(y1 - 4, text_h + 2)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                else:
                    # Fallback to standard detections if no tracks are active
                    xyxy_boxes = boxes.xyxy.int().cpu().tolist()
                    confidences = boxes.conf.cpu().tolist()
                    for box, score in zip(xyxy_boxes, confidences):
                        x1, y1, x2, y2 = box
                        box_w = x2 - x1
                        box_h = y2 - y1
                        if box_w < min_box_size[0] or box_h < min_box_size[1]:
                            continue
                        current_frame_count += 1
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
            
            frame_counts.append(current_frame_count)
            
            # HUD Overlay
            cv2.rectangle(annotated_frame, (10, 10), (420, 110), (15, 23, 42), -1)
            cv2.putText(annotated_frame, f"Model: {self.model_name.upper()} (imgsz={imgsz})", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            cv2.putText(annotated_frame, f"Tracker: ByteTrack | Conf Threshold: {conf}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
            cv2.putText(annotated_frame, f"Current Frame Count: {current_frame_count}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (74, 222, 128), 1)
            cv2.putText(annotated_frame, f"Cumulative Unique Tracked: {len(unique_track_ids)}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (59, 130, 246), 1)
            
            out.write(annotated_frame)
            frame_idx += 1
            
        cap.release()
        out.release()
        
        peak_count = max(frame_counts) if len(frame_counts) > 0 else 0
        avg_count = int(np.mean(frame_counts)) if len(frame_counts) > 0 else 0
        
        return {
            "total_unique_tracked": len(unique_track_ids),
            "peak_frame_count": peak_count,
            "average_frame_count": avg_count,
            "total_frames_processed": frame_idx,
            "output_path": out_video_path
        }

if __name__ == "__main__":
    # Test on a generated video clip if present
    test_video = "benchmark_data/blr_rally_cctv_video.mp4"
    if os.path.exists(test_video):
        tracker = CCTVPedestrianTracker(model_name="yolov8m.pt")
        res = tracker.track_and_count(test_video, out_video_path="benchmark_results/tracked_cctv_demo.mp4")
        print("\n=== CCTV ByteTrack Test Run ===")
        print(f"Processed Video: {test_video}")
        print(f"Total Frames: {res['total_frames_processed']}")
        print(f"Average Pedestrians per Frame: {res['average_frame_count']}")
        print(f"Peak Pedestrians in Single Frame: {res['peak_frame_count']}")
        print(f"Cumulative Unique People Tracked: {res['total_unique_tracked']}")
        print(f"Output saved at: {res['output_path']}")
        print("===============================\n")
    else:
        print(f"Video {test_video} not found for testing.")
