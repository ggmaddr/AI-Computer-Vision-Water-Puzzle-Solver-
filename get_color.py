"""
Get Color at Mouse Position
Prints RGB and HSV color values at mouse cursor every 2 seconds
Press 's' + Enter to stop
"""
import pyautogui
import cv2
import numpy as np
import time
import threading

# Global flag for stopping
stop_flag = False

def handle_user_input():
    """Handle user input in a separate thread"""
    global stop_flag
    try:
        while not stop_flag:
            user_input = input().strip().lower()
            if user_input == 's':
                stop_flag = True
                break
    except:
        pass

print("=" * 60)
print("GET COLOR AT MOUSE POSITION")
print("=" * 60)
print("\nThis will print the color at your mouse cursor every 2 seconds.")
print("The format shows HSV ranges and RGB tuple: ([H_min, S_min, V_min], [H_max, S_max, V_max], (R, G, B))")
print("\nPress 's' + Enter to stop\n")
print("-" * 60)

# Start thread to listen for 's' key
input_thread = threading.Thread(target=handle_user_input, daemon=True)
input_thread.start()

count = 0
print("Starting... Move your mouse to see color values.")
print("Press 's' + Enter to stop\n")

try:
    while not stop_flag:
        # Get current mouse position
        pos = pyautogui.position()
        x, y = pos.x, pos.y
        
        # Get pixel color at mouse position
        # pyautogui doesn't have direct pixel reading, so we'll use screenshot
        screenshot = pyautogui.screenshot()
        rgb = screenshot.getpixel((x, y))
        
        # Convert RGB to BGR for OpenCV (it uses BGR format)
        bgr = (rgb[2], rgb[1], rgb[0])
        
        # Convert to HSV
        bgr_array = np.array([[bgr]], dtype=np.uint8)
        hsv_array = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2HSV)
        h, s, v = hsv_array[0][0]
        
        count += 1
        
        # Create HSV range (approximate ±10 for hue, ±30 for saturation/value)
        # For hue, handle wrapping (red is at both ends)
        h_min = max(0, h - 10)
        h_max = min(180, h + 10)
        
        s_min = max(0, s - 30)
        s_max = min(255, s + 30)
        
        v_min = max(0, v - 30)
        v_max = min(255, v + 30)
        
        # Print in the requested format
        print(f"[{count}] Mouse at ({x}, {y}):")
        print(f"  HSV: H={h}, S={s}, V={v}")
        print(f"  RGB: R={rgb[0]}, G={rgb[1]}, B={rgb[2]}")
        print(f"  Format: ([{h_min}, {s_min}, {v_min}], [{h_max}, {s_max}, {v_max}], {rgb})")
        print()
        
        # Wait 2 seconds (check stop_flag during wait)
        for _ in range(20):
            if stop_flag:
                break
            time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\n\nInterrupted by user.")
    stop_flag = True

if stop_flag:
    print("\n\nStopped by user.")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)

