import os
import cv2
import numpy as np

def create_cctv_video():
    img_path = "benchmark_data/blr_rally_cctv.png"
    out_path = "benchmark_data/blr_rally_cctv_video.mp4"
    
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Source image not found at {img_path}. Generate the image first.")
        
    print(f"Loading base CCTV frame from {img_path}...")
    base_img = cv2.imread(img_path)
    h, w, _ = base_img.shape
    
    # Target 720p
    target_w, target_h = 1280, 720
    if (w, h) != (target_w, target_h):
        base_img = cv2.resize(base_img, (target_w, target_h))
        h, w = target_h, target_w
        
    fps = 24
    duration_sec = 10
    total_frames = fps * duration_sec
    
    print(f"Generating 10-second {target_w}x{target_h} CCTV video clip at {fps} fps ({total_frames} frames)...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (target_w, target_h))
    
    # Initialize random movement vectors for crowd zones
    # We will perturb patches of the image to simulate moving bodies
    np.random.seed(42)
    crowd_zones = []
    # Identify 8 crowd clusters to animate
    for _ in range(8):
        cx = np.random.randint(200, target_w - 200)
        cy = np.random.randint(200, target_h - 200)
        r = np.random.randint(50, 120)
        crowd_zones.append((cx, cy, r))
        
    for frame_idx in range(total_frames):
        # 1. Base copy
        frame = base_img.copy()
        
        # 2. Simulate Pedestrian Sway/Movement (Local warping/perturbation)
        # We slightly shift local crowd patches in a wave-like manner
        for cx, cy, r in crowd_zones:
            shift_x = int(2 * np.sin(frame_idx * 0.15 + cx))
            shift_y = int(2 * np.cos(frame_idx * 0.15 + cy))
            
            # Extract patch and shift it
            x1, y1 = max(0, cx - r), max(0, cy - r)
            x2, y2 = min(target_w, cx + r), min(target_h, cy + r)
            
            patch = frame[y1:y2, x1:x2].copy()
            M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            shifted_patch = cv2.warpAffine(patch, M, (x2 - x1, y2 - y1), borderMode=cv2.BORDER_REPLICATE)
            frame[y1:y2, x1:x2] = shifted_patch
            
        # 3. Simulate Camera Sway (sine pan)
        cam_dx = 1.5 * np.sin(frame_idx * 0.05)
        cam_dy = 1.0 * np.cos(frame_idx * 0.05)
        M_cam = np.float32([[1, 0, cam_dx], [0, 1, cam_dy]])
        frame = cv2.warpAffine(frame, M_cam, (target_w, target_h), borderMode=cv2.BORDER_REPLICATE)
        
        # 4. Add CCTV Analog Scanlines and Noise
        # Random Gaussian noise
        noise = np.random.normal(0, 3, (target_h, target_w, 3)).astype(np.int8)
        frame = cv2.add(frame, noise, dtype=cv2.CV_8U)
        
        # Horizontal scanlines
        scanline_y = (frame_idx * 3) % target_h
        cv2.line(frame, (0, scanline_y), (target_w, scanline_y), (10, 10, 10), 1)
        
        # 5. Draw Digital HUD metadata overlay
        time_sec = frame_idx // fps
        time_ms = int((frame_idx % fps) * (1000 / fps))
        hud_time = f"2026-06-17 12:45:{time_sec:02d}.{time_ms:03d}"
        
        cv2.rectangle(frame, (10, 10), (450, 80), (15, 23, 42), -1)
        cv2.putText(frame, "CAM_BLR_ALT_102 | FEED_ACTIVE", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        cv2.putText(frame, f"TIME: {hud_time}", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        cv2.putText(frame, "FPS: 24.00 | 720p SURVEILLANCE", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Write frame
        out.write(frame)
        
    out.release()
    print(f"CCTV Video generated successfully and saved to {out_path}")

if __name__ == "__main__":
    create_cctv_video()
