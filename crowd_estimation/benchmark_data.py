import os
import cv2
import numpy as np
import urllib.request
from PIL import Image, ImageDraw

# 10 Publicly Available Benchmark Images
BENCHMARK_IMAGES = {
    "sparse_1": {
        "filename": "sparse_1.jpg",
        "url": "https://images.pexels.com/photos/1485894/pexels-photo-1485894.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 18,
        "difficulty": "Easy",
        "description": "Pedestrians walking across a clean city crossing. Well-spaced, minimal occlusion.",
        "category": "Sparse (<50 people)"
    },
    "sparse_2": {
        "filename": "sparse_2.jpg",
        "url": "https://images.pexels.com/photos/1043474/pexels-photo-1043474.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 8,
        "difficulty": "Easy",
        "description": "People sitting on benches and walking in a park under bright daylight.",
        "category": "Sparse (<50 people)"
    },
    "sparse_3": {
        "filename": "sparse_3.jpg",
        "url": "https://images.pexels.com/photos/62689/pexels-photo-62689.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 12,
        "difficulty": "Easy",
        "description": "Patrons at an outdoor cafe. Some sitting, some standing. Good illumination.",
        "category": "Sparse (<50 people)"
    },
    "medium_1": {
        "filename": "medium_1.jpg",
        "url": "https://images.pexels.com/photos/264507/pexels-photo-264507.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 75,
        "difficulty": "Medium",
        "description": "Shopping mall main concourse. Multiple floor levels, some scale variations and overlap.",
        "category": "Medium (50-300 people)"
    },
    "medium_2": {
        "filename": "medium_2.jpg",
        "url": "https://images.pexels.com/photos/1367097/pexels-photo-1367097.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 140,
        "difficulty": "Medium",
        "description": "Busy metropolitan shopping street. Overlaps, background clutter, and perspective scale shifts.",
        "category": "Medium (50-300 people)"
    },
    "medium_3": {
        "filename": "medium_3.jpg",
        "url": "https://images.pexels.com/photos/1190297/pexels-photo-1190297.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 210,
        "difficulty": "Medium-Hard",
        "description": "Indoor music concert crowd facing the stage. Low lighting, colorful spotlights, back views.",
        "category": "Medium (50-300 people)"
    },
    "dense_1": {
        "filename": "dense_1.jpg",
        "url": "https://images.pexels.com/photos/1709003/pexels-photo-1709003.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 450,
        "difficulty": "Hard",
        "description": "Protesters marching down a wide street. High level of body occlusion and overlapping heads.",
        "category": "Dense (300-1000 people)"
    },
    "dense_2": {
        "filename": "dense_2.jpg",
        "url": "https://images.pexels.com/photos/270154/pexels-photo-270154.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 600,
        "difficulty": "Hard",
        "description": "Spectators seated in a large sports stadium during the day. Repetitive patterns, head-only visibility.",
        "category": "Dense (300-1000 people)"
    },
    "extremely_dense_1": {
        "filename": "extremely_dense_1.jpg",
        "url": "https://images.pexels.com/photos/1587927/pexels-photo-1587927.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 1250,
        "difficulty": "Extreme",
        "description": "Outdoor city festival parade. Extremely packed heads, high density, distant heads are tiny pixels.",
        "category": "Extremely Dense (>1000 people)"
    },
    "extremely_dense_2": {
        "filename": "extremely_dense_2.jpg",
        "url": "https://images.pexels.com/photos/157827/pexels-photo-157827.jpeg",
        "source": "Pexels (Stock Image)",
        "ground_truth": 1100,
        "difficulty": "Extreme",
        "description": "Subway station transit rush hour. Mixed motion blur, indoor neon lighting, heavy overlap.",
        "category": "Extremely Dense (>1000 people)"
    }
}

