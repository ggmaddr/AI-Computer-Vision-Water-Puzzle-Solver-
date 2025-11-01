"""
Water Sort Puzzle Solver
Uses BFS algorithm to find solution path
"""
from typing import List, Tuple, Optional, Set
from collections import deque
import copy


class PuzzleSolver:
    """Solves water sort puzzles using BFS"""
    
    def __init__(self, total_tubes: int, empty_tube_numbers: int, filled_tubelist: List[List[str]]):
        """
        Initialize solver
        Args:
            total_tubes: Total number of tubes
            empty_tube_numbers: Number of empty tubes
            filled_tubelist: List of tube contents (each tube is list of colors from bottom to top)
        """
        self.total_tubes = total_tubes
        self.empty_tube_numbers = empty_tube_numbers
        self.initial_state = [list(tube) for tube in filled_tubelist]  # Deep copy
        self.max_capacity = 4  # Typical capacity per tube
    
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
    
    def can_pour(self, from_tube: List[str], to_tube: List[str], max_capacity: int) -> bool:
        """
        Check if we can pour from one tube to another
        Returns: (can_pour, amount) tuple
        """
        if not from_tube:
            return False, 0
        
        # Can't pour if target is full
        if len(to_tube) >= max_capacity:
            return False, 0
        
        # Get top color(s) from source tube
        top_color = from_tube[-1]
        
        # Count consecutive same colors from top
        pour_amount = 0
        for i in range(len(from_tube) - 1, -1, -1):
            if from_tube[i] == top_color:
                pour_amount += 1
            else:
                break
        
        # Can only pour if target is empty or has same color on top
        if to_tube:
            if to_tube[-1] != top_color:
                return False, 0
        
        # Can't pour more than available space
        available_space = max_capacity - len(to_tube)
        pour_amount = min(pour_amount, available_space)
        
        return pour_amount > 0, pour_amount
    
    def pour(self, state: List[List[str]], from_idx: int, to_idx: int, amount: int) -> List[List[str]]:
        """Pour liquid from one tube to another"""
        new_state = [list(tube) for tube in state]  # Deep copy
        
        # Get top color
        top_color = new_state[from_idx][-1]
        
        # Remove from source
        new_state[from_idx] = new_state[from_idx][:-amount]
        
        # Add to target
        new_state[to_idx].extend([top_color] * amount)
        
        return new_state
    
    def state_to_tuple(self, state: List[List[str]]) -> Tuple:
        """Convert state to hashable tuple"""
        return tuple(tuple(tube) for tube in state)
    
    def solve(self) -> Optional[List[Tuple[int, int]]]:
        """
        Solve the puzzle using BFS
        Returns: List of (from_tube, to_tube) moves, or None if unsolvable
        """
        # BFS queue: (state, moves_path)
        queue = deque([(self.initial_state, [])])
        visited = {self.state_to_tuple(self.initial_state)}
        
        while queue:
            current_state, moves = queue.popleft()
            
            # Check if solved
            if self.is_solved(current_state):
                return moves
            
            # Try all possible moves
            for from_idx in range(self.total_tubes):
                if not current_state[from_idx]:  # Source is empty
                    continue
                
                for to_idx in range(self.total_tubes):
                    if from_idx == to_idx:  # Can't pour to self
                        continue
                    
                    can_pour, amount = self.can_pour(
                        current_state[from_idx],
                        current_state[to_idx],
                        self.max_capacity
                    )
                    
                    if can_pour:
                        new_state = self.pour(current_state, from_idx, to_idx, amount)
                        state_tuple = self.state_to_tuple(new_state)
                        
                        if state_tuple not in visited:
                            visited.add(state_tuple)
                            new_moves = moves + [(from_idx, to_idx)]
                            
                            # Prune obviously bad moves
                            if not self._is_bad_state(new_state):
                                queue.append((new_state, new_moves))
        
        return None  # No solution found
    
    def _is_bad_state(self, state: List[List[str]]) -> bool:
        """Heuristic to detect obviously bad states"""
        # Check if there are too many different colors in one tube
        for tube in state:
            if len(tube) > 0:
                unique_colors = set(tube)
                # If tube has multiple colors but they're not organized, it's bad
                if len(unique_colors) > 1:
                    # Check if colors are mixed (not all same color at top)
                    if len(set(tube[-1:])) > 1:  # Top segment has multiple colors
                        return False  # This is actually fine during solving
        return False
    
    def solve_with_limits(self, max_moves: int = 100, max_depth: int = 50) -> Optional[List[Tuple[int, int]]]:
        """
        Solve with limits to prevent infinite loops
        Args:
            max_moves: Maximum number of moves to consider
            max_depth: Maximum depth in search tree
        """
        queue = deque([(self.initial_state, [])])
        visited = {self.state_to_tuple(self.initial_state)}
        
        while queue and len(visited) < max_moves:
            current_state, moves = queue.popleft()
            
            if len(moves) > max_depth:
                continue
            
            if self.is_solved(current_state):
                return moves
            
            for from_idx in range(self.total_tubes):
                if not current_state[from_idx]:
                    continue
                
                for to_idx in range(self.total_tubes):
                    if from_idx == to_idx:
                        continue
                    
                    can_pour, amount = self.can_pour(
                        current_state[from_idx],
                        current_state[to_idx],
                        self.max_capacity
                    )
                    
                    if can_pour:
                        new_state = self.pour(current_state, from_idx, to_idx, amount)
                        state_tuple = self.state_to_tuple(new_state)
                        
                        if state_tuple not in visited:
                            visited.add(state_tuple)
                            new_moves = moves + [(from_idx, to_idx)]
                            queue.append((new_state, new_moves))
        
        return None

