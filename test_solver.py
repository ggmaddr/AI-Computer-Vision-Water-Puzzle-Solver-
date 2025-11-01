"""
Test script for puzzle solver logic
Tests the solver with a simple puzzle
"""
from puzzle_solver import PuzzleSolver


def test_solver():
    """Test the solver with a simple puzzle"""
    print("Testing Water Sort Puzzle Solver")
    print("=" * 60)
    
    # Simple test case: 4 tubes, goal is to separate colors
    # Tube 0: [red, blue, red, blue]
    # Tube 1: [blue, red, blue, red]
    # Tube 2: [] (empty)
    # Tube 3: [] (empty)
    
    filled_tubelist = [
        ['red', 'blue', 'red', 'blue'],
        ['blue', 'red', 'blue', 'red'],
        [],
        []
    ]
    
    solver = PuzzleSolver(
        total_tubes=4,
        empty_tube_numbers=2,
        filled_tubelist=filled_tubelist
    )
    
    print("\nInitial state:")
    for i, tube in enumerate(filled_tubelist):
        print(f"  Tube {i}: {tube}")
    
    print("\nSolving...")
    solution = solver.solve_with_limits(max_moves=100, max_depth=30)
    
    if solution:
        print(f"\n✓ Solution found! {len(solution)} moves:")
        for i, (from_tube, to_tube) in enumerate(solution, 1):
            print(f"  {i}. Pour from tube {from_tube} to tube {to_tube}")
    else:
        print("\n✗ No solution found")
    
    # Test with example from image
    print("\n" + "=" * 60)
    print("Testing with example puzzle from image:")
    print("=" * 60)
    
    example_tubelist = [
        ['orange', 'pink', 'green', 'pink'],
        ['orange', 'red', 'red', 'blue'],
        ['blue', 'green', 'red', 'red'],
        ['pink', 'red', 'orange', 'orange'],
        ['green', 'orange', 'pink', 'blue'],
        [],
        []
    ]
    
    solver2 = PuzzleSolver(
        total_tubes=7,
        empty_tube_numbers=2,
        filled_tubelist=example_tubelist
    )
    
    print("\nInitial state:")
    for i, tube in enumerate(example_tubelist):
        print(f"  Tube {i}: {tube}")
    
    print("\nSolving...")
    solution2 = solver2.solve_with_limits(max_moves=500, max_depth=100)
    
    if solution2:
        print(f"\n✓ Solution found! {len(solution2)} moves")
        print("First 10 moves:")
        for i, (from_tube, to_tube) in enumerate(solution2[:10], 1):
            print(f"  {i}. Pour from tube {from_tube} to tube {to_tube}")
        if len(solution2) > 10:
            print(f"  ... and {len(solution2) - 10} more moves")
    else:
        print("\n✗ No solution found (may need more moves/depth)")


if __name__ == "__main__":
    test_solver()

