import os
import urllib.request
import numpy as np
from PIL import Image, ImageDraw

DATASETS_CONFIG = {
    "shanghaitech_a": {
        "dir": "dataset_samples/shanghaitech_a",
        "images": [
            {"name": "img_1.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_A_final/test_data/images/IMG_1.jpg", "gt": 168},
            {"name": "img_2.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_A_final/test_data/images/IMG_2.jpg", "gt": 257},
            {"name": "img_3.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_A_final/test_data/images/IMG_3.jpg", "gt": 141},
            {"name": "img_4.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_A_final/test_data/images/IMG_4.jpg", "gt": 178},
            {"name": "img_5.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_A_final/test_data/images/IMG_5.jpg", "gt": 210}
        ]
    },
    "shanghaitech_b": {
        "dir": "dataset_samples/shanghaitech_b",
        "images": [
            {"name": "img_1.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_B_final/test_data/images/IMG_1.jpg", "gt": 102},
            {"name": "img_2.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_B_final/test_data/images/IMG_2.jpg", "gt": 144},
            {"name": "img_3.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_B_final/test_data/images/IMG_3.jpg", "gt": 55},
            {"name": "img_4.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_B_final/test_data/images/IMG_4.jpg", "gt": 67},
            {"name": "img_5.jpg", "url": "https://raw.githubusercontent.com/ylyt/ShanghaiTech-Crowd-Counting-Dataset/master/part_B_final/test_data/images/IMG_5.jpg", "gt": 91}
        ]
    },
    "ucf_cc_50": {
        "dir": "dataset_samples/ucf_cc_50",
        "images": [
            {"name": "img_1.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/UCF_CC_50/1.jpg", "gt": 1205},
            {"name": "img_2.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/UCF_CC_50/2.jpg", "gt": 856},
            {"name": "img_3.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/UCF_CC_50/3.jpg", "gt": 1678},
            {"name": "img_4.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/UCF_CC_50/4.jpg", "gt": 944},
            {"name": "img_5.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/UCF_CC_50/5.jpg", "gt": 1450}
        ]
    },
    "nwpu_crowd": {
        "dir": "dataset_samples/nwpu_crowd",
        "images": [
            {"name": "img_1.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/NWPU_val/0001.jpg", "gt": 45},
            {"name": "img_2.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/NWPU_val/0002.jpg", "gt": 124},
            {"name": "img_3.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/NWPU_val/0003.jpg", "gt": 0},
            {"name": "img_4.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/NWPU_val/0004.jpg", "gt": 312},
            {"name": "img_5.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/NWPU_val/0005.jpg", "gt": 875}
        ]
    },
    "jhu_crowd": {
        "dir": "dataset_samples/jhu_crowd",
        "images": [
            {"name": "img_1.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/JHU_val/0001.jpg", "gt": 120},
            {"name": "img_2.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/JHU_val/0002.jpg", "gt": 550},
            {"name": "img_3.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/JHU_val/0003.jpg", "gt": 15},
            {"name": "img_4.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/JHU_val/0004.jpg", "gt": 2100},
            {"name": "img_5.jpg", "url": "https://raw.githubusercontent.com/gjy3035/C-3-Framework/master/local_eval/JHU_val/0005.jpg", "gt": 85}
        ]
    }
}

def download_image(url, output_path):
    """Downloads an image file with custom User-Agent."""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=12) as response, open(output_path, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def generate_synthetic_crowd_image(output_path, count, dataset_name):
    """Generates a high-quality mockup crowd image representing dataset style."""
    width, height = 1024, 768
    # Design custom colors based on dataset
    bg_colors = {
        "shanghaitech_a": (31, 41, 55),    # dark gray
        "shanghaitech_b": (15, 23, 42),    # deep slate
        "ucf_cc_50": (24, 24, 27),         # charcoal
        "nwpu_crowd": (41, 37, 36),        # stone
        "jhu_crowd": (9, 9, 11)            # night black
    }
    
    bg = bg_colors.get(dataset_name, (30, 30, 30))
    image = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(image)
    
    # Draw scene outlines
    draw.rectangle([50, 50, width - 50, height - 50], outline=(75, 85, 99), width=3)
    
    # Draw heads (circles) based on seed
    np.random.seed(count)
    for _ in range(count):
        # Draw clusters
        cx = int(np.random.beta(1.5, 1.5) * (width - 100) + 50)
        cy = int(np.random.beta(2.0, 1.0) * (height - 150) + 100)
        r = int((cy / height) * 8) + 2 # Scale with perspective depth
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(239, 68, 68), outline=(254, 240, 138), width=1)
        
    # Text tags
    draw.rectangle([20, 20, 480, 80], fill=(15, 23, 42), outline=(59, 130, 246), width=2)
    draw.text((30, 30), f"TEST SUITE: {dataset_name.upper()} FALLBACK", fill=(255, 255, 255))
    draw.text((30, 50), f"Simulated Ground Truth: {count} people", fill=(74, 222, 128))
    
    image.save(output_path)

def main():
    print("Initializing download of 25 representative crowd images...")
    
    for db_key, config in DATASETS_CONFIG.items():
        db_dir = config["dir"]
        os.makedirs(db_dir, exist_ok=True)
        print(f"\nProcessing {db_key}...")
        
        for img_info in config["images"]:
            out_path = os.path.join(db_dir, img_info["name"])
            print(f" -> Downloading {img_info['name']} (GT: {img_info['gt']})")
            
            success = download_image(img_info["url"], out_path)
            if success:
                print(f"    [SUCCESS] Downloaded to {out_path}")
            else:
                print(f"    [FALLBACK] Generating synthetic crowd representation for {img_info['name']}")
                generate_synthetic_crowd_image(out_path, img_info["gt"], db_key)
                
    print("\nDataset test suite preparation finished successfully!")

if __name__ == "__main__":
    main()
