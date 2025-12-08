"""
Main Application for AI Water Sort Puzzle Solver
Orchestrates image capture, puzzle solving, and mouse automation
"""
import time
import sys
from typing import Tuple, List
from image_processor import ImageProcessor
from puzzle_solver import PuzzleSolver
from mouse_controller import MouseController
import pyautogui


class WaterSortSolverApp:
    """Main application for solving water sort puzzles"""
    
    def __init__(self):
        self.image_processor = None
        self.mouse_controller = None
        self.game_region = None
        self.tube_positions = None
    
    def setup_game_region(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Get game screen region from user by clicking corners
        Returns: (top_left, bottom_right) tuples
        """
        print("=" * 60)
        print("Step 1: Define Game Screen Region")
        print("=" * 60)
        print("\nPlease click on the TOP-LEFT corner of the game screen...")
        print("You have 0.5 seconds to position your mouse, then click...")
        time.sleep(0.5)
        
        # Wait for mouse click
        top_left = self._wait_for_click()
        print(f"Top-left corner recorded: {top_left}")
        
        print("\nPlease click on the BOTTOM-RIGHT corner of the game screen...")
        print("You have 0.5 seconds to position your mouse, then click...")
        time.sleep(0.5)
        
        bottom_right = self._wait_for_click()
        print(f"Bottom-right corner recorded: {bottom_right}")
        
        if top_left[0] >= bottom_right[0] or top_left[1] >= bottom_right[1]:
            print("ERROR: Invalid region! Top-left must be above and left of bottom-right.")
            sys.exit(1)
        
        return top_left, bottom_right
    
    def _wait_for_click(self) -> Tuple[int, int]:
        """Wait for user mouse click and return position"""
        try:
            from pynput import mouse
            
            clicked_pos = None
            clicked = False
            
            def on_click(x, y, button, pressed):
                nonlocal clicked_pos, clicked
                if pressed and button == mouse.Button.left:
                    clicked_pos = (int(x), int(y))  # Ensure integers
                    clicked = True
                    return False  # Stop listener
            
            listener = mouse.Listener(on_click=on_click)
            listener.start()
            
            # Wait for click (max 10 seconds)
            start_time = time.time()
            while not clicked and (time.time() - start_time) < 10:
                time.sleep(0.1)
            
            listener.stop()
            
            if clicked and clicked_pos:
                return clicked_pos
            else:
                # Fallback: use current position
                pos = pyautogui.position()
                return (int(pos[0]), int(pos[1]))
        except ImportError:
            # Fallback: use keyboard input
            input("Press Enter after positioning mouse...")
            pos = pyautogui.position()
            return (int(pos[0]), int(pos[1]))
    
    def analyze_puzzle(self, silent: bool = False) -> dict:
        """
        Capture and analyze current puzzle state
        Returns: Puzzle parameters dict
        """
        if not silent:
            print("\n" + "=" * 60)
            print("Step 2: Analyzing Puzzle")
            print("=" * 60)
            
            print("Capturing screenshot...")
        
        image = self.image_processor.capture_screen()
        
        if not silent:
            print("Detecting tubes and extracting colors...")
        
        puzzle_state = self.image_processor.analyze_puzzle(image)
        
        # Store tube positions for mouse control
        tubes = self.image_processor.detect_tubes(image)
        if not tubes:
            tubes = self.image_processor._detect_tubes_grid(image)
        
        # Validate that we detected the correct number of tubes
        expected_tubes = puzzle_state['totalTube']
        if len(tubes) != expected_tubes:
            if not silent:
                print(f"\n⚠️  WARNING: Detected {len(tubes)} tube positions but puzzle has {expected_tubes} tubes!")
                print("This may cause errors. Trying to continue anyway...")
        
        self.tube_positions = tubes
        
        # Update mouse controller with new tube positions (important after each round)
        if self.mouse_controller:
            x1, y1 = self.game_region[0], self.game_region[1]
            x2, y2 = self.game_region[2], self.game_region[3]
            self.mouse_controller.tube_positions = tubes
            self.mouse_controller.game_region = (x1, y1, x2, y2)
        
        # if not silent:
        #     print(f"\nPuzzle Analysis Results:")
        #     print(f"  Total Tubes: {puzzle_state['totalTube']}")
        #     print(f"  Empty Tubes: {puzzle_state['emptyTubeNumbers']}")
        #     print(f"  Filled Tubes: {len([t for t in puzzle_state['filledTubelist'] if t])}")
            
        #     print("\nTube Contents (bottom to top):")
        #     for i, tube in enumerate(puzzle_state['filledTubelist']):
        #         if tube:
        #             print(f"  Tube {i}: {tube}")
        #         else:
        #             print(f"  Tube {i}: [empty]")
        
        return puzzle_state
    
    def solve_puzzle(self, puzzle_state: dict) -> List[Tuple[int, int]]:
        """
        Solve the puzzle
        Returns: List of (from_tube, to_tube) moves
        """
        print("\n" + "=" * 60)
        print("Step 3: Solving Puzzle")
        print("=" * 60)
        
        solver = PuzzleSolver(
            puzzle_state['totalTube'],
            puzzle_state['emptyTubeNumbers'],
            puzzle_state['filledTubelist'],
            debug=True  # Enable detailed logging
        )
        
        solution = solver.solve_with_limits(max_moves=500, max_depth=100)
        
        if not solution:
            print("ERROR: Could not find solution!")
            return None
        
        return solution
    
    def execute_solution(self, moves: List[Tuple[int, int]]):
        """
        Execute the solution using mouse automation
        """
        # Validate that all tube indices in moves are within range
        max_tube_index = max(max(from_tube, to_tube) for from_tube, to_tube in moves) if moves else -1
        if max_tube_index >= len(self.tube_positions):
            raise ValueError(
                f"Solution contains tube index {max_tube_index} but only {len(self.tube_positions)} "
                f"tubes detected. Puzzle analysis may be incorrect."
            )
        
        # Always recreate mouse controller with current tube positions
        # This ensures we have the correct positions after each round
        x1, y1 = self.game_region[0], self.game_region[1]
        x2, y2 = self.game_region[2], self.game_region[3]
        self.mouse_controller = MouseController(
            (x1, y1, x2, y2),
            self.tube_positions
        )
        
        print("Starting in 3 seconds... Move mouse to corner to abort (failsafe)...")
        time.sleep(3)
        
        self.mouse_controller.execute_moves(moves, delay_between_moves=0.8)
    
    def check_if_solved(self) -> bool:
        """Check if puzzle is solved by analyzing current state"""
        puzzle_state = self.analyze_puzzle()
        solver = PuzzleSolver(
            puzzle_state['totalTube'],
            puzzle_state['emptyTubeNumbers'],
            puzzle_state['filledTubelist']
        )
        
        return solver.is_solved(puzzle_state['filledTubelist'])
    
    def run(self):
        """Main application loop"""
        print("\n" + "=" * 60)
        print("AI Water Sort Puzzle Solver")
        print("=" * 60)
        print("\nThis application will:")
        print("1. Ask you to define the game screen region")
        print("2. Calibrate unit height (click top and bottom of one block)")
        print("3. Analyze the puzzle from a screenshot")
        print("4. Solve the puzzle")
        print("5. Automatically play the moves")
        print("\nNote: Keep the game visible on screen!")
        
        input("\nPress Enter to start...")
        # Step 1: Get Next button position
        print("\n" + "=" * 60)
        print("Step 1: Click the Next Button")
        print("=" * 60)
        print("Please click on the Next button (you can click it now or wait for it to appear)")
        #wait for click or press enter to continue, if press enter, next_button_pos = (242, 565) by default
        next_button_pos = (242, 565)
        response = input("Press Enter to use default position, or position mouse and press Enter...")
        if response == "":
            next_button_pos = (242, 565)
        else:
            next_button_pos = self._wait_for_click()
        
        self.next_button_pos = next_button_pos
        print(f"✓ Next button position saved: {next_button_pos}")
    
        self.start_button_pos = (360, 243)
        
        # Step 2: Setup game region
        print("\n" + "=" * 60)
        print("Step 2: Define Game Region")
        print("=" * 60)
        top_left, bottom_right = self.setup_game_region()
        x1, y1 = int(top_left[0]), int(top_left[1])
        x2, y2 = int(bottom_right[0]), int(bottom_right[1])
        self.game_region = (x1, y1, x2, y2)
        
        # Initialize image processor
        self.image_processor = ImageProcessor(self.game_region)
        
        # Number of rounds before clicking Start button instead of Next
        nround = 42
        
        # Main loop: solve and play until win
        round_number = 1
        
        while True:
            print(f"\n{'=' * 60}")
            print(f"ROUND {round_number}")
            print(f"{'=' * 60}")
            
            # Set turn number for logging
            self.image_processor.set_turn(round_number)
            
            # Step 2: Analyze puzzle
            puzzle_state = self.analyze_puzzle()
            
            # Step 3: Solve
            solution = self.solve_puzzle(puzzle_state)
            
            if not solution:
                print("\nCannot solve this puzzle. Please check manually.")
                break
            
            # Step 4: Execute
            self.execute_solution(solution)
            
            # Wait 2 seconds for button to appear
            time.sleep(2)
            
            # Determine which button to click based on round number
            import pyautogui

            # Click Next button for other rounds
            print(f"Clicking Next button (round {round_number})")
            pyautogui.moveTo(self.next_button_pos[0], self.next_button_pos[1], duration=0.5)
            pyautogui.click(self.next_button_pos[0], self.next_button_pos[1])
            time.sleep(2)
            round_number += 1
            if round_number % nround == 0:
                # Click Start button every nround rounds (41, 82, 123, etc.)
                print(f"Round {round_number} is a multiple of {nround} - clicking Start button")
                pyautogui.moveTo(self.start_button_pos[0], self.start_button_pos[1], duration=0.5)
                pyautogui.click(self.start_button_pos[0], self.start_button_pos[1])
                time.sleep(2)
                    
        print("\n" + "=" * 60)
        print("Application finished. Thank you!")
        print("=" * 60)


def main():
    """Entry point"""
    app = WaterSortSolverApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

