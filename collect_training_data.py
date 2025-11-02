"""
Training Data Collection Script
Click on each color in the puzzle to collect training samples
"""
import pyautogui
import cv2
import numpy as np
import json
import os
from typing import Dict, List
import time

# Color names to collect
COLORS = ['pink', 'green', 'orange', 'red', 'gray', 'blue', 'yellow']

def collect_color_samples(color_name: str, num_samples: int = 20) -> List[tuple]:
    """Collect RGB samples by clicking on the color"""
    print(f"\n{'='*60}")
    print(f"Collecting samples for: {color_name.upper()}")
    print(f"{'='*60}")
    print(f"\nClick on {color_name} pixels {num_samples} times")
    print("Press 's' to skip this color, 'q' to quit")
    
    samples = []
    count = 0
    
    try:
        from pynput import keyboard, mouse
        
        stop_collection = False
        
        def on_press(key):
            nonlocal stop_collection
            try:
                if key.char == 's':
                    print("  Skipping this color...")
                    stop_collection = True
                    return False
                elif key.char == 'q':
                    print("  Quitting...")
                    stop_collection = True
                    return False
            except:
                pass
        
        def on_click(x, y, button, pressed):
            nonlocal count
            if pressed and button == mouse.Button.left:
                # Get pixel color at click position
                screenshot = pyautogui.screenshot()
                rgb = screenshot.getpixel((x, y))
                samples.append((int(rgb[0]), int(rgb[1]), int(rgb[2])))
                count += 1
                print(f"  Sample {count}/{num_samples}: RGB{rgb}")
                
                if count >= num_samples:
                    return False
        
        keyboard_listener = keyboard.Listener(on_press=on_press)
        mouse_listener = mouse.Listener(on_click=on_click)
        
        keyboard_listener.start()
        mouse_listener.start()
        
        while count < num_samples and not stop_collection:
            time.sleep(0.1)
        
        keyboard_listener.stop()
        mouse_listener.stop()
        
    except ImportError:
        print("pynput not available, using manual input...")
        for i in range(num_samples):
            input(f"Click on {color_name} and press Enter ({i+1}/{num_samples})...")
            x, y = pyautogui.position()
            screenshot = pyautogui.screenshot()
            rgb = screenshot.getpixel((x, y))
            samples.append((int(rgb[0]), int(rgb[1]), int(rgb[2])))
            print(f"  Sample {i+1}: RGB{rgb}")
    
    print(f"\n✓ Collected {len(samples)} samples for {color_name}")
    return samples

def main():
    """Main training data collection"""
    print("="*60)
    print("TRAINING DATA COLLECTION")
    print("="*60)
    print("\nThis script will help you collect color samples for training.")
    print("You'll click on each color multiple times to build a dataset.")
    print("\nColors to collect:", ", ".join(COLORS))
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    training_data = {}
    
    for color_name in COLORS:
        samples = collect_color_samples(color_name, num_samples=30)
        if samples:
            training_data[color_name] = samples
    
    # Save training data
    os.makedirs('training_data', exist_ok=True)
    output_file = 'training_data/color_samples.json'
    
    with open(output_file, 'w') as f:
        json.dump(training_data, f, indent=2)
    
    print(f"\n{'='*60}")
    print("TRAINING DATA COLLECTED")
    print(f"{'='*60}")
    print(f"\nSaved {len(training_data)} colors to {output_file}")
    print(f"Total samples: {sum(len(samples) for samples in training_data.values())}")
    print("\nNext step: Run train_color_model.py to train the model")

if __name__ == "__main__":
    main()

