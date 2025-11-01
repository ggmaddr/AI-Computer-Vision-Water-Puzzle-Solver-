"""
Water Sort Puzzle Solver
Uses A* algorithm with heuristic to find optimal solution path
Based on the sample water solver implementation
"""
from typing import List, Tuple, Optional
import heapq


class PuzzleSolver:
    """Solves water sort puzzles using A* algorithm"""
    
    def __init__(self, total_tubes: int, empty_tube_numbers: int, filled_tubelist: List[List[str]], debug: bool = True):
        """
        Initialize solver
        Args:
            total_tubes: Total number of tubes
            empty_tube_numbers: Number of empty tubes
            filled_tubelist: List of tube contents (each tube is list of colors from bottom to top)
            debug: Enable debug logging
        """
        self.total_tubes = total_tubes
        self.empty_tube_numbers = empty_tube_numbers
        self.initial_state = [list(tube) for tube in filled_tubelist]  # Deep copy
        self.max_capacity = 4  # Typical capacity per tube
        self.debug = debug
    
    def is_solved(self, state: List[List[str]]) -> bool:
        """Check if puzzle is solved (all tubes have same color or are empty)"""
        for tube in state:
            if not tube:  # Empty tube
                continue
            # Check if all colors in tube are the same
            first_color = tube[0]
            if not all(color == first_color for color in tube):
                return False
        return True
    
    def get_top_color(self, tube: List[str]) -> Optional[str]:
        """Get the top color of a tube"""
        if not tube:
            return None
        return tube[-1]
    
    def count_top_colors(self, tube: List[str]) -> int:
        """Count consecutive same colors from top"""
        if not tube:
            return 0
        top_color = tube[-1]
        count = 0
        for i in range(len(tube) - 1, -1, -1):
            if tube[i] == top_color:
                count += 1
            else:
                break
        return count
    
    def can_pour(self, from_tube: List[str], to_tube: List[str], block_size: int) -> bool:
        """
        Check if we can pour a block of colors from one tube to another
        Args:
            from_tube: Source tube
            to_tube: Destination tube
            block_size: Size of the block to pour
        Returns: True if can pour
        """
        if not from_tube:
            return False
        
        space = self.max_capacity - len(to_tube)
        if space < block_size:
            return False
        
        if not to_tube:
            return True
        
        return self.get_top_color(from_tube) == self.get_top_color(to_tube)
    
    def pour(self, state: List[List[str]], from_idx: int, to_idx: int, block_size: int) -> List[List[str]]:
        """Pour a block of liquid from one tube to another"""
        new_state = [list(tube) for tube in state]  # Deep copy
        
        # Pour block_size units from source to target
        for _ in range(block_size):
            new_state[to_idx].append(new_state[from_idx].pop())
        
        return new_state
    
    def state_to_key(self, state: List[List[str]]) -> str:
        """Convert state to hashable string key"""
        return '|'.join(','.join(tube) for tube in state)
    
    def is_useful_move(self, from_tube: List[str], to_tube: List[str], block_size: int) -> bool:
        """
        Check if a move is useful (prunes obviously bad moves)
        """
        if not to_tube:  # Pouring to empty tube
            top_color = self.get_top_color(from_tube)
            # Don't pour to empty if the source tube is already all one color
            if from_tube and all(c == top_color for c in from_tube):
                return False
        return True
    
    def heuristic(self, state: List[List[str]]) -> int:
        """
        Heuristic function for A* algorithm
        Counts color transitions and bottom color conflicts
        """
        h = 0
        # Count color transitions within tubes
        for tube in state:
            for i in range(1, len(tube)):
                if tube[i] != tube[i - 1]:
                    h += 1
        
        # Count bottom color conflicts (same color at bottom of multiple tubes)
        bottoms = {}
        for tube in state:
            if tube:
                bottom = tube[0]
                bottoms[bottom] = bottoms.get(bottom, 0) + 1
        
        # Add penalty for each duplicate bottom color (except first one)
        for count in bottoms.values():
            if count > 1:
                h += count - 1
        
        return h
    
    def _print_state(self, state: List[List[str]], title: str = "State"):
        """Print the current state of tubes"""
        if not self.debug:
            return
        
        print(f"\n{title}:")
        for i, tube in enumerate(state):
            if tube:
                print(f"  Tube {i}: {tube} (bottom→top)")
            else:
                print(f"  Tube {i}: [empty]")
    
    def _print_move(self, from_idx: int, to_idx: int, from_tube: List[str], to_tube: List[str], 
                    block_size: int, move_num: int = None):
        """Print move details"""
        if not self.debug:
            return
        
        top_color = from_tube[-1] if from_tube else "N/A"
        prefix = f"[Move {move_num}] " if move_num is not None else ""
        print(f"{prefix}Pouring {block_size} unit(s) of '{top_color}' from Tube {from_idx} to Tube {to_idx}")
        
        from_display = from_tube if from_tube else ["[empty]"]
        to_display = to_tube if to_tube else ["[empty]"]
        print(f"    Tube {from_idx}: {from_display} → Tube {to_idx}: {to_display}")
    
    def solve(self) -> Optional[List[Tuple[int, int]]]:
        """
        Solve the puzzle using A* algorithm
        Returns: List of (from_tube, to_tube) moves, or None if unsolvable
        """
        if self.debug:
            print("\n" + "=" * 60)
            print("SOLVING PUZZLE")
            print("=" * 60)
            self._print_state(self.initial_state, "Initial State")
            print()
        
        initial_key = self.state_to_key(self.initial_state)
        initial_h = self.heuristic(self.initial_state)
        
        if self.debug:
            print(f"Heuristic (initial): {initial_h}")
            print(f"Starting A* search...\n")
        
        # Priority queue: (f_score, counter, g_score, state, moves)
        # Use counter to break ties and ensure FIFO for same f_score
        counter = 0
        pq = [(initial_h, counter, 0, self.initial_state, [])]
        heapq.heapify(pq)
        counter += 1
        
        # Track best g_score for each state
        g_score = {initial_key: 0}
        
        max_iterations = 1000000
        iterations = 0
        last_log_iteration = 0
        
        while pq and iterations < max_iterations:
            iterations += 1
            
            # Progress logging every 10000 iterations
            if self.debug and iterations - last_log_iteration >= 10000:
                print(f"Progress: {iterations} iterations, {len(pq)} states in queue, {len(g_score)} states explored")
                last_log_iteration = iterations
            
            f, _, g, current_state, moves = heapq.heappop(pq)
            state_key = self.state_to_key(current_state)
            
            # Skip if we've found a better path to this state
            if g > g_score.get(state_key, float('inf')):
                continue
            
            # Check if solved
            if self.is_solved(current_state):
                if self.debug:
                    print(f"\n{'='*60}")
                    print(f"SOLUTION FOUND in {iterations} iterations!")
                    print(f"{'='*60}")
                    self._print_state(current_state, "Final State (Solved)")
                    print(f"\nTotal moves: {len(moves)}")
                return moves
            
            # Try all possible moves
            for from_idx in range(self.total_tubes):
                if not current_state[from_idx]:
                    continue
                
                block_size = self.count_top_colors(current_state[from_idx])
                if block_size == 0:
                    continue
                
                for to_idx in range(self.total_tubes):
                    if from_idx == to_idx:
                        continue
                    
                    if not self.can_pour(current_state[from_idx], current_state[to_idx], block_size):
                        continue
                    
                    if not self.is_useful_move(current_state[from_idx], current_state[to_idx], block_size):
                        continue
                    
                    # Make the move
                    new_state = self.pour(current_state, from_idx, to_idx, block_size)
                    new_key = self.state_to_key(new_state)
                    tentative_g = g + 1
                    
                    # Check if this is a better path
                    current_g = g_score.get(new_key, float('inf'))
                    if tentative_g < current_g:
                        g_score[new_key] = tentative_g
                        new_h = self.heuristic(new_state)
                        new_f = tentative_g + new_h
                        new_moves = moves + [(from_idx, to_idx)]
                        heapq.heappush(pq, (new_f, counter, tentative_g, new_state, new_moves))
                        counter += 1
        
        if self.debug:
            print(f"\nNo solution found after {iterations} iterations")
        
        return None  # No solution found
    
    def solve_with_limits(self, max_moves: int = 500, max_depth: int = 100) -> Optional[List[Tuple[int, int]]]:
        """
        Solve with limits (for backward compatibility)
        The A* algorithm already has built-in iteration limits
        Args:
            max_moves: Not used (kept for compatibility)
            max_depth: Not used (kept for compatibility)
        """
        return self.solve()

