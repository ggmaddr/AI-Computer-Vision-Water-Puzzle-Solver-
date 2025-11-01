# AI Water Sort Puzzle Solver

An intelligent water sort puzzle solver that uses computer vision to analyze the game screen and automatically solve puzzles using mouse automation.

## Features

- **Computer Vision**: Automatically extracts puzzle state from screenshots
- **AI Solver**: Uses BFS algorithm to find optimal solution
- **Mouse Automation**: Automatically plays the moves on your screen
- **Interactive Setup**: Easy game region calibration by clicking corners

## Installation

1. Install Python dependencies:
```bash
# On macOS, use pip3:
pip3 install -r requirements.txt

# On Linux/Windows, use pip or pip3:
pip install -r requirements.txt
```

2. On macOS, you may need to grant accessibility permissions for mouse control:
   - Go to System Preferences → Security & Privacy → Privacy → Accessibility
   - Add Python or your terminal application

## Usage

1. Open your water sort puzzle game on screen
2. Run the solver:
```bash
python main.py
```

3. Follow the prompts:
   - **Step 1**: Click the top-left corner of the game screen, then the bottom-right corner
   - **Step 2**: The app will analyze the current puzzle state
   - **Step 3**: The solver will find a solution
   - **Step 4**: The app will automatically play the moves

## How It Works

### Image Processing (`image_processor.py`)
- Captures screenshot of the defined game region
- Detects tube positions using contour detection
- Extracts colors from each tube (bottom to top)
- Returns puzzle parameters: `totalTube`, `emptyTubeNumbers`, `filledTubelist`

### Puzzle Solver (`puzzle_solver.py`)
- Uses BFS (Breadth-First Search) algorithm
- Validates moves (can only pour same colors, respects capacity)
- Finds shortest solution path
- Returns list of moves: `[(from_tube, to_tube), ...]`

### Mouse Controller (`mouse_controller.py`)
- Maps tube indices to screen coordinates
- Clicks tubes in sequence to pour liquids
- Executes solution moves automatically

## Puzzle Parameters Format

The solver expects puzzle state in this format:
```python
{
    'totalTube': 7,
    'emptyTubeNumbers': 2,
    'filledTubelist': [
        ['orange', 'pink', 'green', 'pink'],  # Tube 0
        ['orange', 'red', 'red', 'blue'],      # Tube 1
        ['blue', 'green', 'red', 'red'],       # Tube 2
        ['pink', 'red', 'orange', 'orange'],   # Tube 3
        ['green', 'orange', 'pink', 'blue'],   # Tube 4
        [],                                    # Tube 5 (empty)
        []                                     # Tube 6 (empty)
    ]
}
```

Colors are listed from **bottom to top** in each tube.

## Supported Colors

The image processor recognizes these colors:
- red
- orange
- yellow
- green
- blue
- purple
- pink
- brown
- cyan
- gray

## Safety

- **Failsafe**: Move mouse to screen corner to abort automation
- The app pauses briefly between moves to allow game updates
- All actions are logged to console

## Limitations

- Color detection accuracy depends on game graphics and lighting
- Tube detection works best with standard layouts (2 rows)
- May require manual adjustment for custom game variants
- Solver may timeout on very complex puzzles (adjustable in code)

## Troubleshooting

**Issue**: Colors not detected correctly
- Ensure good lighting and clear game graphics
- Check that game region is set correctly
- Try adjusting color thresholds in `image_processor.py`

**Issue**: Tubes not detected
- Verify the game region includes all tubes
- Try a different game layout or adjust detection parameters

**Issue**: Mouse clicks not working
- Check accessibility permissions on macOS
- Verify game region coordinates are correct
- Try increasing delays between clicks

## License

This project is provided as-is for educational purposes.

