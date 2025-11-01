"""
Simple Mouse Controller Test
Test mouse movement and clicking to verify pyautogui works
"""
import pyautogui
import time

def test_mouse_movement():
    """Test mouse movement and clicking"""
    print("=" * 60)
    print("Mouse Controller Test")
    print("=" * 60)
    print("\nThis will test mouse movement and clicking.")
    print("Watch your screen - the mouse should move visibly.")
    print("\n⚠️  To abort: Move mouse to top-left corner (0,0)\n")
    
    # Get current position
    current = pyautogui.position()
    print(f"Current mouse position: {current}")
    
    input("Press Enter to start test...")
    
    # Test 1: Move to a specific position
    print("\n" + "=" * 60)
    print("Test 1: Move mouse to position (500, 500)")
    print("=" * 60)
    print("Moving mouse...")
    pyautogui.moveTo(500, 500, duration=2.0)  # Slow movement so you can see it
    print("✓ Mouse should be at (500, 500)")
    time.sleep(1)
    
    # Test 2: Draw a visible pattern
    print("\n" + "=" * 60)
    print("Test 2: Draw a square pattern")
    print("=" * 60)
    start_x, start_y = 600, 600
    
    print("Drawing square pattern at (600, 600)...")
    points = [
        (start_x - 50, start_y - 50),  # Top-left
        (start_x + 50, start_y - 50),  # Top-right
        (start_x + 50, start_y + 50),  # Bottom-right
        (start_x - 50, start_y + 50),  # Bottom-left
        (start_x - 50, start_y - 50),  # Back to start
        (start_x, start_y)  # Center
    ]
    
    for i, (x, y) in enumerate(points):
        print(f"  Moving to point {i+1}: ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.5)
        time.sleep(0.3)
    
    print("✓ Square pattern drawn")
    time.sleep(1)
    
    # Test 3: Draw a circle
    print("\n" + "=" * 60)
    print("Test 3: Draw a circle pattern")
    print("=" * 60)
    center_x, center_y = 700, 700
    radius = 50
    num_points = 16
    
    print(f"Drawing circle at ({center_x}, {center_y}) with radius {radius}...")
    import math
    for i in range(num_points + 1):
        angle = (2 * math.pi * i) / num_points
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        print(f"  Point {i+1}/{num_points+1}: ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)
    
    print("✓ Circle pattern drawn")
    time.sleep(1)
    
    # Test 4: Click test
    print("\n" + "=" * 60)
    print("Test 4: Click test (will click at current position)")
    print("=" * 60)
    pos = pyautogui.position()
    print(f"Current position: {pos}")
    input("Press Enter to perform 3 clicks (watch carefully)...")
    
    for i in range(3):
        print(f"  Click {i+1}/3...")
        # Draw a small cross before clicking
        x, y = pos[0], pos[1]
        pyautogui.moveTo(x - 10, y, duration=0.1)
        pyautogui.moveTo(x + 10, y, duration=0.1)
        pyautogui.moveTo(x, y - 10, duration=0.1)
        pyautogui.moveTo(x, y + 10, duration=0.1)
        pyautogui.moveTo(x, y, duration=0.1)
        time.sleep(0.2)
        pyautogui.click()
        print(f"    ✓ Clicked at ({x}, {y})")
        time.sleep(0.5)
    
    # Test 5: Interactive coordinate input
    print("\n" + "=" * 60)
    print("Test 5: Interactive - Enter coordinates")
    print("=" * 60)
    
    while True:
        try:
            coord_input = input("\nEnter coordinates (x,y) or 'q' to quit: ").strip()
            if coord_input.lower() == 'q':
                break
            
            if ',' in coord_input:
                x_str, y_str = coord_input.split(',')
                x = int(x_str.strip())
                y = int(y_str.strip())
                
                print(f"Moving mouse to ({x}, {y})...")
                pyautogui.moveTo(x, y, duration=1.0)
                time.sleep(0.5)
                
                click = input("Click here? (y/n): ").strip().lower()
                if click == 'y':
                    # Draw attention with pattern
                    for offset in [(-10, 0), (10, 0), (0, -10), (0, 10), (0, 0)]:
                        pyautogui.moveTo(x + offset[0], y + offset[1], duration=0.1)
                    pyautogui.click()
                    print(f"✓ Clicked at ({x}, {y})")
            else:
                print("Invalid format. Use: x,y (e.g., 500,500)")
        except ValueError:
            print("Invalid coordinates. Use numbers like: 500,500")
        except KeyboardInterrupt:
            break
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    print("\nIf you saw the mouse move, pyautogui is working correctly.")
    print("If you didn't see anything:")
    print("  1. Check if accessibility permissions are granted")
    print("  2. Make sure you're on macOS (Settings > Security > Accessibility)")
    print("  3. Try running with: python3 test_mouse.py")

if __name__ == "__main__":
    # Configure pyautogui
    pyautogui.PAUSE = 0.1
    pyautogui.FAILSAFE = True
    
    print("\n⚠️  FAILSAFE: Move mouse to top-left corner (0,0) to abort")
    print("   PyAutoGUI will raise an exception if mouse goes to corner\n")
    
    try:
        test_mouse_movement()
    except pyautogui.FailSafeException:
        print("\n\n⚠️  FAILSAFE triggered! Mouse moved to corner.")
        print("Test aborted for safety.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check macOS Accessibility permissions")
        print("2. Terminal might need to be added to allowed apps")
        print("3. Try: System Settings > Privacy & Security > Accessibility")

