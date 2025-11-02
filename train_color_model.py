"""
Train Color Detection Model
Uses collected training data to learn color clusters and create detection model
"""
import json
import numpy as np
import cv2
from sklearn.cluster import KMeans
from typing import Dict, Tuple, List
import os
import pickle

def load_training_data(data_file: str = 'training_data/color_samples.json') -> Dict[str, List[Tuple[int, int, int]]]:
    """Load training samples from JSON file"""
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Training data not found: {data_file}\nRun collect_training_data.py first!")
    
    with open(data_file, 'r') as f:
        return json.load(f)

def train_color_model(data_file: str = 'training_data/color_samples.json', 
                     output_file: str = 'training_data/color_model.pkl'):
    """
    Train color detection model using K-means clustering
    Learns optimal color templates and decision boundaries
    """
    print("="*60)
    print("TRAINING COLOR DETECTION MODEL")
    print("="*60)
    
    # Load training data
    print("\nLoading training data...")
    training_data = load_training_data(data_file)
    
    if not training_data:
        raise ValueError("No training data found!")
    
    print(f"Loaded {len(training_data)} colors:")
    for color_name, samples in training_data.items():
        print(f"  {color_name}: {len(samples)} samples")
    
    # Process each color: find optimal cluster centers
    color_models = {}
    color_stats = {}
    
    for color_name, rgb_samples in training_data.items():
        if not rgb_samples:
            continue
        
        # Convert to numpy array
        rgb_array = np.array(rgb_samples, dtype=np.float32)
        
        # Convert to LAB color space for better clustering
        rgb_reshaped = rgb_array.reshape(-1, 1, 3).astype(np.uint8)
        lab_array = cv2.cvtColor(rgb_reshaped, cv2.COLOR_RGB2LAB)
        lab_samples = lab_array.reshape(-1, 3).astype(float)
        
        # Also convert to HSV for hue-based rules
        hsv_array = cv2.cvtColor(rgb_reshaped, cv2.COLOR_RGB2HSV)
        hsv_samples = hsv_array.reshape(-1, 3)
        
        # Use K-means to find main cluster (k=1 to get centroid)
        # But also try k=2 to separate main color from outliers
        kmeans = KMeans(n_clusters=1, n_init=10, random_state=42)
        kmeans.fit(lab_samples)
        
        # Main cluster center in LAB
        lab_center = kmeans.cluster_centers_[0]
        
        # Convert back to RGB
        lab_center_reshaped = lab_center.reshape(1, 1, 3).astype(np.uint8)
        rgb_center_reshaped = cv2.cvtColor(lab_center_reshaped, cv2.COLOR_LAB2RGB)
        rgb_center = rgb_center_reshaped[0][0]
        
        # Calculate statistics
        lab_distances = np.sqrt(np.sum((lab_samples - lab_center)**2, axis=1))
        mean_distance = np.mean(lab_distances)
        std_distance = np.std(lab_distances)
        max_distance = np.percentile(lab_distances, 95)  # 95th percentile
        
        # HSV statistics
        h_mean = np.mean(hsv_samples[:, 0])
        s_mean = np.mean(hsv_samples[:, 1])
        v_mean = np.mean(hsv_samples[:, 2])
        
        h_std = np.std(hsv_samples[:, 0])
        s_std = np.std(hsv_samples[:, 1])
        v_std = np.std(hsv_samples[:, 2])
        
        color_models[color_name] = {
            'rgb_center': tuple(rgb_center),
            'lab_center': tuple(lab_center),
            'hsv_mean': (h_mean, s_mean, v_mean),
            'hsv_std': (h_std, s_std, v_std),
        }
        
        color_stats[color_name] = {
            'mean_lab_distance': float(mean_distance),
            'std_lab_distance': float(std_distance),
            'max_lab_distance': float(max_distance),  # Detection threshold
        }
        
        print(f"\n{color_name.upper()}:")
        print(f"  RGB center: {tuple(rgb_center)}")
        print(f"  LAB center: {lab_center}")
        print(f"  HSV mean: ({h_mean:.1f}, {s_mean:.1f}, {v_mean:.1f})")
        print(f"  Max LAB distance (threshold): {max_distance:.1f}")
    
    # Save model
    model_data = {
        'color_models': color_models,
        'color_stats': color_stats,
        'training_samples': {k: len(v) for k, v in training_data.items()}
    }
    
    os.makedirs('training_data', exist_ok=True)
    with open(output_file, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"\n{'='*60}")
    print("MODEL TRAINED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"\nSaved model to: {output_file}")
    print(f"\nModel includes:")
    print(f"  - RGB/LAB/HSV centers for each color")
    print(f"  - Detection thresholds (max LAB distance)")
    print(f"  - Statistics for robust matching")
    print(f"\nNext: Update image_processor.py to use this trained model")

if __name__ == "__main__":
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else 'training_data/color_samples.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'training_data/color_model.pkl'
    train_color_model(data_file, output_file)

