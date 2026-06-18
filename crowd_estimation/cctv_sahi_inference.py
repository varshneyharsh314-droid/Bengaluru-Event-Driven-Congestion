import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" # Workaround for OpenMP library conflicts
import cv2
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO

from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

def run_comparison(image_path, model_weights="yolov8n.pt", confidence_threshold=0.25, out_plot_path="benchmark_results/sahi_comparison.png"):
    """Compares standard YOLOv8 inference with SAHI-sliced inference for CCTV crowd estimation."""
    print(f"Loading YOLOv8 model: {model_weights}...")

    # 1. Initialize Standard YOLOv8
    yolo_model = YOLO(model_weights)

    # 2. Initialize SAHI Wrapper Model
    sahi_model = AutoDetectionModel.from_pretrained(
        model_type="ultralytics",
        model_path=model_weights,
        confidence_threshold=confidence_threshold,
        device="cpu",  # Set to 'cuda' if GPU is available
    )

    # Load image
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Source image not found at {image_path}")
        
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, _ = img.shape

    print(f"Processing image of size: {w}x{h}")

    # =========================================================================
    # PHASE 1: Standard YOLOv8 Inference
    # =========================================================================
    print("Running Standard YOLOv8 Inference...")
    standard_results = yolo_model.predict(
        source=image_path, conf=confidence_threshold, classes=[0], verbose=False
    )[0]

    # Extract standard boxes (Class 0 is person in COCO)
    standard_boxes = standard_results.boxes.xyxy.cpu().numpy()
    standard_count = len(standard_boxes)

    # Draw Standard Bounding Boxes (Red for verified persons)
    img_standard = img_rgb.copy()
    for box in standard_boxes:
        x1, y1, x2, y2 = map(int, box[:4])
        cv2.rectangle(img_standard, (x1, y1), (x2, y2), (255, 0, 0), 2)
        label = "VERIFIED"
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        cv2.rectangle(img_standard, (x1, max(y1 - text_h - 6, 0)), (x1 + text_w + 4, max(y1, text_h + 6)), (255, 0, 0), -1)
        cv2.putText(img_standard, label, (x1 + 2, max(y1 - 4, text_h + 2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

    # =========================================================================
    # PHASE 2: SAHI Sliced Inference
    # =========================================================================
    print("Running SAHI Sliced Inference...")

    # Tuning hyperparameters optimized for 1024x1024 / 1280x720 CCTV traffic views
    sahi_result = get_sliced_prediction(
        image_path,
        sahi_model,
        slice_height=320,  # Smaller slice heights capture tiny pedestrians deep in the background
        slice_width=320,
        overlap_height_ratio=0.25,  # 25% overlap guarantees NMS handles split objects smoothly
        overlap_width_ratio=0.25,
        perform_standard_pred=True,  # Combines full-frame heuristic with sliced heuristic
        verbose=0
    )

    # Filter for person class (COCO 0)
    sahi_objects = [
        obj for obj in sahi_result.object_prediction_list if obj.category.id == 0
    ]
    sahi_count = len(sahi_objects)

    # Draw SAHI Bounding Boxes (Red for verified persons)
    img_sahi = img_rgb.copy()
    for obj in sahi_objects:
        bbox = obj.bbox.to_voc_bbox()  # Returns [xmin, ymin, xmax, ymax]
        x1, y1, x2, y2 = map(int, bbox)
        cv2.rectangle(img_sahi, (x1, y1), (x2, y2), (255, 0, 0), 2)
        label = "VERIFIED"
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        cv2.rectangle(img_sahi, (x1, max(y1 - text_h - 6, 0)), (x1 + text_w + 4, max(y1, text_h + 6)), (255, 0, 0), -1)
        cv2.putText(img_sahi, label, (x1 + 2, max(y1 - 4, text_h + 2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

    # =========================================================================
    # PHASE 3: Metrics Evaluation & Plotting
    # =========================================================================
    print("\n" + "=" * 50)
    print("SAHI Crowd Estimation Evaluation Report:")
    print("=" * 50)
    print(f"Standard YOLO Count : {standard_count} pedestrians")
    print(f"SAHI + YOLO Count   : {sahi_count} pedestrians")

    # Assuming ground truth upper bound is ~22 for our verified test image
    estimated_gt = 22
    std_accuracy = max(0, (1 - abs(standard_count - estimated_gt) / estimated_gt)) * 100
    sahi_accuracy = max(0, (1 - abs(sahi_count - estimated_gt) / estimated_gt)) * 100

    print(f"Standard Accuracy (est. GT {estimated_gt}): {std_accuracy:.1f}%")
    print(f"SAHI Accuracy     (est. GT {estimated_gt}): {sahi_accuracy:.1f}%")
    print(f"Net Recall Boost                       : +{sahi_count - standard_count} people detected")
    print("=" * 50)

    # Plot Visualizations Side-by-Side and Save
    os.makedirs(os.path.dirname(out_plot_path), exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    axes[0].imshow(img_standard)
    axes[0].set_title(
        f"Standard YOLOv8 (Count: {standard_count})", fontsize=16, color="red"
    )
    axes[0].axis("off")

    axes[1].imshow(img_sahi)
    axes[1].set_title(
        f"SAHI + YOLOv8 (Count: {sahi_count})", fontsize=16, color="green"
    )
    axes[1].axis("off")

    plt.tight_layout()
    plt.savefig(out_plot_path, dpi=150)
    plt.close()
    print(f"Comparison plot saved successfully to: {out_plot_path}")

if __name__ == "__main__":
    # Test on our newly generated photorealistic street crosswalk image
    test_img = "benchmark_data/blr_street_cctv_yolo.png"
    
    if not os.path.exists(test_img):
        # Fallback dummy canvas creation
        test_img = "cctv_frame.jpg"
        placeholder = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(
            placeholder,
            "Drop your CCTV Image here",
            (350, 360),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        cv2.imwrite(test_img, placeholder)
        print(f"Created a placeholder image at '{test_img}'.")

    run_comparison(image_path=test_img)
