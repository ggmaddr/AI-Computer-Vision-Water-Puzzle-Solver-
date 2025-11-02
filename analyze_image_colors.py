"""
Image Color Analyzer
Analyzes an image and determines HSV ranges and RGB values for specific colors
"""
import cv2
import numpy as np
from PIL import Image
import sys
from typing import Dict, List, Tuple

# Target colors to detect
TARGET_COLORS = ['pink', 'green', 'orange', 'red', 'gray', 'blue', 'yellow', 'darkbackground']

def rgb_to_hsv(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Convert RGB to HSV"""
    r, g, b = rgb
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val
    
    # Value
    v = int(max_val * 255)
    
    # Saturation
    if max_val == 0:
        s = 0
    else:
        s = int((diff / max_val) * 255)
    
    # Hue
    if diff == 0:
        h = 0
    elif max_val == r:
        h = int(((g - b) / diff) % 6) * 30
        if h < 0:
            h += 180
    elif max_val == g:
        h = int(((b - r) / diff) + 2) * 30
    else:  # max_val == b
        h = int(((r - g) / diff) + 4) * 30
    
    return (h, s, v)

def analyze_image_colors(image_path: str = None) -> Dict[str, Tuple]:
    """
    Analyze image and determine color values
    Returns dict with color names and their HSV ranges + RGB values
    """
    if image_path:
        # Load image from file
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
    else:
        # Capture screenshot
        import pyautogui
        screenshot = pyautogui.screenshot()
        image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    h, w = image.shape[:2]
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Dictionary to store color information
    color_data = {}
    
    # Analyze each target color
    for color_name in TARGET_COLORS:
        pixels = []
        
        # Sample pixels from the image (sample every Nth pixel for efficiency)
        # More sampling for better accuracy
        sample_rate = 5
        for y in range(0, h, sample_rate):
            for x in range(0, w, sample_rate):
                bgr = image[y, x]
                hsv = hsv_image[y, x]
                
                # Check if this pixel matches the color criteria
                if matches_color(color_name, hsv, bgr):
                    rgb = (int(bgr[2]), int(bgr[1]), int(bgr[0]))  # BGR to RGB
                    pixels.append((hsv, rgb))
        
        if pixels and len(pixels) > 10:  # Need at least 10 pixels to be valid
            # Calculate HSV ranges and average RGB
            hsv_values = np.array([p[0] for p in pixels])
            rgb_values = np.array([p[1] for p in pixels])
            
            h_vals = hsv_values[:, 0]
            s_vals = hsv_values[:, 1]
            v_vals = hsv_values[:, 2]
            
            # Get min/max ranges with some padding
            h_min = max(0, int(np.percentile(h_vals, 5)) - 5)
            h_max = min(180, int(np.percentile(h_vals, 95)) + 5)
            s_min = max(0, int(np.percentile(s_vals, 5)) - 10)
            s_max = min(255, int(np.percentile(s_vals, 95)) + 10)
            v_min = max(0, int(np.percentile(v_vals, 5)) - 10)
            v_max = min(255, int(np.percentile(v_vals, 95)) + 10)
            
            # Handle hue wrapping for red
            if h_min > h_max and color_name == 'red':
                # Red wraps around
                h_min = 0
                h_max = 180
            
            # Median RGB (more robust than mean)
            median_rgb = (int(np.median(rgb_values[:, 0])), 
                         int(np.median(rgb_values[:, 1])), 
                         int(np.median(rgb_values[:, 2])))
            
            color_data[color_name] = (
                ([h_min, s_min, v_min], [h_max, s_max, v_max], median_rgb),
                len(pixels)
            )
    
    return color_data

def matches_color(color_name: str, hsv: np.ndarray, bgr: np.ndarray) -> bool:
    """Check if a pixel matches a color category"""
    h, s, v = hsv
    b, g_val, r = bgr
    
    # Dark background: very dark colors (low value, any saturation)
    if color_name == 'darkbackground':
        return v < 60
    
    # Gray: low saturation, medium value (not too dark, not too bright)
    if color_name == 'gray':
        return s < 60 and 60 <= v <= 200 and r > 30 and g_val > 30 and b > 30
    
    # Red: hue around 0-10 or 170-180, high saturation, medium-high value
    if color_name == 'red':
        return ((h <= 10 or h >= 170) and s > 40 and v > 80 and r > g_val and r > b)
    
    # Orange: hue around 10-25, high saturation, medium-high value
    if color_name == 'orange':
        return (10 <= h <= 25 and s > 60 and v > 100 and r > 100)
    
    # Yellow: hue around 20-35, high saturation, high value
    if color_name == 'yellow':
        return (20 <= h <= 35 and s > 80 and v > 150 and r > 150 and g_val > 150)
    
    # Green: hue around 35-85, high saturation, medium-high value
    if color_name == 'green':
        return (35 <= h <= 85 and s > 40 and v > 80 and g_val > r and g_val > b)
    
    # Blue: hue around 85-130, high saturation, medium-high value
    if color_name == 'blue':
        return (85 <= h <= 130 and s > 50 and v > 80 and b > r and b > g_val)
    
    # Pink: hue around 160-180, medium-high saturation, high value
    if color_name == 'pink':
        return (160 <= h <= 180 and s > 50 and v > 120 and r > 100)
    
    return False

def main():
    """Main function"""
    print("=" * 60)
    print("IMAGE COLOR ANALYZER")
    print("=" * 60)
    print("\nThis will analyze an image to determine color HSV ranges and RGB values.")
    print("Detecting colors: pink, green, orange, red, gray, blue, yellow, darkbackground")
    print()
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"Analyzing image: {image_path}")
        color_data = analyze_image_colors(image_path)
    else:
        print("No image path provided. Capturing screenshot...")
        print("(You can also provide image path as argument: python3 analyze_image_colors.py image.jpg)")
        color_data = analyze_image_colors()
    
    # Print only the colors found, in the exact format requested
    for color_name in TARGET_COLORS:
        if color_name in color_data:
            data_tuple, pixel_count = color_data[color_name]
            hsv_min, hsv_max, rgb = data_tuple
            h_min, s_min, v_min = hsv_min
            h_max, s_max, v_max = hsv_max
            r, g, b = rgb
            
            print(f"'{color_name}': ([{h_min}, {s_min}, {v_min}], [{h_max}, {s_max}, {v_max}], ({r}, {g}, {b}));")

if __name__ == "__main__":
    main()

