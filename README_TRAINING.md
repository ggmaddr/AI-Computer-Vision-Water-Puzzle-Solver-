# Color Detection Training Guide

This system uses machine learning to learn optimal color detection from real puzzle screenshots.

## Quick Start

### 1. Collect Training Data

Run the data collection script and click on each color multiple times:

```bash
python3 collect_training_data.py
```

**Instructions:**
- For each color (pink, green, orange, red, gray, blue, yellow), click on that color ~30 times in the puzzle
- Try to click on different shades/variations of each color
- Click on actual liquid blocks in different tubes
- Press 's' to skip a color, 'q' to quit

The script saves samples to `training_data/color_samples.json`

### 2. Train the Model

After collecting samples, train the model:

```bash
python3 train_color_model.py
```

This will:
- Load collected samples
- Use K-means clustering to find optimal color centers
- Calculate optimal detection thresholds for each color
- Save trained model to `training_data/color_model.pkl`

### 3. Use the Trained Model

The `ImageProcessor` automatically loads the trained model if it exists. Just run your solver:

```bash
python3 main.py
```

## How It Works

1. **Data Collection**: Collects RGB samples from actual puzzle colors by clicking
2. **K-means Clustering**: Learns the optimal color center in LAB color space (perceptually uniform)
3. **Threshold Learning**: Calculates detection thresholds based on 95th percentile distance
4. **Robust Matching**: Uses learned centers and thresholds for more accurate detection

## Benefits

- **Learns from your actual game**: Adapts to your specific screen/monitor colors
- **Robust to variations**: Handles slight color differences automatically
- **Automatic threshold tuning**: No manual parameter tweaking needed
- **Better accuracy**: Trained on real data, not hardcoded templates

## Tips

- Collect samples from multiple puzzles/levels for better generalization
- Click on various shades of each color (lighter/darker regions)
- Re-train if you change monitors or game settings
- More samples = better accuracy (aim for 30+ per color)

