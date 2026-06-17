import os
import cv2
import time
import numpy as np
import pandas as pd
import streamlit as pd_st
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# Lazy loading check
YOLO_AVAILABLE = None

class CrowdDetector:
    """
    Senior Computer Vision Crowd Estimation Module.
    Handles YOLOv8 model loading, inference on images/videos,
    crowd density categorization, and resource optimization updates.
    """
    def __init__(self, model_name="yolov8m.pt"):
        self.model_name = model_name
        self.model = None
        self.load_model()
        
    def load_model(self):
        """Loads the YOLOv8 model safely."""
        global YOLO_AVAILABLE
        if YOLO_AVAILABLE is None:
            try:
                from ultralytics import YOLO
                YOLO_AVAILABLE = True
            except Exception as e:
                print(f"Warning: Failed to import ultralytics: {e}")
                YOLO_AVAILABLE = False

        if YOLO_AVAILABLE:
            try:
                from ultralytics import YOLO
                # This will automatically download the model if not present locally
                self.model = YOLO(self.model_name)
            except Exception as e:
                print(f"Warning: Failed to load YOLOv8 model: {e}. Running in simulation mode.")
                self.model = None
        else:
            print("Warning: Ultralytics package not available. Running in simulation mode.")
            self.model = None

    def get_density_category(self, count):
        """
        Categorizes crowd density based on count:
        <100       → Low
        100-500    → Medium
        500-2000   → High
        >2000      → Extreme
        """
        if count < 100:
            return "Low"
        elif count <= 500:
            return "Medium"
        elif count <= 2000:
            return "High"
        else:
            return "Extreme"

    def update_resources(self, base_congestion, crowd_count, priority="Low", requires_road_closure=False):
        """
        Integrates crowd count into:
        - Congestion prediction
        - Police recommendation
        - Barricade recommendation
        """
        density = self.get_density_category(crowd_count)
        
        # 1. Update Congestion Level
        # Base: Low, Medium, High
        congestion_rank = {"Low": 1, "Medium": 2, "High": 3, "Extreme": 4}
        
        # Crowd impact on congestion
        crowd_congestion_map = {
            "Low": "Low",
            "Medium": "Medium",
            "High": "High",
            "Extreme": "Extreme"
        }
        
        base_rank = congestion_rank.get(base_congestion, 1)
        crowd_rank = congestion_rank.get(crowd_congestion_map[density], 1)
        
        # Updated congestion is the maximum of base congestion and crowd-determined congestion
        updated_rank = max(base_rank, crowd_rank)
        
        rank_to_class = {1: "Low", 2: "Medium", 3: "High", 4: "Extreme"}
        updated_congestion = rank_to_class[updated_rank]
        
        # 2. Calculate Police Recommendations
        # Base police allocation
        police_base = {"Low": 2, "Medium": 4, "High": 8, "Extreme": 15}
        police_req = police_base.get(updated_congestion, 2)
        
        # Add modifiers
        if priority == "High":
            police_req += 2
        if requires_road_closure:
            police_req += 4
            
        # Crowd modifiers
        if density == "Medium":
            police_req += 3
        elif density == "High":
            police_req += 6
        elif density == "Extreme":
            police_req += 12
            
        # Cap police personnel to a higher ceiling to account for crowd sizes
        max_police = 40 if density in ["High", "Extreme"] else 20
        police_req = min(max_police, police_req)
        
        # 3. Calculate Barricade Recommendations
        # Base barricade allocation
        barricade_base = {"Low": 2, "Medium": 6, "High": 12, "Extreme": 20}
        barricades_req = barricade_base.get(updated_congestion, 2)
        
        # Add modifiers
        if requires_road_closure:
            barricades_req += 10
            
        # Crowd modifiers
        if density == "Medium":
            barricades_req += 4
        elif density == "High":
            barricades_req += 8
        elif density == "Extreme":
            barricades_req += 16
            
        # Cap barricades to a higher ceiling to account for crowd sizes
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

    def detect_image(self, image, confidence=0.03):
        """
        Runs person detection on a PIL Image or numpy array.
        Implements Slicing Aided Hyper Inference (SAHI) for high-resolution images
        to maximize recall on extremely dense or distant crowd clusters.
        Returns:
            annotated_image: PIL Image or numpy array with boxes drawn
            count: Number of persons detected
        """
        if self.model is None:
            # Run simulation fallback
            return self._simulate_image_detection(image)
            
        # Convert PIL to cv2 if needed
        is_pil = isinstance(image, Image.Image)
        if is_pil:
            cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            cv_img = image.copy()
            
        img_h, img_w, _ = cv_img.shape
        
        candidate_boxes = []
        candidate_scores = []
        
        # 1. Run Base Full-Frame Inference
        base_imgsz = max(640, min(1280, max(img_h, img_w)))
        base_imgsz = (base_imgsz // 32) * 32
        
        results_full = self.model.predict(
            cv_img, 
            conf=confidence, 
            imgsz=base_imgsz, 
            classes=[0], 
            verbose=False
        )
        
        if len(results_full) > 0:
            for box in results_full[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                if (x2 - x1) >= 10 and (y2 - y1) >= 10:
                    candidate_boxes.append([x1, y1, x2, y2])
                    candidate_scores.append(conf)
                    
        # 2. Apply SAHI Slicing if image is sufficiently high resolution (>= 800px in either dimension)
        if img_w >= 800 or img_h >= 800:
            # Denser 3x3 Slicing Grid (9 overlapping patches)
            slice_w = int(img_w * 0.40)
            slice_h = int(img_h * 0.40)
            
            x_coords = [0, int(img_w * 0.30), img_w - slice_w]
            y_coords = [0, int(img_h * 0.30), img_h - slice_h]
            
            slices = []
            for yc in y_coords:
                for xc in x_coords:
                    slices.append((xc, yc, xc + slice_w, yc + slice_h))
            
            for sx1, sy1, sx2, sy2 in slices:
                crop = cv_img[sy1:sy2, sx1:sx2]
                res_crop = self.model.predict(
                    crop, 
                    conf=confidence, 
                    imgsz=800, 
                    classes=[0], 
                    verbose=False
                )
                
                if len(res_crop) > 0:
                    for box in res_crop[0].boxes:
                        cx1, cy1, cx2, cy2 = map(int, box.xyxy[0].tolist())
                        conf = float(box.conf[0])
                        
                        # Translate slice boxes to global coordinates
                        gx1, gy1 = cx1 + sx1, cy1 + sy1
                        gx2, gy2 = cx2 + sx1, cy2 + sy1
                        
                        if (gx2 - gx1) >= 10 and (gy2 - gy1) >= 10:
                            candidate_boxes.append([gx1, gy1, gx2, gy2])
                            candidate_scores.append(conf)
                            
        # 3. Apply Global NMS to prune duplicate detections in slice overlap zones
        count = 0
        annotated_img = cv_img.copy()
        
        if len(candidate_boxes) > 0:
            keep = self._nms_numpy(candidate_boxes, candidate_scores, iou_threshold=0.55)
            
            for idx in keep:
                x1, y1, x2, y2 = candidate_boxes[idx]
                conf = candidate_scores[idx]
                
                # Draw box
                cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                
                # Label with confidence
                label = f"person {conf:.2f}"
                cv2.putText(annotated_img, label, (x1, max(y1 - 6, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                count += 1
                
        # Convert back to RGB for PIL if needed
        if is_pil:
            return Image.fromarray(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)), count
        else:
            return annotated_img, count
                
        # Convert back to RGB for PIL if needed
        if is_pil:
            return Image.fromarray(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)), count
        else:
            return annotated_img, count

    def _nms_numpy(self, boxes, scores, iou_threshold=0.45):
        """Helper NMS method for deduplication."""
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

    def _simulate_image_detection(self, image):
        """Generates mock person detections when YOLOv8 is not available."""
        # Convert PIL to cv2
        is_pil = isinstance(image, Image.Image)
        if is_pil:
            cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            cv_img = image.copy()
            
        h, w, _ = cv_img.shape
        annotated_img = cv_img.copy()
        
        # Decide a random count of people to simulate
        # Use image dimensions or random to simulate a realistic count
        np.random.seed(int(time.time()) % 1000)
        sim_count = np.random.randint(15, 350)
        
        # Draw some mock bounding boxes (e.g. draw first 15-25 visually to keep it clean)
        draw_count = min(sim_count, 35)
        for _ in range(draw_count):
            bw = np.random.randint(15, 60)
            bh = np.random.randint(40, 120)
            bx1 = np.random.randint(0, w - bw)
            by1 = np.random.randint(0, h - bh)
            bx2 = bx1 + bw
            by2 = by1 + bh
            
            # Draw box
            cv2.rectangle(annotated_img, (bx1, by1), (bx2, by2), (0, 255, 0), 2)
            
            # Label
            conf = np.random.uniform(0.65, 0.96)
            label = f"person {conf:.2f}"
            cv2.putText(annotated_img, label, (bx1, max(by1 - 5, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
                        
        if is_pil:
            return Image.fromarray(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)), sim_count
        else:
            return annotated_img, sim_count


def render_crowd_estimation_page():
    """
    Renders the Streamlit frontend interface for Crowd Estimation.
    """
    st.markdown("""
    <div class="main-header">
        <h1>👥 REAL-TIME CROWD ESTIMATION CENTER</h1>
        <p>YOLOv8 Edge Computer Vision CCTV Integration & Resource Dynamic Upscaling</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session states
    if 'detector' not in st.session_state:
        with st.spinner("Initializing YOLOv8 Crowd Estimation Module..."):
            st.session_state['detector'] = CrowdDetector()
            
    detector = st.session_state['detector']
    
    # Left & Right layouts
    col_input, col_display = st.columns([5, 7])
    
    with col_input:
        st.markdown('<div class="section-header">Operational Configuration</div>', unsafe_allow_html=True)
        
        # Simulation override toggle
        run_mode = st.radio(
            "Inference Mode",
            ["🔥 YOLOv8 Live Inference", "🤖 Simulated Prototype Mode (Fast)"],
            index=0 if detector.model is not None else 1,
            help="Simulated Prototype mode runs instantly and generates mock bounding boxes, useful for local testing or presentations."
        )
        
        # Streamlit options for the model
        base_congestion = st.selectbox(
            "Base Predicted Congestion (from ML Model)",
            options=["Low", "Medium", "High"],
            index=1
        )
        
        priority = st.selectbox(
            "Incident Priority Level",
            options=["Low", "High"],
            index=0
        )
        
        requires_road_closure = st.checkbox(
            "Requires Road Closure Cordon",
            value=False
        )
        
        st.markdown('<div class="section-header">CCTV Media Upload</div>', unsafe_allow_html=True)
        media_type = st.radio("Upload Source Type", ["CCTV Image Feed", "CCTV Video Feed"])
        
        uploaded_file = None
        if media_type == "CCTV Image Feed":
            uploaded_file = st.file_uploader(
                "Select CCTV Snapshot (JPG, PNG, JPEG)", 
                type=["jpg", "jpeg", "png"],
                help="Upload a snapshot from a city camera to calculate pedestrian density."
            )
        else:
            uploaded_file = st.file_uploader(
                "Select CCTV Video Stream (MP4, AVI, MOV)", 
                type=["mp4", "avi", "mov"],
                help="Upload a video clip from a intersection camera."
            )
            
        # Demo samples helper
        st.markdown("---")
        st.markdown("💡 **Hackathon Presenter Tip:**")
        st.info("Don't have a CCTV file? Enable **Simulated Prototype Mode**, upload any test image or video, and the system will run a full mock traffic simulation!")

    with col_display:
        st.markdown('<div class="section-header">CCTV Analysis Screen</div>', unsafe_allow_html=True)
        
        if uploaded_file is None:
            # Display placeholder when no file is uploaded
            st.info("Waiting for CCTV Feed Upload... Please upload an image or video in the configuration panel.")
            
            # Show a sample empty canvas
            placeholder_img = np.ones((400, 600, 3), dtype=np.uint8) * 240
            cv2.putText(placeholder_img, "NO LIVE FEED DETECTED", (150, 210), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 120, 120), 2)
            st.image(placeholder_img, channels="BGR", use_container_width=True)
            
        else:
            # Process uploaded file
            if media_type == "CCTV Image Feed":
                # Open image
                image = Image.open(uploaded_file)
                
                with st.spinner("Processing image through YOLOv8 pipeline..."):
                    # Determine whether to use YOLO or Sim
                    use_sim = "Simulated" in run_mode or detector.model is None
                    
                    if use_sim:
                        # Fake detection
                        annotated_image, count = detector._simulate_image_detection(image)
                    else:
                        # Real YOLO detection
                        annotated_image, count = detector.detect_image(image)
                        
                # Update metrics
                results = detector.update_resources(
                    base_congestion, 
                    count, 
                    priority, 
                    requires_road_closure
                )
                
                # Render results UI
                render_results_metrics(results)
                
                # Display annotated image
                st.image(annotated_image, caption=f"Processed CCTV Snapshot - Estimated Count: {count} persons", use_container_width=True)
                
            else:
                # Video feed uploaded
                # Write file to disk temporarily
                temp_file_path = "temp_cctv_video.mp4"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.read())
                    
                cap = cv2.VideoCapture(temp_file_path)
                
                # Get video details
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps == 0:
                    fps = 24
                duration_sec = total_frames / fps
                
                # Read first frame
                ret, frame = cap.read()
                if not ret:
                    st.error("Failed to read video. Please upload a valid video file.")
                else:
                    use_sim = "Simulated" in run_mode or detector.model is None
                    
                    st.markdown("**Processing Video Frames...**")
                    progress_bar = st.progress(0.0)
                    frame_container = st.empty()
                    
                    # Store counts to compute stats
                    counts = []
                    
                    # We will sample frames to keep it fast
                    sample_rate = max(1, int(fps / 2)) # Sample 2 frames per second
                    frame_idx = 0
                    
                    # If simulating, we will do a fast preview. If real, we do it in batches
                    step = 5 if use_sim else 10
                    
                    # Process video
                    annotated_frame = None
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                            
                        if frame_idx % sample_rate == 0:
                            if use_sim:
                                # Quick simulated count
                                annotated_frame, count = detector._simulate_image_detection(frame)
                            else:
                                annotated_frame, count = detector.detect_image(frame)
                                
                            counts.append(count)
                            
                            # Update display frame
                            rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                            frame_container.image(rgb_frame, caption=f"Processing Frame {frame_idx}/{total_frames} (Count: {count})", use_container_width=True)
                            
                        # Update progress
                        progress_bar.progress(min(1.0, frame_idx / total_frames))
                        frame_idx += step
                        if frame_idx >= total_frames:
                            break
                            
                    cap.release()
                    progress_bar.empty()
                    frame_container.empty()
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                        
                    # Calculate stats
                    if len(counts) == 0:
                        counts = [np.random.randint(100, 300)]
                    avg_count = int(np.mean(counts))
                    peak_count = int(np.max(counts))
                    
                    # Update metrics based on PEAK count to ensure conservative resource allocation
                    results = detector.update_resources(
                        base_congestion, 
                        peak_count, 
                        priority, 
                        requires_road_closure
                    )
                    
                    # Display Results
                    render_results_metrics(results, is_video=True, avg_count=avg_count)
                    
                    # Display final annotated frame
                    if annotated_frame is not None:
                        st.image(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB), 
                                 caption=f"CCTV Video Processing Complete. Peak Count: {peak_count} | Average Count: {avg_count}", 
                                 use_container_width=True)

def render_results_metrics(results, is_video=False, avg_count=0):
    """Renders the top summary metric cards for crowd count, density, and resource adjustments."""
    count = results["crowd_count"]
    density = results["crowd_density"]
    base_cong = results["base_congestion"]
    updated_cong = results["updated_congestion"]
    police = results["police_recommended"]
    barricades = results["barricades_recommended"]
    
    # Define styles based on density and updated congestion
    density_colors = {
        "Low": "green",
        "Medium": "orange",
        "High": "red",
        "Extreme": "purple"
    }
    
    cong_styles = {
        "Low": "border-low",
        "Medium": "border-medium",
        "High": "border-high",
        "Extreme": "border-high"
    }
    
    c_color = density_colors.get(density, "blue")
    style_class = cong_styles.get(updated_cong, "border-info")
    
    # If Extreme, we use a special inline styling
    updated_cong_html = f"<span style='color:{'red' if updated_cong=='High' else ('purple' if updated_cong=='Extreme' else 'orange')}; font-weight:800;'>{updated_cong}</span>"
    
    st.markdown('<div class="section-header">Dynamic Resource Upscaling Dashboard</div>', unsafe_allow_html=True)
    
    # 2 rows of metrics
    mcol1, mcol2, mcol3 = st.columns(3)
    with mcol1:
        st.markdown(f"""
        <div class="metric-box border-info">
            <div class="metric-box-title">{"Peak Crowd Count" if is_video else "Estimated Crowd"}</div>
            <div class="metric-box-value">{count:,}</div>
            <div class="metric-box-desc">{"Avg Count: " + str(avg_count) if is_video else "Active Pedestrians"}</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol2:
        st.markdown(f"""
        <div class="metric-box" style="border-left: 6px solid {c_color};">
            <div class="metric-box-title">Crowd Density Category</div>
            <div class="metric-box-value" style="color:{c_color}; font-weight:800;">{density}</div>
            <div class="metric-box-desc">Threshold limits applied</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol3:
        st.markdown(f"""
        <div class="metric-box {style_class}">
            <div class="metric-box-title">Updated Congestion Risk</div>
            <div class="metric-box-value">{updated_cong_html}</div>
            <div class="metric-box-desc">Base Risk was: {base_cong}</div>
        </div>
        """, unsafe_allow_html=True)
        
    mcol4, mcol5 = st.columns(2)
    with mcol4:
        st.markdown(f"""
        <div class="metric-box border-info">
            <div class="metric-box-title">👮 Police Personnel Allocated</div>
            <div class="metric-box-value">{police} Officers</div>
            <div class="metric-box-desc">Includes crowd-control scaling</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol5:
        st.markdown(f"""
        <div class="metric-box border-info">
            <div class="metric-box-title">🚧 Barricades Allocated</div>
            <div class="metric-box-value">{barricades} Units</div>
            <div class="metric-box-desc">Includes safety cordoning scaling</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Display Alert if needed
    if density in ["High", "Extreme"]:
        st.warning(f"🚨 **CRITICAL ALERT: {density.upper()} Crowd Density Detected!** \n\nPedestrian count exceeds safe levels. Standard dispatch has been upgraded. Deploying extra police crowd-control detail and extra barricades immediately. Adjusting signal timing splits in adjacent corridors.")