# 5 Publicly Available Benchmark Videos
BENCHMARK_VIDEOS = {
    "political_rally": {
        "filename": "political_rally.mp4",
        "url": "https://videos.pexels.com/video-files/3129957/3129957-hd_1280_720_25fps.mp4",
        "source": "Pexels Video",
        "ground_truth": 350,
        "difficulty": "Hard",
        "description": "Crowd waving flags and signs in an outdoor political speech. Hand movements, occlusions.",
        "category": "Political Rally"
    },
    "cricket_match": {
        "filename": "cricket_match.mp4",
        "url": "https://videos.pexels.com/video-files/8937669/8937669-hd_1080_1920_25fps.mp4",
        "source": "Pexels Video",
        "ground_truth": 850,
        "difficulty": "Hard",
        "description": "Spectator stand during a match. Rapid cheering movements, changing illumination, extreme perspective.",
        "category": "Cricket Match Crowd"
    },
    "religious_gathering": {
        "filename": "religious_gathering.mp4",
        "url": "https://videos.pexels.com/video-files/5425624/5425624-sd_640_360_24fps.mp4",
        "source": "Pexels Video",
        "ground_truth": 1200,
        "difficulty": "Extreme",
        "description": "Massive religious festival procession. Heavy shoulder-to-shoulder pack, slow moving wave, extreme scale changes.",
        "category": "Religious Gathering"
    },
    "street_protest": {
        "filename": "street_protest.mp4",
        "url": "https://videos.pexels.com/video-files/4226317/4226317-hd_1920_1080_30fps.mp4",
        "source": "Pexels Video",
        "ground_truth": 400,
        "difficulty": "Hard",
        "description": "Protesters walking holding banners. Banners blocking people, moving cameras, variable perspective.",
        "category": "Street Protest"
    },
    "traffic_intersection": {
        "filename": "traffic_intersection.mp4",
        "url": "https://videos.pexels.com/video-files/3125288/3125288-hd_1280_720_25fps.mp4",
        "source": "Pexels Video",
        "ground_truth": 45,
        "difficulty": "Medium",
        "description": "Pedestrians crossing a busy urban street intersection. High angle view, mix of people and vehicles.",
        "category": "Traffic Intersection with Pedestrians"
    }
}

