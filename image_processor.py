"""
Image Processing Module for Water Sort Puzzle
Extracts puzzle state from screenshots using computer vision
"""
import numpy as np
from PIL import Image
import cv2
from typing import List, Tuple, Dict
import colorsys


class ImageProcessor:
    """Processes screenshots to extract puzzle state"""
    
    # Color mapping - common colors in water sort puzzles
    COLOR_NAMES = {
        'red': ([0, 50, 50], [10, 255, 255], (255, 0, 0)),
        'orange': ([10, 50, 50], [25, 255, 255], (255, 165, 0)),
        'yellow': ([25, 50, 50], [35, 255, 255], (255, 255, 0)),
        'green': ([35, 50, 50], [85, 255, 255], (0, 255, 0)),
        'blue': ([85, 50, 50], [130, 255, 255], (0, 0, 255)),
        'purple': ([130, 50, 50], [170, 255, 255], (128, 0, 128)),
        'pink': ([170, 50, 50], [180, 255, 255], (255, 192, 203)),
        'brown': ([5, 50, 20], [30, 255, 200], (165, 42, 42)),
        'cyan': ([85, 100, 100], [95, 255, 255], (0, 255, 255)),
        'gray': ([0, 0, 30], [180, 30, 200], (128, 128, 128)),
    }
    
    def __init__(self, game_region: Tuple[int, int, int, int] = None):
        """
        Initialize image processor
        Args:
            game_region: (x1, y1, x2, y2) coordinates of game area
        """
        self.game_region = game_region
    
    def set_game_region(self, top_left: Tuple[int, int], bottom_right: Tuple[int, int]):
        """Set the game screen region"""
        x1, y1 = top_left
        x2, y2 = bottom_right
        self.game_region = (x1, y1, x2, y2)
    
    def capture_screen(self) -> np.ndarray:
        """Capture screenshot of the game region"""
        import pyautogui
        
        if self.game_region is None:
            raise ValueError("Game region not set. Call set_game_region() first.")
        
        x1, y1, x2, y2 = self.game_region
        # Ensure all values are integers
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        width = int(x2 - x1)
        height = int(y2 - y1)
        
        screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def detect_tubes(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect tube positions in the image
        Returns: List of (x, y, width, height) for each tube
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect circular/rounded shapes (tubes)
        # Using HoughCircles or contour detection
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        tubes = []
        min_area = 500  # Minimum area for a tube
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = h / w if w > 0 else 0
            
            # Tubes are typically tall and narrow
            if aspect_ratio > 1.5 and area > min_area:
                tubes.append((x, y, w, h))
        
        # Sort tubes by position (left to right, top to bottom)
        tubes.sort(key=lambda t: (t[1] // (image.shape[0] // 2), t[0]))
        
        return tubes
    
    def extract_tube_colors(self, image: np.ndarray, tube_rect: Tuple[int, int, int, int]) -> List[str]:
        """
        Extract colors from a tube from bottom to top
        Detects continuous color blocks representing liquid levels
        Args:
            image: Full game image
            tube_rect: (x, y, width, height) of the tube
        Returns: List of color names from bottom to top (each element = one liquid unit)
        """
        x, y, w, h = tube_rect
        
        # Extract tube region
        tube_img = image[y:y+h, x:x+w]
        
        if tube_img.size == 0:
            return []
        
        # Scan from bottom to top, detecting continuous color blocks
        # This approach detects each liquid unit as a separate color block
        colors = []
        max_units = 4  # Maximum liquid units per tube
        
        center_x = w // 2
        sample_width = max(5, w // 4)
        sample_x1 = max(0, center_x - sample_width // 2)
        sample_x2 = min(w, center_x + sample_width // 2)
        
        if sample_x2 <= sample_x1:
            return []
        
        # Estimate liquid unit height (each unit is roughly h/4)
        unit_height = h / max_units
        
        # Scan from bottom to top with fine steps to detect color transitions
        sample_step = max(2, int(h / 50))  # Sample every few pixels
        
        current_block_color = None
        current_block_samples = []
        block_start_y = None
        
        # Track all detected color blocks
        color_blocks = []  # List of (color, start_y, end_y)
        
        for sample_y in range(h - 1, -1, -sample_step):
            if sample_y >= h or sample_y < 0:
                continue
            
            # Get average color at this row
            row_segment = tube_img[sample_y, sample_x1:sample_x2]
            if row_segment.size == 0:
                continue
            
            # Get average color
            if len(row_segment.shape) == 2 and row_segment.shape[0] > 0:
                avg_color = np.mean(row_segment, axis=0)
            elif len(row_segment.shape) == 1 and row_segment.shape[0] >= 3:
                avg_color = row_segment[:3]
            else:
                continue
            
            if avg_color.size == 0 or len(avg_color) < 3:
                continue
            
            avg_color_bgr = avg_color[:3].astype(np.uint8)
            
            # Convert to HSV
            if len(avg_color_bgr) == 3:
                color_reshaped = np.reshape(avg_color_bgr, (1, 1, 3))
                try:
                    avg_color_hsv = cv2.cvtColor(color_reshaped, cv2.COLOR_BGR2HSV)[0][0]
                except:
                    continue
            else:
                continue
            
            # Match to known color
            color_name = self._match_color(avg_color_hsv)
            
            # Detect color transitions
            if color_name:
                if current_block_color is None:
                    # Start new block
                    current_block_color = color_name
                    block_start_y = sample_y
                    current_block_samples = [color_name]
                elif color_name == current_block_color:
                    # Same color continues
                    current_block_samples.append(color_name)
                else:
                    # Color changed - finalize previous block
                    if current_block_color and len(current_block_samples) >= 2:
                        # Block must have at least 2 samples to be valid
                        color_blocks.append((current_block_color, block_start_y, sample_y))
                    
                    # Start new block
                    current_block_color = color_name
                    block_start_y = sample_y
                    current_block_samples = [color_name]
            else:
                # Empty/transparent - end current block if any
                if current_block_color and len(current_block_samples) >= 2:
                    color_blocks.append((current_block_color, block_start_y, sample_y))
                current_block_color = None
                block_start_y = None
                current_block_samples = []
        
        # Finalize last block if any
        if current_block_color and len(current_block_samples) >= 2:
            color_blocks.append((current_block_color, block_start_y, 0))
        
        # Convert blocks to color list (one color per unit)
        # Split blocks by height - each liquid unit is roughly h/4 tall
        unit_height = h / max_units
        for block_color, block_start, block_end in reversed(color_blocks):  # Reverse to get bottom-to-top order
            block_height = abs(block_start - block_end)
            # Calculate how many units this block represents (round to nearest)
            num_units = max(1, round(block_height / unit_height))
            
            # Add the color for each unit this block represents
            for _ in range(num_units):
                colors.append(block_color)
                if len(colors) >= max_units:
                    break
            
            if len(colors) >= max_units:
                break
        
        return colors
    
    def _match_color(self, hsv_color: np.ndarray) -> str:
        """Match HSV color to a named color"""
        h, s, v = hsv_color
        
        best_match = None
        min_distance = float('inf')
        
        for color_name, (lower, upper, _) in self.COLOR_NAMES.items():
            # Check if color is in range
            if lower[0] <= upper[0]:  # Normal range
                if lower[0] <= h <= upper[0] and lower[1] <= s <= upper[1] and lower[2] <= v <= upper[2]:
                    distance = sum([abs(h - (lower[0] + upper[0]) / 2),
                                   abs(s - (lower[1] + upper[1]) / 2),
                                   abs(v - (lower[2] + upper[2]) / 2)])
                    if distance < min_distance:
                        min_distance = distance
                        best_match = color_name
            else:  # Wrapping range (like red)
                if (h >= lower[0] or h <= upper[0]) and lower[1] <= s <= upper[1] and lower[2] <= v <= upper[2]:
                    distance = sum([abs(h - (lower[0] + upper[0]) / 2),
                                   abs(s - (lower[1] + upper[1]) / 2),
                                   abs(v - (lower[2] + upper[2]) / 2)])
                    if distance < min_distance:
                        min_distance = distance
                        best_match = color_name
        
        # If saturation is too low, it's likely empty/transparent
        if s < 30 or v < 50:
            return None
        
        return best_match
    
    def analyze_puzzle(self, image: np.ndarray = None) -> Dict:
        """
        Analyze the puzzle image and extract state
        Returns:
            {
                'totalTube': int,
                'emptyTubeNumbers': int,
                'filledTubelist': List[List[str]]  # Colors from bottom to top
            }
        """
        if image is None:
            image = self.capture_screen()
        
        tubes = self.detect_tubes(image)
        
        if not tubes:
            # Fallback: try manual grid detection
            tubes = self._detect_tubes_grid(image)
        
        total_tubes = len(tubes)
        filled_tubelist = []
        empty_tubes = 0
        
        for tube_rect in tubes:
            colors = self.extract_tube_colors(image, tube_rect)
            if not colors:
                empty_tubes += 1
                filled_tubelist.append([])
            else:
                filled_tubelist.append(colors)
        
        return {
            'totalTube': total_tubes,
            'emptyTubeNumbers': empty_tubes,
            'filledTubelist': filled_tubelist
        }
    
    def _detect_tubes_grid(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Fallback method: detect tubes in a grid pattern"""
        h, w = image.shape[:2]
        
        # Try common layouts (2 rows, 3-4 columns each)
        tubes = []
        
        # Estimate tube size and spacing
        # Typical layout: 4 tubes top row, 3-4 tubes bottom row
        num_rows = 2
        num_cols_top = 4
        num_cols_bottom = 3
        
        # Estimate dimensions
        top_row_y = h // 4
        bottom_row_y = h * 3 // 4
        tube_width = w // (num_cols_top + 1)
        tube_height = h // 3
        
        # Top row
        for i in range(num_cols_top):
            x = (i + 1) * w // (num_cols_top + 1) - tube_width // 2
            tubes.append((x, top_row_y, tube_width, tube_height))
        
        # Bottom row
        for i in range(num_cols_bottom):
            x = (i + 1) * w // (num_cols_bottom + 1) - tube_width // 2
            tubes.append((x, bottom_row_y, tube_width, tube_height))
        
        return tubes

