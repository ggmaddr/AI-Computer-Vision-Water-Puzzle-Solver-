"""
Diagnose Color Detection Errors
Shows what colors are being detected vs what they should be
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from image_processor import ImageProcessor

def diagnose_tubes():
    """Diagnose detection errors in current puzzle"""
    print("="*60)
    print("COLOR DETECTION DIAGNOSIS")
    print("="*60)
    
    # Expected correct values (you'll need to provide these)
    expected = {
        0: ['red', 'orange', 'green', 'pink'],
        1: ['gray', 'orange', 'gray', 'green'],
        2: ['blue', 'gray', 'pink', 'orange'],
        3: ['pink', 'green', 'yellow', 'red'],
    }
    
    processor = ImageProcessor()
    
    print("\nCapturing puzzle...")
    image = processor.capture_screen()
    
    print("Analyzing tubes...")
    puzzle_state = processor.analyze_puzzle(image)
    
    print("\n" + "="*60)
    print("DETECTION RESULTS")
    print("="*60)
    
    errors = []
    
    for i, tube_colors in enumerate(puzzle_state['filledTubelist']):
        expected_colors = expected.get(i, None)
        
        if expected_colors:
            print(f"\nTube {i}:")
            print(f"  Expected: {expected_colors}")
            print(f"  Detected: {tube_colors}")
            
            if tube_colors != expected_colors:
                print(f"  ❌ MISMATCH!")
                
                # Show position-by-position errors
                max_len = max(len(expected_colors), len(tube_colors))
                for pos in range(max_len):
                    exp = expected_colors[pos] if pos < len(expected_colors) else "MISSING"
                    det = tube_colors[pos] if pos < len(tube_colors) else "MISSING"
                    
                    if exp != det:
                        print(f"    Position {pos} (bottom={pos==0}, top={pos==max_len-1}):")
                        print(f"      Expected: {exp}")
                        print(f"      Detected: {det}")
                        errors.append({
                            'tube': i,
                            'position': pos,
                            'expected': exp,
                            'detected': det
                        })
            else:
                print(f"  ✓ CORRECT")
        else:
            print(f"\nTube {i}: {tube_colors}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL ERRORS: {len(errors)}")
    print(f"{'='*60}")
    
    if errors:
        print("\nError Summary:")
        error_summary = {}
        for err in errors:
            key = f"{err['expected']} -> {err['detected']}"
            error_summary[key] = error_summary.get(key, 0) + 1
        
        for pattern, count in sorted(error_summary.items(), key=lambda x: -x[1]):
            print(f"  {pattern}: {count} occurrences")
        
        print("\n💡 To fix these errors:")
        print("  1. Run: python3 interactive_training.py")
        print("  2. Or collect more samples for misdetected colors")
    
    return errors

if __name__ == "__main__":
    diagnose_tubes()

