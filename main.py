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
        print("You have 5 seconds to position your mouse, then click...")
        time.sleep(2)
        
        # Wait for mouse click
        top_left = self._wait_for_click()
        print(f"Top-left corner recorded: {top_left}")
        
        print("\nPlease click on the BOTTOM-RIGHT corner of the game screen...")
        print("You have 5 seconds to position your mouse, then click...")
        time.sleep(2)
        
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
    
    def analyze_puzzle(self) -> dict:
        """
        Capture and analyze current puzzle state
        Returns: Puzzle parameters dict
        """
        print("\n" + "=" * 60)
        print("Step 2: Analyzing Puzzle")
        print("=" * 60)
        
        print("Capturing screenshot...")
        image = self.image_processor.capture_screen()
        
        print("Detecting tubes and extracting colors...")
        puzzle_state = self.image_processor.analyze_puzzle(image)
        
        # Store tube positions for mouse control
        tubes = self.image_processor.detect_tubes(image)
        if not tubes:
            tubes = self.image_processor._detect_tubes_grid(image)
        self.tube_positions = tubes
        
        print(f"\nPuzzle Analysis Results:")
        print(f"  Total Tubes: {puzzle_state['totalTube']}")
        print(f"  Empty Tubes: {puzzle_state['emptyTubeNumbers']}")
        print(f"  Filled Tubes: {len([t for t in puzzle_state['filledTubelist'] if t])}")
        
        print("\nTube Contents (bottom to top):")
        for i, tube in enumerate(puzzle_state['filledTubelist']):
            if tube:
                print(f"  Tube {i}: {tube}")
            else:
                print(f"  Tube {i}: [empty]")
        
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
        
        print("Searching for solution...")
        solution = solver.solve_with_limits(max_moves=500, max_depth=100)
        
        if solution:
            # Print solution with color details
            print("\n" + "=" * 60)
            print("SOLUTION MOVES (with colors):")
            print("=" * 60)
            
            # Reconstruct state to show colors for each move
            current_state = [list(tube) for tube in puzzle_state['filledTubelist']]
            
            # Print initial state
            print("\nInitial State:")
            for idx, tube in enumerate(current_state):
                if tube:
                    print(f"  Tube {idx}: {tube}")
                else:
                    print(f"  Tube {idx}: [empty]")
            
            for i, (from_tube, to_tube) in enumerate(solution, 1):
                # Get color being poured
                if current_state[from_tube]:
                    top_color = current_state[from_tube][-1]
                    block_size = solver.count_top_colors(current_state[from_tube])
                    print(f"\n{'='*60}")
                    print(f"Move {i}/{len(solution)}: Pour {block_size} unit(s) of '{top_color}' from Tube {from_tube} → Tube {to_tube}")
                    print(f"{'='*60}")
                    
                    # Apply move
                    current_state = solver.pour(current_state, from_tube, to_tube, block_size)
                    
                    # Print state of ALL tubes after this move
                    print(f"\nState after move {i}:")
                    for idx, tube in enumerate(current_state):
                        if tube:
                            print(f"  Tube {idx}: {tube}")
                        else:
                            print(f"  Tube {idx}: [empty]")
                else:
                    print(f"\nMove {i}: ERROR - Tube {from_tube} is empty!")
                    # Still print state even if error
                    print(f"\nState after move {i}:")
                    for idx, tube in enumerate(current_state):
                        if tube:
                            print(f"  Tube {idx}: {tube}")
                        else:
                            print(f"  Tube {idx}: [empty]")
        
        if not solution:
            print("ERROR: Could not find solution!")
            return None
        
        print(f"\nSolution found! Total moves: {len(solution)}")
        print("\nSolution moves:")
        for i, (from_tube, to_tube) in enumerate(solution, 1):
            print(f"  {i}. Pour from tube {from_tube} to tube {to_tube}")
        
        return solution
    
    def execute_solution(self, moves: List[Tuple[int, int]]):
        """
        Execute the solution using mouse automation
        """
        print("\n" + "=" * 60)
        print("Step 4: Executing Solution")
        print("=" * 60)
        
        if not self.mouse_controller:
            # Create mouse controller with current state
            x1, y1 = self.game_region[0], self.game_region[1]
            x2, y2 = self.game_region[2], self.game_region[3]
            self.mouse_controller = MouseController(
                (x1, y1, x2, y2),
                self.tube_positions
            )
        
        print("Starting in 3 seconds... Move mouse to corner to abort (failsafe)...")
        time.sleep(3)
        
        self.mouse_controller.execute_moves(moves, delay_between_moves=0.8)
        
        print("\nSolution execution complete!")
    
    def check_if_solved(self) -> bool:
        """Check if puzzle is solved by analyzing current state"""
        print("\nChecking if puzzle is solved...")
        
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
        print("2. Analyze the puzzle from a screenshot")
        print("3. Solve the puzzle")
        print("4. Automatically play the moves")
        print("\nNote: Keep the game visible on screen!")
        
        input("\nPress Enter to start...")
        
        # Step 1: Setup game region
        top_left, bottom_right = self.setup_game_region()
        x1, y1 = int(top_left[0]), int(top_left[1])
        x2, y2 = int(bottom_right[0]), int(bottom_right[1])
        self.game_region = (x1, y1, x2, y2)
        
        # Initialize image processor
        self.image_processor = ImageProcessor(self.game_region)
        
        # Main loop: solve and play until win
        round_number = 1
        
        while True:
            print(f"\n{'=' * 60}")
            print(f"ROUND {round_number}")
            print(f"{'=' * 60}")
            
            # Step 2: Analyze puzzle
            puzzle_state = self.analyze_puzzle()
            
            # Step 3: Solve
            solution = self.solve_puzzle(puzzle_state)
            
            if not solution:
                print("\nCannot solve this puzzle. Please check manually.")
                break
            
            # Step 4: Execute
            self.execute_solution(solution)
            
            # Check if solved
            time.sleep(2)  # Wait for game to update
            
            if self.check_if_solved():
                print("\n🎉 Puzzle solved!")
                
                # Ask if user wants to continue
                response = input("\nContinue to next round? (y/n): ").lower()
                if response != 'y':
                    break
                
                round_number += 1
                print("\nWaiting for next puzzle to appear...")
                input("Press Enter when the next puzzle is ready...")
            else:
                print("\n⚠️  Puzzle not yet solved. Attempting to continue...")
                # Re-analyze and try again
                time.sleep(1)
        
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