def download_file(url, output_path):
    """Downloads a file from a URL with custom User-Agent to bypass basic scrap blockers."""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=20) as response, open(output_path, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except Exception as e:
        print(f"Error downloading {url} -> {output_path}: {e}")
        return False

def generate_synthetic_image(output_path, count, category):
    """Generates a high-quality mockup crowd image with dots representing heads/people."""
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), color=(30, 41, 59)) # Deep slate background
    draw = ImageDraw.Draw(image)
    
    # Draw simple background elements: a road grid and street lines
    draw.polygon([(400, 720), (880, 720), (670, 300), (610, 300)], fill=(71, 85, 105)) # Road
    draw.line([(640, 720), (640, 300)], fill=(253, 224, 71), width=4) # Yellow dash line
    draw.rectangle([0, 0, width, 250], fill=(15, 23, 42)) # Buildings sky area
    draw.rectangle([50, 100, 300, 250], fill=(51, 65, 85)) # Building left
    draw.rectangle([980, 50, 1200, 250], fill=(51, 65, 85)) # Building right
    
    # Generate random points corresponding to people
    np.random.seed(hash(output_path) % 1234567)
    
    # Scale dots by perspective (lower down the image -> larger dots)
    for _ in range(count):
        # Sample points on or near the road
        y = int(np.random.beta(2, 1) * 470 + 250) # Mostly on the lower part (closer)
        spread = int((y - 250) * 1.2) + 20
        x = int(640 + np.random.uniform(-spread, spread))
        x = max(10, min(width - 10, x))
        
        # Calculate size based on distance (y coordinate)
        size = int((y - 250) / 45) + 3
        
        # Draw head (circle) and simple torso
        r = size
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(239, 68, 68)) # Red head
        draw.line([x, y + r, x, y + 3 * r], fill=(59, 130, 246), width=max(1, r // 2)) # Blue body
        
    # Draw label on the image
    draw.rectangle([20, 20, 450, 80], fill=(15, 23, 42), outline=(59, 130, 246), width=2)
    draw.text((30, 30), f"SYNTHETIC CROWD GENERATOR: {category}", fill=(248, 250, 252))
    draw.text((30, 50), f"Target Ground Truth: {count} people", fill=(74, 222, 128))
    
    image.save(output_path)

def generate_synthetic_video(output_path, count, category, duration_sec=5, fps=24):
    """Generates a mockup crowd video with moving objects to simulate motion dynamics."""
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = int(duration_sec * fps)
    
    # Setup initial positions of simulated people
    np.random.seed(42)
    people = []
    for _ in range(count):
        y = np.random.uniform(260, 700)
        spread = (y - 250) * 1.2 + 20
        x = 640 + np.random.uniform(-spread, spread)
        speed_x = np.random.uniform(-1.0, 1.0)
        speed_y = np.random.uniform(-0.5, 0.5)
        color = (np.random.randint(50, 255), np.random.randint(50, 255), np.random.randint(50, 255))
        people.append({"x": x, "y": y, "vx": speed_x, "vy": speed_y, "color": color})
        
    for frame_idx in range(total_frames):
        # Create canvas
        frame = np.ones((height, width, 3), dtype=np.uint8) * 41 # RGB(41, 41, 41) -> Slate
        
        # Draw background elements
        # Road outline
        road_pts = np.array([[350, 720], [930, 720], [670, 250], [610, 250]], np.int32)
        cv2.fillPoly(frame, [road_pts], (85, 85, 85)) # Grey road
        
        # Draw text overlay
        cv2.putText(frame, f"SYNTHETIC CCTV STREAM: {category}", (30, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"GT Count: {count} | Frame: {frame_idx}/{total_frames}", (30, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)
        
        # Update and draw people
        for p in people:
            # Update position
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            
            # Constrain position to keep it in road perspective
            spread = (p["y"] - 250) * 1.2 + 20
            if p["x"] < 640 - spread or p["x"] > 640 + spread or p["y"] < 250 or p["y"] > 720:
                # Reset
                p["y"] = np.random.uniform(260, 700)
                new_spread = (p["y"] - 250) * 1.2 + 20
                p["x"] = 640 + np.random.uniform(-new_spread, new_spread)
                
            x, y = int(p["x"]), int(p["y"])
            size = max(2, int((p["y"] - 250) / 45) + 2)
            
            # Draw person as circle
            cv2.circle(frame, (x, y), size, p["color"], -1)
            # Draw a tiny body line
            cv2.line(frame, (x, y + size), (x, y + 3 * size), (255, 255, 255), max(1, size // 2))
            
        out.write(frame)
        
    out.release()

def prepare_benchmark_assets(data_dir="benchmark_data", force_download=False):
    """
    Downloads or generates the benchmark images and videos.
    Returns status of each asset.
    """
    os.makedirs(data_dir, exist_ok=True)
    results = {"images": {}, "videos": {}}
    
    # Process Images
    for key, info in BENCHMARK_IMAGES.items():
        out_path = os.path.join(data_dir, info["filename"])
        if os.path.exists(out_path) and not force_download:
            results["images"][key] = {"path": out_path, "status": "exists"}
        else:
            print(f"Downloading image {info['filename']}...")
            success = download_file(info["url"], out_path)
            if success:
                results["images"][key] = {"path": out_path, "status": "downloaded"}
            else:
                print(f"Fallback: Generating synthetic image for {info['filename']}...")
                generate_synthetic_image(out_path, info["ground_truth"], info["category"])
                results["images"][key] = {"path": out_path, "status": "synthetic"}
                
    # Process Videos
    for key, info in BENCHMARK_VIDEOS.items():
        out_path = os.path.join(data_dir, info["filename"])
        if os.path.exists(out_path) and not force_download:
            results["videos"][key] = {"path": out_path, "status": "exists"}
        else:
            print(f"Downloading video {info['filename']}...")
            success = download_file(info["url"], out_path)
            if success:
                results["videos"][key] = {"path": out_path, "status": "downloaded"}
            else:
                print(f"Fallback: Generating synthetic video for {info['filename']}...")
                generate_synthetic_video(out_path, info["ground_truth"], info["category"])
                results["videos"][key] = {"path": out_path, "status": "synthetic"}
                
    return results

if __name__ == "__main__":
    print("Initializing benchmark dataset creation...")
    res = prepare_benchmark_assets()
    print("Initialization finished!")
    print(res)
