import cv2
import numpy as np
from ultralytics import YOLO

def nms_numpy(boxes, scores, iou_threshold=0.45):
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

def run_sahi():
    img_path = "benchmark_data/blr_rally_cctv.png"
    img = cv2.imread(img_path)
    h, w, _ = img.shape
    print(f"Loaded image: {w}x{h}")
    
    model = YOLO("yolov8m.pt")
    
    # 1. Full Image Inference
    res_full = model.predict(img, conf=0.05, imgsz=1280, classes=[0], verbose=False)[0]
    all_boxes = []
    all_scores = []
    
    for box in res_full.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        all_boxes.append([x1, y1, x2, y2])
        all_scores.append(float(box.conf[0]))
        
    print(f"Full-frame YOLOv8m detections: {len(all_boxes)}")
    
    # 2. Slice-based Inference (2x2 overlapping grid)
    # Define slice sizes
    slice_w = int(w * 0.55)
    slice_h = int(h * 0.55)
    
    # Overlap coordinates (top-left, top-right, bottom-left, bottom-right)
    slices = [
        (0, 0, slice_w, slice_h), # Top-Left
        (w - slice_w, 0, w, slice_h), # Top-Right
        (0, h - slice_h, slice_w, h), # Bottom-Left
        (w - slice_w, h - slice_h, w, h) # Bottom-Right
    ]
    
    for i, (x1, y1, x2, y2) in enumerate(slices):
        crop = img[y1:y2, x1:x2]
        res_crop = model.predict(crop, conf=0.05, imgsz=800, classes=[0], verbose=False)[0]
        
        for box in res_crop.boxes:
            cx1, cy1, cx2, cy2 = map(int, box.xyxy[0].tolist())
            # Translate back to global coordinates
            gx1, gy1 = cx1 + x1, cy1 + y1
            gx2, gy2 = cx2 + x1, cy2 + y1
            
            all_boxes.append([gx1, gy1, gx2, gy2])
            all_scores.append(float(box.conf[0]))
            
    print(f"Total detections after combining slices: {len(all_boxes)}")
    
    # 3. Apply Global NMS to prune duplicates
    keep = nms_numpy(all_boxes, all_scores, iou_threshold=0.35)
    print(f"Detections after NMS deduplication (SAHI Count): {len(keep)}")

if __name__ == "__main__":
    run_sahi()
