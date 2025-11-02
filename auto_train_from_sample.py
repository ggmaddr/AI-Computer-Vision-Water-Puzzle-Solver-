"""
Automated Training from Sample Image
Extracts color samples from sample.png and trains the model automatically
"""
import cv2
import numpy as np
import json
import os
from sklearn.cluster import KMeans

def extract_samples_from_image(image_path: str = 'sample.png', samples_per_color: int = 100):
    """Automatically extract color samples from the sample image"""
    print("="*60)
    print("AUTOMATED TRAINING DATA EXTRACTION")
    print("="*60)
    
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found!")
        return None
    
    print(f"\nLoading {image_path}...")
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return None
    
    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = image_rgb.shape[:2]
    
    print(f"Image size: {w}x{h}")
    
    # Known color templates (approximate) - we'll refine these
    color_templates = {
        'pink': (236, 105, 144),
        'green': (108, 220, 158),
        'orange': (231, 161, 75),
        'red': (222, 105, 144),
        'gray': (101, 100, 103),
        'blue': (33, 80, 218),
        'yellow': (250, 223, 75),
    }
    
    # Convert to LAB for better matching
    def rgb_to_lab(rgb):
        rgb_arr = np.array([[rgb]], dtype=np.uint8).reshape(1, 1, 3)
        lab_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2LAB)
        return lab_arr[0][0]
    
    # Find pixels closest to each color template
    training_data = {}
    
    print("\nExtracting samples for each color...")
    
    for color_name, template_rgb in color_templates.items():
        print(f"\nProcessing {color_name}...")
        
        template_lab = rgb_to_lab(template_rgb)
        
        # Sample pixels from the image - focus on bright, saturated areas
        # Use a grid to avoid clustering in one area
        sample_step = max(2, int(np.sqrt(w * h / (samples_per_color * 20))))
        
        candidates = []
        
        for y in range(0, h, sample_step):
            for x in range(0, w, sample_step):
                pixel_rgb = image_rgb[y, x]
                pixel_lab = rgb_to_lab(pixel_rgb)
                
                # Calculate LAB distance
                lab_dist = np.sqrt(np.sum((pixel_lab - template_lab)**2))
                
                # Filter: must be bright enough and have reasonable color
                brightness = np.mean(pixel_rgb)
                saturation = np.std(pixel_rgb)  # Color variance as saturation proxy
                
                # Gray needs special handling (low saturation)
                if color_name == 'gray':
                    if 70 < brightness < 220 and saturation < 30:  # Gray: medium brightness, low saturation
                        candidates.append({
                            'rgb': tuple(pixel_rgb),
                            'distance': lab_dist,
                            'x': x,
                            'y': y
                        })
                else:
                    # Other colors: bright and saturated
                    if brightness > 80 and saturation > 20:  # Bright enough and has color
                        candidates.append({
                            'rgb': tuple(pixel_rgb),
                            'distance': lab_dist,
                            'x': x,
                            'y': y
                        })
        
        # Sort by distance and take closest samples
        candidates.sort(key=lambda c: c['distance'])
        
        # Take samples within reasonable distance (tighter threshold)
        if len(candidates) > 0:
            max_distance = candidates[min(samples_per_color, len(candidates)-1)]['distance'] * 1.2
        
        samples = [c['rgb'] for c in candidates if c['distance'] <= max_distance]
        samples = samples[:samples_per_color]
        
        if samples:
            training_data[color_name] = samples
            print(f"  ✓ Extracted {len(samples)} samples")
        else:
            print(f"  ✗ No samples found")
    
    return training_data

def train_from_samples(training_data, output_file='training_data/color_model.pkl'):
    """Train model from extracted samples"""
    print("\n" + "="*60)
    print("TRAINING MODEL")
    print("="*60)
    
    color_models = {}
    color_stats = {}
    
    for color_name, rgb_samples in training_data.items():
        if not rgb_samples:
            continue
        
        rgb_array = np.array(rgb_samples, dtype=np.float32)
        
        # Convert to LAB
        rgb_reshaped = rgb_array.reshape(-1, 1, 3).astype(np.uint8)
        lab_array = cv2.cvtColor(rgb_reshaped, cv2.COLOR_RGB2LAB)
        lab_samples = lab_array.reshape(-1, 3).astype(float)
        
        # Convert to HSV
        hsv_array = cv2.cvtColor(rgb_reshaped, cv2.COLOR_RGB2HSV)
        hsv_samples = hsv_array.reshape(-1, 3)
        
        # K-means to find center
        kmeans = KMeans(n_clusters=1, n_init=10, random_state=42)
        kmeans.fit(lab_samples)
        
        lab_center = kmeans.cluster_centers_[0]
        
        # Convert back to RGB
        lab_center_reshaped = lab_center.reshape(1, 1, 3).astype(np.uint8)
        rgb_center_reshaped = cv2.cvtColor(lab_center_reshaped, cv2.COLOR_LAB2RGB)
        rgb_center = rgb_center_reshaped[0][0]
        
        # Statistics
        lab_distances = np.sqrt(np.sum((lab_samples - lab_center)**2, axis=1))
        mean_distance = np.mean(lab_distances)
        std_distance = np.std(lab_distances)
        max_distance = np.percentile(lab_distances, 95)
        
        h_mean = np.mean(hsv_samples[:, 0])
        s_mean = np.mean(hsv_samples[:, 1])
        v_mean = np.mean(hsv_samples[:, 2])
        
        color_models[color_name] = {
            'rgb_center': tuple(rgb_center),
            'lab_center': tuple(lab_center),
            'hsv_mean': (float(h_mean), float(s_mean), float(v_mean)),
        }
        
        color_stats[color_name] = {
            'mean_lab_distance': float(mean_distance),
            'std_lab_distance': float(std_distance),
            'max_lab_distance': float(max_distance),
        }
        
        print(f"\n{color_name.upper()}:")
        print(f"  RGB center: {tuple(rgb_center)}")
        print(f"  Max LAB distance (threshold): {max_distance:.1f}")
    
    # Save model
    import pickle
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
    print(f"\nSaved to: {output_file}")
    
    return model_data

def main():
    """Main automated training"""
    print("="*60)
    print("AUTOMATED COLOR MODEL TRAINING")
    print("="*60)
    print("\nThis will:")
    print("1. Extract color samples from sample.png")
    print("2. Train the color detection model")
    print("3. Save the trained model")
    
    # Step 1: Extract samples
    training_data = extract_samples_from_image('sample.png', samples_per_color=150)
    
    if not training_data:
        print("\n✗ Failed to extract training data")
        return
    
    # Save raw samples
    os.makedirs('training_data', exist_ok=True)
    with open('training_data/color_samples.json', 'w') as f:
        # Convert to list format for JSON
        json_data = {k: [[int(r), int(g), int(b)] for r, g, b in v] for k, v in training_data.items()}
        json.dump(json_data, f, indent=2)
    
    print(f"\n✓ Saved raw samples to training_data/color_samples.json")
    
    # Step 2: Train model
    model_data = train_from_samples(training_data)
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print("\n✓ Model is ready to use")
    print("\nYou can now run:")
    print("  python3 main.py")

if __name__ == "__main__":
    main()

