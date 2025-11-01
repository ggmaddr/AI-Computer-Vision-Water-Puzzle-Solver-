"""
Quick Mouse Test - Simple version
Continuously prints mouse position every 3 seconds
Press 'm' to move mouse to coordinates and click
Press 's' to stop
"""
import pyautogui
import time
import threading

# Global flags
stop_flag = False
move_mode = False
pause_tracking = False

def handle_user_input():
    """Handle user input in a separate thread"""
    global stop_flag, move_mode, pause_tracking
    try:
        while not stop_flag:
            user_input = input().strip().lower()
            
            if user_input == 's':
                stop_flag = True
                break
            elif user_input == 'm':
                move_mode = True
                pause_tracking = True
                break
    except:
        pass

def move_and_click_mode():
    """Handle move and click mode"""
    global stop_flag, pause_tracking
    screen_width, screen_height = pyautogui.size()
    
    while True:
        try:
            # Get coordinates
            print("\n" + "=" * 60)
            print("MOVE AND CLICK MODE")
            print("=" * 60)
            coord_input = input("Enter coordinates (x,y): ").strip()
            
            if ',' not in coord_input:
                print("Invalid format. Use: x,y (e.g., 500,300)")
                continue
            
            x_str, y_str = coord_input.split(',')
            x = int(x_str.strip())
            y = int(y_str.strip())
            
            if x < 0 or y < 0 or x > screen_width or y > screen_height:
                print(f"Warning: Coordinates outside screen ({screen_width}x{screen_height})")
                proceed = input("Continue anyway? (y/n): ").strip().lower()
                if proceed != 'y':
                    continue
            
            # Move mouse to position
            print(f"\n📍 Moving mouse to ({x}, {y})...")
            pyautogui.moveTo(x, y, duration=1.0)
            time.sleep(0.3)
            
            # Draw a circle around the point to make it visible
            import math
            radius = 15
            for angle in range(0, 361, 30):
                rad = math.radians(angle)
                cx = int(x + radius * math.cos(rad))
                cy = int(y + radius * math.sin(rad))
                pyautogui.moveTo(cx, cy, duration=0.05)
            
            # Return to center and click
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.2)
            
            print(f"🖱️  Clicking at ({x}, {y})...")
            # pyautogui.mouseDown(button='left')
            pyautogui.doubleClick()
            # time.sleep(0.5)
            # pyautogui.mouseUp(button='left')
            print(f"✓ Clicked!")
            
            # Wait for next action
            print("\n" + "-" * 60)
            print("What would you like to do next?")
            print("  M - Move and click again")
            print("  S - Stop program")
            print("  R - Resume printing mouse position")
            print("-" * 60)
            
            while True:
                action = input("Enter choice (M/S/R): ").strip().upper()
                
                if action == 'M':
                    break  # Continue loop to ask for new coordinates
                elif action == 'S':
                    stop_flag = True
                    return
                elif action == 'R':
                    pause_tracking = False
                    return
                else:
                    print("Invalid choice. Enter M, S, or R.")
            
        except ValueError:
            print("Invalid coordinates. Use numbers like: 500,300")
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            stop_flag = True
            return
        except Exception as e:
            print(f"Error: {e}")

print("=" * 60)
print("QUICK MOUSE TEST")
print("=" * 60)
print("\nThis will continuously print mouse position every 3 seconds.")
print("\nControls:")
print("  'm' - Enter move and click mode")
print("  's' - Stop the program")
print("-" * 60)

# Get screen size
screen_width, screen_height = pyautogui.size()
print(f"Screen size: {screen_width} x {screen_height}\n")

# Start thread to listen for user input
input_thread = threading.Thread(target=handle_user_input, daemon=True)
input_thread.start()

# Continuously print mouse position every 3 seconds
count = 0
print("Tracking started...")
print("Type 'm' + Enter to move/click, or 's' + Enter to stop\n")

try:
    while not stop_flag:
        # Check if we should pause tracking
        if move_mode:
            move_and_click_mode()
            move_mode = False  # Reset for next time
            # Restart input thread if we're resuming
            if not stop_flag and not pause_tracking:
                input_thread = threading.Thread(target=handle_user_input, daemon=True)
                input_thread.start()
        
        if pause_tracking or move_mode:
            time.sleep(0.1)
            continue
        
        # Get current mouse position
        current_pos = pyautogui.position()
        count += 1
        
        # Print with count and position
        print(f"[{count}] Mouse position: ({current_pos.x}, {current_pos.y})")
        
        # Wait 3 seconds (check flags during wait)
        for _ in range(30):  # Check 10 times per second
            if stop_flag or move_mode:
                break
            time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\n\nInterrupted by user.")
    stop_flag = True

if stop_flag:
    print("\n\nStopping...")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)

# Final check
final_pos = pyautogui.position()
print(f"\nFinal mouse position: ({final_pos.x}, {final_pos.y})")

print("\nTroubleshooting if mouse didn't move:")
print("1. macOS: System Settings > Privacy & Security > Accessibility")
print("2. Add Terminal or Python to allowed apps")
print("3. Make sure pyautogui is installed: pip3 install pyautogui")
print("4. Try running with: python3 quick_mouse_test.py")

