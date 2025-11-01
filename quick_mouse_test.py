"""
Quick Mouse Test - Simple version
Just enter coordinates and see mouse move
"""
import pyautogui
import time

print("=" * 60)
print("QUICK MOUSE TEST")
print("=" * 60)
print("\nThis will move your mouse to test if pyautogui works.")
print("Watch your screen carefully!\n")

# Get screen size
screen_width, screen_height = pyautogui.size()
print(f"Screen size: {screen_width} x {screen_height}")

current_pos = pyautogui.position()
print(f"Current mouse position: {current_pos}\n")

# Test 1: Move to center of screen
print("Test 1: Moving to center of screen...")
center_x = screen_width // 2
center_y = screen_height // 2
print(f"Moving to ({center_x}, {center_y})...")
pyautogui.moveTo(center_x, center_y, duration=2.0)
print("✓ Mouse should be at center. Did you see it move?")
input("\nPress Enter to continue...")

# Test 2: Draw visible cross
print("\nTest 2: Drawing a cross pattern...")
x, y = center_x, center_y
size = 100

# Draw a large cross
points = [
    (x - size, y),      # Left
    (x + size, y),      # Right  
    (x, y),             # Center
    (x, y - size),      # Top
    (x, y + size),      # Bottom
    (x, y)              # Back to center
]

for i, (px, py) in enumerate(points):
    print(f"  Point {i+1}: ({px}, {py})")
    pyautogui.moveTo(px, py, duration=0.5)
    time.sleep(0.2)

print("✓ Cross drawn. Did you see it?")
input("\nPress Enter to continue...")

# Test 3: User input coordinates
print("\n" + "=" * 60)
print("Test 3: Enter your own coordinates")
print("=" * 60)

while True:
    try:
        user_input = input("\nEnter x,y coordinates (or 'q' to quit): ").strip()
        
        if user_input.lower() == 'q':
            break
        
        if ',' not in user_input:
            print("Format: x,y (e.g., 500,300)")
            continue
        
        x_str, y_str = user_input.split(',')
        x = int(x_str.strip())
        y = int(y_str.strip())
        
        if x < 0 or y < 0 or x > screen_width or y > screen_height:
            print(f"Warning: Coordinates outside screen ({screen_width}x{screen_height})")
            proceed = input("Continue anyway? (y/n): ").strip().lower()
            if proceed != 'y':
                continue
        
        print(f"\n📍 Moving mouse to ({x}, {y})...")
        
        # Move in a visible way - first fast, then slow
        pyautogui.moveTo(x, y, duration=1.5)
        
        # Draw a circle around the point
        import math
        radius = 20
        for angle in range(0, 361, 45):
            rad = math.radians(angle)
            cx = int(x + radius * math.cos(rad))
            cy = int(y + radius * math.sin(rad))
            pyautogui.moveTo(cx, cy, duration=0.1)
        
        # Return to center
        pyautogui.moveTo(x, y, duration=0.2)
        
        print(f"✓ Mouse positioned at ({x}, {y})")
        print("Did you see the mouse move?")
        
        click = input("Click here? (y/n): ").strip().lower()
        if click == 'y':
            # Flash before clicking
            for _ in range(3):
                pyautogui.moveTo(x - 5, y, duration=0.05)
                pyautogui.moveTo(x + 5, y, duration=0.05)
                pyautogui.moveTo(x, y, duration=0.05)
            pyautogui.click()
            print(f"✓ Clicked at ({x}, {y})")
        
    except ValueError:
        print("Invalid input. Use numbers like: 500,300")
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
        break
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)

# Final check
final_pos = pyautogui.position()
print(f"\nFinal mouse position: {final_pos}")

print("\nTroubleshooting if mouse didn't move:")
print("1. macOS: System Settings > Privacy & Security > Accessibility")
print("2. Add Terminal or Python to allowed apps")
print("3. Make sure pyautogui is installed: pip3 install pyautogui")
print("4. Try running with: python3 quick_mouse_test.py")

