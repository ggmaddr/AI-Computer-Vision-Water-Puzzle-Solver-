"""
Image Processing Module for Water Sort Puzzle
Extracts puzzle state from screenshots using computer vision
"""
import numpy as np
from PIL import Image
import cv2
from typing import List, Tuple, Dict, Optional
import colorsys
import time


class ImageProcessor:
    """Processes screenshots to extract puzzle state"""
    
    # Known color templates in RGB (from sample.png analysis)
    # Used for matching detected colors to color names
    COLOR_TEMPLATES = {
        'pink': (236, 105, 144),
        'green': (108, 220, 158),
        'orange': (231, 161, 75),
        'red': (222, 105, 144),
        'gray': (101, 100, 103),
        'grey': (101, 100, 103),  # Alias
        'blue': (33, 80, 218),
        'yellow': (250, 223, 75),
    }
    
    def __init__(self, game_region: Tuple[int, int, int, int] = None, unit_height: float = None):
        """
        Initialize image processor
        Args:
            game_region: (x1, y1, x2, y2) coordinates of game area
            unit_height: Calibrated height of one liquid unit in pixels
        """
        self.game_region = game_region
        self.unit_height = unit_height  # Calibrated unit height from user
    
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
    
    def set_unit_height(self, unit_height: float):
        """Set the calibrated unit height from user measurement"""
        self.unit_height = unit_height
    
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
        
        if self.unit_height is None:
            raise ValueError("Unit height not calibrated. Call calibrate_unit_height() first.")
        
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
        
        # Use finer sampling for better detection of all segments
        # Sample more frequently to catch all color transitions
        # Skip the very bottom pixels (rounded tube bottom) - start from slightly higher
        bottom_offset = max(3, int(h / 20))  # Skip bottom 5% or at least 3 pixels
        for sample_y in range(h - 1 - bottom_offset, -1, -sample_step):
            if sample_y >= h or sample_y < 0:
                continue
            
            # Get pixel block at this row (BGR format)
            row_segment = tube_img[sample_y, sample_x1:sample_x2]
            if row_segment.size == 0:
                continue
            
            # row_segment is in shape (width, 3) for BGR
            # Reshape to (1, width, 3) for color detection
            if len(row_segment.shape) == 2 and row_segment.shape[1] == 3:
                # Already correct shape, just add batch dimension
                row_segment_bgr = row_segment.reshape(1, -1, 3)
            elif len(row_segment.shape) == 1:
                # Flattened, reshape if it's divisible by 3
                if row_segment.shape[0] % 3 == 0:
                    row_segment_bgr = row_segment.reshape(1, -1, 3)
                else:
                    continue
            else:
                continue
            
            # Use ML-based color detection on the pixel block
            color_name = self._detect_color_from_pixels(row_segment_bgr)
            
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
                    # Accept blocks with at least 1 sample (more sensitive)
                    if current_block_color and len(current_block_samples) >= 1:
                        color_blocks.append((current_block_color, block_start_y, sample_y))
                    
                    # Start new block
                    current_block_color = color_name
                    block_start_y = sample_y
                    current_block_samples = [color_name]
            else:
                # Empty/transparent detected - end current block if any
                # Don't add empty segments as blocks
                if current_block_color and len(current_block_samples) >= 1:
                    color_blocks.append((current_block_color, block_start_y, sample_y))
                current_block_color = None
                block_start_y = None
                current_block_samples = []
        
        # Finalize last block if any
        if current_block_color and len(current_block_samples) >= 1:
            color_blocks.append((current_block_color, block_start_y, 0))
        
        # Convert blocks to color list (one color per unit)
        # Use calibrated unit_height to accurately count consecutive same-color blocks
        # color_blocks are in order from bottom (h-1) to top (0) since we scanned that way
        # block_start is higher y value (bottom), block_end is lower y value (top)
        # So first block in list is bottom, last is top - KEEP this order (don't reverse)
        
        if not color_blocks:
            return []
        
        # Use the calibrated unit height to determine how many units each block represents
        unit_height = self.unit_height
        
        for block_color, block_start, block_end in color_blocks:  # Keep original order (bottom to top)
            block_height = abs(block_start - block_end)
            
            if block_height == 0:
                # Very small block - count as 1 unit
                num_units = 1
            else:
                # Calculate units using calibrated unit height
                # Divide block height by unit height to get number of units
                units_float = block_height / unit_height
                
                # Round to nearest integer, but be smart about it
                # Round to nearest: 0.5-1.5 = 1, 1.5-2.5 = 2, etc.
                num_units = max(1, int(round(units_float)))
                
                # Ensure we don't exceed reasonable bounds
                num_units = min(num_units, max_units)
            
            # Don't exceed max_units total
            remaining_slots = max_units - len(colors)
            if remaining_slots <= 0:
                break
            
            num_units = min(num_units, remaining_slots)
            
            # Add the color for each unit this block represents
            for _ in range(num_units):
                colors.append(block_color)
                if len(colors) >= max_units:
                    break
            
            if len(colors) >= max_units:
                break
        
        return colors
    
    def calibrate_unit_height(self) -> float:
        """
        Calibrate unit height by asking user to click top and bottom of a single block
        Returns: The calibrated unit height in pixels
        """
        import pyautogui
        
        print("\n" + "=" * 60)
        print("UNIT HEIGHT CALIBRATION")
        print("=" * 60)
        print("\nPlease click on the BOTTOM of a single color block")
        print("(e.g., the bottom edge of one liquid unit)")
        print("You have 0.5 seconds to position your mouse...")
        time.sleep(0.5)
        
        try:
            from pynput import mouse
            
            bottom_clicked = False
            bottom_pos = None
            
            def on_click(x, y, button, pressed):
                nonlocal bottom_clicked, bottom_pos
                if pressed and button == mouse.Button.left:
                    bottom_pos = (x, y)
                    bottom_clicked = True
                    return False
            
            listener = mouse.Listener(on_click=on_click)
            listener.start()
            
            start_time = time.time()
            while not bottom_clicked and (time.time() - start_time) < 10:
                time.sleep(0.1)
            
            listener.stop()
            
            if not bottom_clicked or not bottom_pos:
                bottom_pos = pyautogui.position()
        except ImportError:
            input("Press Enter after clicking the BOTTOM of a block...")
            bottom_pos = pyautogui.position()
        
        print(f"✓ Bottom position recorded: {bottom_pos}")
        
        print("\nPlease click on the TOP of the SAME color block")
        print("(e.g., the top edge of the same liquid unit)")
        print("You have 5 seconds to position your mouse...")
        time.sleep(2)
        
        try:
            from pynput import mouse
            
            top_clicked = False
            top_pos = None
            
            def on_click(x, y, button, pressed):
                nonlocal top_clicked, top_pos
                if pressed and button == mouse.Button.left:
                    top_pos = (x, y)
                    top_clicked = True
                    return False
            
            listener = mouse.Listener(on_click=on_click)
            listener.start()
            
            start_time = time.time()
            while not top_clicked and (time.time() - start_time) < 10:
                time.sleep(0.1)
            
            listener.stop()
            
            if not top_clicked or not top_pos:
                top_pos = pyautogui.position()
        except ImportError:
            input("Press Enter after clicking the TOP of the block...")
            top_pos = pyautogui.position()
        
        print(f"✓ Top position recorded: {top_pos}")
        
        # Calculate unit height (absolute difference in y coordinates)
        if self.game_region:
            x1, y1, x2, y2 = self.game_region
            # Convert screen coordinates to relative coordinates
            bottom_y_rel = bottom_pos[1] - y1
            top_y_rel = top_pos[1] - y1
            unit_height = abs(bottom_y_rel - top_y_rel)
        else:
            unit_height = abs(bottom_pos[1] - top_pos[1])
        
        self.unit_height = unit_height
        
        print(f"\n✓ Unit height calibrated: {unit_height:.1f} pixels")
        print(f"  This will be used to count consecutive color blocks (1x, 2x, 3x, etc.)\n")
        
        return unit_height
    
    def _detect_color_from_pixels(self, pixels: np.ndarray) -> Optional[str]:
        """
        Detect color from a block of pixels using median RGB and nearest neighbor matching
        Args:
            pixels: Array of pixels in BGR format, shape (batch, width, 3) or (width, 3)
        Returns:
            Color name or None if empty/background
        """
        if pixels.size == 0:
            return None
        
        # Handle different input shapes
        if len(pixels.shape) == 3:
            # (batch, width, 3) - flatten to (batch*width, 3)
            bgr_pixels = pixels.reshape(-1, 3)
        elif len(pixels.shape) == 2 and pixels.shape[1] == 3:
            # (width, 3) - already flat
            bgr_pixels = pixels
        else:
            return None
        
        if len(bgr_pixels) == 0:
            return None
        
        # Convert BGR to RGB
        rgb_pixels = bgr_pixels[:, [2, 1, 0]]  # BGR -> RGB
        
        # Check for empty/background - very dark pixels
        # Calculate average brightness (value in RGB)
        avg_brightness = np.mean(rgb_pixels)
        if avg_brightness < 50:  # Very dark = empty/background
            return None
        
        # Use median to find dominant color (robust to outliers)
        dominant_rgb = np.median(rgb_pixels, axis=0).astype(int)
        r, g, b = int(dominant_rgb[0]), int(dominant_rgb[1]), int(dominant_rgb[2])
        
        # Convert to HSV for better color discrimination (especially pink vs red)
        rgb_array = np.array([[r, g, b]], dtype=np.uint8).reshape(1, 1, 3)
        hsv_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)
        h, s, v = int(hsv_array[0][0][0]), int(hsv_array[0][0][1]), int(hsv_array[0][0][2])
        
        # Use explicit HSV-based rules for colors that are close in RGB
        # Priority order matters for similar colors
        
        # First check: Gray (low saturation)
        if s < 60 and 70 <= v <= 220:
            return 'gray'
        
        # Second: Pink vs Red - they're very close, use strict hue check
        # Pink: H around 171, Red: H around 170 but often lower
        if h >= 168:  # Higher hue = pink
            if 140 <= s <= 255 and 200 <= v <= 255:
                return 'pink'
        
        # Orange: H around 17, high saturation
        if 10 <= h <= 25 and s >= 160 and v >= 200:
            return 'orange'
        
        # Yellow: H around 20-30, very high value
        if 18 <= h <= 35 and s >= 140 and v >= 220:
            return 'yellow'
        
        # Green: H around 60-80
        if 60 <= h <= 90 and s >= 90 and v >= 190:
            return 'green'
        
        # Blue: H around 105-120
        if 100 <= h <= 125 and s >= 180 and v >= 200:
            return 'blue'
        
        # Red: Lower hue, or wrap case
        if (h <= 12 or h >= 165) and s >= 120 and v >= 190:
            # Make sure it's not pink (pink has higher hue and more saturation)
            if h < 168 or (h >= 168 and s < 140):
                return 'red'
        
        # Fallback: nearest neighbor in HSV
        best_match = None
        min_distance = float('inf')
        
        for color_name, (template_r, template_g, template_b) in self.COLOR_TEMPLATES.items():
            if color_name == 'grey':
                continue
            
            template_rgb = np.array([[template_r, template_g, template_b]], dtype=np.uint8).reshape(1, 1, 3)
            template_hsv = cv2.cvtColor(template_rgb, cv2.COLOR_RGB2HSV)
            template_h, template_s, template_v = int(template_hsv[0][0][0]), int(template_hsv[0][0][1]), int(template_hsv[0][0][2])
            
            # Weighted HSV distance
            h_dist = min(abs(h - template_h), 180 - abs(h - template_h))
            distance = h_dist * 5.0 + abs(s - template_s) * 0.5 + abs(v - template_v) * 0.5
            
            if distance < min_distance:
                min_distance = distance
                best_match = color_name
        
        if min_distance < 100:
            return best_match
        
        return None
    
    def _match_color(self, hsv_color: np.ndarray) -> str:
        """
        Legacy method - kept for compatibility but not used
        """
        return None
    
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
        
        # Last two tubes are always empty - skip analyzing them
        tubes_to_analyze = tubes[:-2] if len(tubes) >= 2 else tubes
        last_two_count = max(0, len(tubes) - len(tubes_to_analyze))
        
        for tube_rect in tubes_to_analyze:
            colors = self.extract_tube_colors(image, tube_rect)
            if not colors:
                empty_tubes += 1
                filled_tubelist.append([])
            else:
                filled_tubelist.append(colors)
        
        # Add last two tubes as empty (no analysis needed)
        for _ in range(last_two_count):
            empty_tubes += 1
            filled_tubelist.append([])
        
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
    
    def detect_next_button(self, image: np.ndarray = None) -> Optional[Tuple[int, int]]:
        """
        Detect the "Next" button on the completion screen
        Looks for a bright yellow button with "Next" text
        Returns: (x, y) center coordinates of the button in screen coordinates, or None if not found
        """
        if image is None:
            image = self.capture_screen()
        
        h, w = image.shape[:2]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define yellow color range (bright yellow button)
        # Yellow in HSV: H=20-30, S=100-255, V=200-255
        lower_yellow = np.array([20, 100, 200])
        upper_yellow = np.array([30, 255, 255])
        
        # Create mask for yellow pixels
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Find contours of yellow regions
        contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Look for a reasonably sized rectangular yellow region (the button)
        button_candidates = []
        for contour in contours:
            x, y, bw, bh = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Button should be:
            # - Reasonably sized (not too small, not too large)
            # - Rectangular-ish (width/height ratio between 2:1 and 4:1)
            # - Located in lower-middle area of screen
            if area > 500 and area < 50000:  # Reasonable button size
                aspect_ratio = bw / bh if bh > 0 else 0
                if 1.5 <= aspect_ratio <= 5.0:  # Button-like aspect ratio
                    # Check if it's in the lower-middle area
                    center_y = y + bh // 2
                    if center_y > h * 0.5:  # In lower half of screen
                        button_candidates.append((x + bw // 2, y + bh // 2, area))
        
        if button_candidates:
            # Sort by area (largest first) and take the best candidate
            button_candidates.sort(key=lambda x: x[2], reverse=True)
            bx, by, _ = button_candidates[0]
            
            # Convert to screen coordinates
            if self.game_region:
                x1, y1, x2, y2 = self.game_region
                screen_x = int(x1 + bx)
                screen_y = int(y1 + by)
                return (screen_x, screen_y)
            else:
                return (int(bx), int(by))
        
        return None

