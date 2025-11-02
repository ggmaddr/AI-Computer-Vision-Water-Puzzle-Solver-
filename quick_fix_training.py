"""
Quick Fix Training - Collect samples for specific wrong detections
Run this after seeing wrong colors to quickly add correction samples
"""
import json
import os
import pyautogui
import time

def collect_samples_for_color(color_name: str, num_samples: int = 20):
    """Quickly collect samples for a specific color"""
    print(f"\n{'='*60}")
    print(f"Collecting samples for: {color_name.upper()}")
    print(f"{'='*60}")
    print(f"\nClick on {color_name} pixels {num_samples} times")
    print("Press 'q' to quit early")
    
    samples = []
    count = 0
    
    try:
        from pynput import keyboard, mouse
        
        stop = False
        
        def on_press(key):
            nonlocal stop
            try:
                if key.char == 'q':
                    stop = True
                    return False
            except:
                pass
        
        def on_click(x, y, button, pressed):
            nonlocal count
            if pressed and button == mouse.Button.left:
                screenshot = pyautogui.screenshot()
                rgb = screenshot.getpixel((x, y))
                samples.append([int(rgb[0]), int(rgb[1]), int(rgb[2])])
                count += 1
                print(f"  [{count}/{num_samples}] RGB{rgb}")
                if count >= num_samples:
                    return False
        
        keyboard_listener = keyboard.Listener(on_press=on_press)
        mouse_listener = mouse.Listener(on_click=on_click)
        
        keyboard_listener.start()
        mouse_listener.start()
        
        while count < num_samples and not stop:
            time.sleep(0.1)
        
        keyboard_listener.stop()
        mouse_listener.stop()
        
    except ImportError:
        for i in range(num_samples):
            input(f"Click on {color_name} and press Enter ({i+1}/{num_samples})...")
            x, y = pyautogui.position()
            screenshot = pyautogui.screenshot()
            rgb = screenshot.getpixel((x, y))
            samples.append([int(rgb[0]), int(rgb[1]), int(rgb[2])])
    
    return samples

def main():
    """Quick training for specific colors"""
    print("="*60)
    print("QUICK FIX TRAINING")
    print("="*60)
    print("\nThis will help you quickly add training samples for colors that were wrong.")
    print("Focus on the colors that were misdetected.")
    
    # Load existing data
    data_file = 'training_data/color_samples.json'
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            training_data = json.load(f)
    else:
        training_data = {}
        os.makedirs('training_data', exist_ok=True)
    
    colors_to_fix = [
        'pink', 'red', 'orange', 'yellow', 'green', 'blue', 'gray'
    ]
    
    print("\nWhich colors need more training?")
    print("(Colors that were detected wrong)")
    
    fixed_colors = []
    
    for color in colors_to_fix:
        response = input(f"\nCollect more samples for {color}? (y/n): ").strip().lower()
        if response == 'y':
            samples = collect_samples_for_color(color, num_samples=25)
            if samples:
                if color not in training_data:
                    training_data[color] = []
                training_data[color].extend(samples)
                fixed_colors.append(color)
                print(f"✓ Added {len(samples)} samples for {color}")
                print(f"  Total samples for {color}: {len(training_data[color])}")
    
    if fixed_colors:
        # Save updated data
        with open(data_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        print(f"\n{'='*60}")
        print("TRAINING DATA UPDATED")
        print(f"{'='*60}")
        print(f"\nUpdated colors: {', '.join(fixed_colors)}")
        print(f"\nTotal samples per color:")
        for color, samples in training_data.items():
            print(f"  {color}: {len(samples)}")
        
        print("\n✓ Next step: Run 'python3 train_color_model.py' to retrain")
    else:
        print("\nNo samples collected.")

if __name__ == "__main__":
    main()

