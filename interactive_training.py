"""
Interactive Training Mode
Shows detected colors and allows correction to improve the model
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from image_processor import ImageProcessor
import json
import numpy as np
from typing import List, Tuple

def verify_and_correct_tubes(processor: ImageProcessor, image, tubes_data: List[dict]):
    """
    Interactive verification of detected tube colors
    Shows each tube and asks user to correct if wrong
    """
    print("\n" + "="*60)
    print("INTERACTIVE TUBE VERIFICATION")
    print("="*60)
    
    corrections = []
    
    for i, tube_data in enumerate(tubes_data):
        tube_idx = tube_data['index']
        detected_colors = tube_data['colors']
        
        print(f"\n{'='*60}")
        print(f"TUBE {tube_idx}")
        print(f"{'='*60}")
        print(f"Detected: {detected_colors}")
        
        response = input("Is this correct? (y/n, or 's' to skip): ").strip().lower()
        
        if response == 's':
            continue
        elif response == 'n':
            # Get correct colors
            print("\nEnter correct colors from BOTTOM to TOP (e.g., red,orange,green,pink):")
            correct_input = input("Colors: ").strip()
            
            if correct_input:
                correct_colors = [c.strip() for c in correct_input.split(',')]
                print(f"You entered: {correct_colors}")
                
                # Collect samples for correction
                correction_samples = collect_correction_samples(
                    processor, image, tube_data['rect'], 
                    detected_colors, correct_colors
                )
                
                if correction_samples:
                    corrections.append({
                        'tube_idx': tube_idx,
                        'detected': detected_colors,
                        'correct': correct_colors,
                        'samples': correction_samples
                    })
        
        print()
    
    return corrections

def collect_correction_samples(processor, image, tube_rect, detected: List[str], correct: List[str]) -> dict:
    """Collect samples for colors that were misdetected"""
    print("\nCollecting correction samples...")
    print("Click on each color in this tube from BOTTOM to TOP")
    
    samples = {}
    
    for i, (det, cor) in enumerate(zip(detected, correct)):
        if det != cor:
            print(f"\nColor {i+1}: Wrongly detected as '{det}', should be '{cor}'")
            print(f"Click on the correct '{cor}' color in this position...")
            
            color_samples = collect_click_samples(cor, num_samples=10)
            if color_samples:
                if cor not in samples:
                    samples[cor] = []
                samples[cor].extend(color_samples)
    
    return samples

def collect_click_samples(color_name: str, num_samples: int = 10) -> List[Tuple[int, int, int]]:
    """Collect RGB samples by clicking"""
    import pyautogui
    import time
    
    samples = []
    count = 0
    
    try:
        from pynput import mouse
        
        def on_click(x, y, button, pressed):
            nonlocal count
            if pressed and button == mouse.Button.left:
                screenshot = pyautogui.screenshot()
                rgb = screenshot.getpixel((x, y))
                samples.append((int(rgb[0]), int(rgb[1]), int(rgb[2])))
                count += 1
                print(f"  Sample {count}/{num_samples}: RGB{rgb}")
                if count >= num_samples:
                    return False
        
        listener = mouse.Listener(on_click=on_click)
        listener.start()
        
        start_time = time.time()
        while count < num_samples and (time.time() - start_time) < 30:
            time.sleep(0.1)
        
        listener.stop()
    except ImportError:
        for i in range(num_samples):
            input(f"Click on {color_name} and press Enter ({i+1}/{num_samples})...")
            x, y = pyautogui.position()
            screenshot = pyautogui.screenshot()
            rgb = screenshot.getpixel((x, y))
            samples.append((int(rgb[0]), int(rgb[1]), int(rgb[2])))
    
    return samples

def merge_training_data(existing_file: str, corrections: List[dict]):
    """Merge correction samples into existing training data"""
    # Load existing
    if os.path.exists(existing_file):
        with open(existing_file, 'r') as f:
            training_data = json.load(f)
    else:
        training_data = {}
    
    # Add corrections
    for correction in corrections:
        for color_name, samples in correction['samples'].items():
            if color_name not in training_data:
                training_data[color_name] = []
            training_data[color_name].extend(samples)
            print(f"Added {len(samples)} samples for {color_name}")
    
    # Save
    with open(existing_file, 'w') as f:
        json.dump(training_data, f, indent=2)
    
    print(f"\n✓ Updated training data: {existing_file}")
    print(f"Total samples per color:")
    for color_name, samples in training_data.items():
        print(f"  {color_name}: {len(samples)}")

def main():
    """Main interactive training"""
    print("="*60)
    print("INTERACTIVE COLOR TRAINING")
    print("="*60)
    print("\nThis will:")
    print("1. Capture current puzzle")
    print("2. Show detected colors for each tube")
    print("3. Let you correct wrong detections")
    print("4. Collect samples from corrected colors")
    print("5. Update training data")
    
    input("\nPress Enter to start...")
    
    # Initialize processor
    processor = ImageProcessor()
    
    # Capture current screen
    print("\nCapturing current puzzle...")
    image = processor.capture_screen()
    
    # Detect tubes
    tubes = processor.detect_tubes(image)
    if not tubes:
        print("No tubes detected! Make sure the puzzle is visible.")
        return
    
    print(f"Detected {len(tubes)} tubes")
    
    # Analyze each tube
    tubes_data = []
    for i, tube_rect in enumerate(tubes):
        colors = processor.extract_tube_colors(image, tube_rect)
        tubes_data.append({
            'index': i,
            'rect': tube_rect,
            'colors': colors
        })
    
    # Verify and correct
    corrections = verify_and_correct_tubes(processor, image, tubes_data)
    
    if corrections:
        print(f"\n{'='*60}")
        print(f"FOUND {len(corrections)} CORRECTIONS")
        print(f"{'='*60}")
        
        merge = input("\nMerge corrections into training data? (y/n): ").strip().lower()
        if merge == 'y':
            merge_training_data('training_data/color_samples.json', corrections)
            print("\n✓ Training data updated!")
            print("Run: python3 train_color_model.py to retrain")
    else:
        print("\nNo corrections needed!")

if __name__ == "__main__":
    main()

