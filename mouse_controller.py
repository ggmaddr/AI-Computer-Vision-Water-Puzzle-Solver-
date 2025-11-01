"""
Mouse Controller for Water Sort Puzzle
Handles mouse interactions with the game
"""
import pyautogui
import time
from typing import List, Tuple
import numpy as np


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
    
    def click_tube(self, tube_index: int, delay: float = 0.2):
        """
        Click on a tube
        Args:
            tube_index: Index of tube to click
            delay: Delay after clicking
        """
        x, y = self.get_tube_center(tube_index)
        pyautogui.click(x, y)
        time.sleep(delay)
    
    def pour_tube(self, from_tube: int, to_tube: int, delay: float = 0.3):
        """
        Pour from one tube to another by clicking both
        Args:
            from_tube: Index of source tube
            to_tube: Index of destination tube
            delay: Delay between clicks
        """
        self.click_tube(from_tube, delay=0.1)
        time.sleep(delay)
        self.click_tube(to_tube, delay=0.1)
        time.sleep(delay)
    
    def execute_moves(self, moves: List[Tuple[int, int]], delay_between_moves: float = 0.5):
        """
        Execute a sequence of moves
        Args:
            moves: List of (from_tube, to_tube) tuples
            delay_between_moves: Delay between each move
        """
        print(f"\nExecuting {len(moves)} moves...")
        for i, (from_tube, to_tube) in enumerate(moves, 1):
            print(f"Move {i}/{len(moves)}: Pouring from tube {from_tube} to tube {to_tube}")
            self.pour_tube(from_tube, to_tube, delay=delay_between_moves)
        
        print("All moves executed!")
    
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

