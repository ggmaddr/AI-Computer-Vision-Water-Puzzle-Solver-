"""
Mouse Controller for Water Sort Puzzle
Handles mouse interactions with the game
"""
import pyautogui
import time
from typing import List, Tuple
import numpy as np
import sys


class MouseController:
    """Controls mouse to interact with water sort puzzle game"""
    
    def __init__(self, game_region: Tuple[int, int, int, int], tube_positions: List[Tuple[int, int, int, int]]):
        """
        Initialize mouse controller
        Args:
            game_region: (x1, y1, x2, y2) coordinates of game area
            tube_positions: List of (x, y, width, height) for each tube
        """
        self.game_region = game_region
        self.tube_positions = tube_positions
        pyautogui.PAUSE = 0.1  # Small pause between actions
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        self.debug = True  # Enable debug mode for visual feedback
    
    def get_tube_center(self, tube_index: int) -> Tuple[int, int]:
        """Get center coordinates of a tube in screen coordinates"""
        if tube_index >= len(self.tube_positions):
            raise ValueError(f"Tube index {tube_index} out of range")
        
        x1, y1, x2, y2 = self.game_region
        x1, y1 = int(x1), int(y1)  # Ensure integers
        tube_x, tube_y, tube_w, tube_h = self.tube_positions[tube_index]
        tube_x, tube_y = int(tube_x), int(tube_y)
        tube_w, tube_h = int(tube_w), int(tube_h)
        
        # Convert to screen coordinates
        screen_x = int(x1 + tube_x + tube_w // 2)
        screen_y = int(y1 + tube_y + tube_h // 2)
        
        return (screen_x, screen_y)
    
    def _draw_click_indicator(self, x: int, y: int, color: str = "red"):
        """
        Draw a visual indicator at click position using keyboard/mouse tricks
        This creates a visible indication on screen
        """
        try:
            # Move mouse in a small circle to make it visible
            # This draws attention to the click location
            radius = 5
            steps = 4
            for i in range(steps):
                angle = (2 * 3.14159 * i) / steps
                offset_x = int(radius * (1 if i % 2 == 0 else -1))
                offset_y = int(radius * (1 if i % 2 == 0 else -1))
                pyautogui.moveTo(x + offset_x, y + offset_y, duration=0.05)
            # Return to center
            pyautogui.moveTo(x, y, duration=0.1)
        except:
            pass  # If anything fails, just continue
    
    def click_tube(self, tube_index: int, delay: float = 0.2):
        """
        Click on a tube with visual feedback
        Args:
            tube_index: Index of tube to click
            delay: Delay after clicking
        """
        x, y = self.get_tube_center(tube_index)
        
        if self.debug:
            # Move to position first so user can see where we're going
            current_pos = pyautogui.position()
            print(f"\033[93m📍 Moving mouse to Tube {tube_index}: ({x}, {y})\033[0m", end="", flush=True)
            pyautogui.moveTo(x, y, duration=0.5)  # Slower, more visible movement
            self._draw_click_indicator(x, y, "yellow")  # Draw attention
            time.sleep(0.3)  # Pause so user can see position
            print(f" \033[92m✓ Positioned\033[0m")
            
            # Show click with visual feedback - flash red before clicking
            print(f"\033[91m🖱️  CLICKING at ({x}, {y})...\033[0m", end="", flush=True)
            # Flash indicator in red before click
            self._draw_click_indicator(x, y, "red")
            time.sleep(0.1)
        
        pyautogui.click(x, y)
        
        if self.debug:
            print(f" \033[92m✓ Clicked!\033[0m")
            # Flash green after click to confirm
            self._draw_click_indicator(x, y, "green")
        
        time.sleep(delay)
    
    def pour_tube(self, from_tube: int, to_tube: int, delay: float = 0.3):
        """
        Pour from one tube to another by clicking both
        Args:
            from_tube: Index of source tube
            to_tube: Index of destination tube
            delay: Delay between clicks
        """
        if self.debug:
            print(f"\n\033[96m🔄 Pouring: Tube {from_tube} → Tube {to_tube}\033[0m")
        
        self.click_tube(from_tube, delay=0.1)
        time.sleep(delay)
        self.click_tube(to_tube, delay=0.1)
        time.sleep(delay)
    
    def execute_moves(self, moves: List[Tuple[int, int]], delay_between_moves: float = 0.5):
        """
        Execute a sequence of moves with visual feedback
        Args:
            moves: List of (from_tube, to_tube) tuples
            delay_between_moves: Delay between each move
        """
        print(f"\n\033[95m{'='*60}\033[0m")
        print(f"\033[95m🎯 Executing {len(moves)} moves...\033[0m")
        print(f"\033[95m{'='*60}\033[0m\n")
        
        for i, (from_tube, to_tube) in enumerate(moves, 1):
            print(f"\033[94m━━━ Move {i}/{len(moves)} ━━━\033[0m")
            self.pour_tube(from_tube, to_tube, delay=delay_between_moves)
            if i < len(moves):
                print()  # Blank line between moves
        
        print(f"\n\033[92m{'='*60}\033[0m")
        print(f"\033[92m✓ All {len(moves)} moves executed successfully!\033[0m")
        print(f"\033[92m{'='*60}\033[0m")
    
    def wait_for_user_input(self, message: str = "") -> Tuple[int, int]:
        """
        Wait for user to click on screen
        Returns: (x, y) coordinates of click
        """
        if message:
            print(message)
        
        print("Waiting for mouse click...")
        
        # Store original position
        original_pos = pyautogui.position()
        
        # Wait for mouse button press
        try:
            import mouse
            click_pos = mouse.get_position()
            # Wait for actual click
            event = mouse.wait()
            if event.event_type == 'down':
                click_pos = mouse.get_position()
        except ImportError:
            # Fallback: use keyboard input
            input("Press Enter after clicking the desired position...")
            click_pos = pyautogui.position()
        
        return click_pos
    
    @staticmethod
    def get_click_position() -> Tuple[int, int]:
        """
        Get current mouse position (for user to click and we record it)
        Uses a simple method - user clicks and we read position
        """
        print("Click now...")
        time.sleep(1)  # Give user time to position mouse
        return pyautogui.position()

