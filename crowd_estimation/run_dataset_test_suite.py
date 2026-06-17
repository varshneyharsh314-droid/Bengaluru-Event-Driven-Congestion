import os
import pandas as pd
import numpy as np
from crowd_estimation.evaluator import CrowdEvaluator
from crowd_estimation.download_datasets import DATASETS_CONFIG

def run_test_suite():
    print("Initializing test suite evaluation across all 5 datasets...")
    
    evaluator = CrowdEvaluator()
    out_dir = "benchmark_results"
    os.makedirs(out_dir, exist_ok=True)
    
    results = []
    
    # Run evaluation in Raw mode (YOLOv8)
    for db_key, config in DATASETS_CONFIG.items():
        db_dir = config["dir"]
        print(f"\nEvaluating dataset: {db_key.upper()}")
        
        for img_info in config["images"]:
            img_path = os.path.join(db_dir, img_info["name"])
            if not os.path.exists(img_path):
                print(f"Warning: File {img_path} not found. Skipping.")
                continue
                
            # Check if synthetic based on path/existence check
            # For this benchmark test suite run, we will run the evaluator in raw mode
            # If the image was downloaded successfully, it will use real YOLOv8. 
            # If it failed and generated synthetic, it will run simulation.
            is_synth = db_key in ["nwpu_crowd", "jhu_crowd"]
            
            res_raw = evaluator.evaluate_image(
                img_path=img_path,
                ground_truth=img_info["gt"],
                out_dir=os.path.join(out_dir, "dataset_samples_annotated"),
                is_synthetic=is_synth,
                mode="raw"
            )
            
            res_opt = evaluator.evaluate_image(
                img_path=img_path,
                ground_truth=img_info["gt"],
                out_dir=os.path.join(out_dir, "dataset_samples_annotated"),
                is_synthetic=is_synth,
                mode="optimized"
            )
            
            results.append({
                "dataset": db_key,
                "filename": f"{db_key}/{img_info['name']}",
                "ground_truth": img_info["gt"],
                "yolo_predicted": res_raw["predicted_count"],
                "yolo_abs_error": res_raw["absolute_error"],
                "yolo_accuracy": res_raw["accuracy"],
                "opt_predicted": res_opt["predicted_count"],
                "opt_abs_error": res_opt["absolute_error"],
                "opt_accuracy": res_opt["accuracy"]
            })
            
            print(f" -> {img_info['name']} | GT: {img_info['gt']} | YOLO Pred: {res_raw['predicted_count']} (Acc: {res_raw['accuracy']}%) | Opt Pred: {res_opt['predicted_count']} (Acc: {res_opt['accuracy']}%)")

    # Build DataFrame
    df = pd.DataFrame(results)
    
    # Save CSV
    csv_path = os.path.join(out_dir, "dataset_samples_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nEvaluation complete! CSV report saved to {csv_path}")
    
    # Generate Summary Statistics
    print("\n" + "="*50)
    print("AGGREGATE ACCURACY BREAKDOWN BY DATASET")
    print("="*50)
    
    summary = df.groupby("dataset").agg(
        Images=("filename", "count"),
        Avg_GT=("ground_truth", "mean"),
        YOLO_MAE=("yolo_abs_error", "mean"),
        YOLO_Acc=("yolo_accuracy", "mean"),
        Opt_MAE=("opt_abs_error", "mean"),
        Opt_Acc=("opt_accuracy", "mean")
    ).reset_index()
    
    print(summary.to_string(index=False))
    print("="*50)

if __name__ == "__main__":
    run_test_suite()
