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
import os
from datetime import datetime


class ImageProcessor:
    """Processes screenshots to extract puzzle state"""
    
    # Color mapping using BGR ranges (OpenCV uses BGR format)
    # Format: 'color_name': ((B_min, G_min, R_min), (B_max, G_max, R_max))
    COLOR_RANGES_BGR = {
        'red': ((0, 0, 180), (80, 80, 255)),
        'orange': ((0, 100, 200), (100, 180, 255)),
        'yellow': ((0, 180, 180), (100, 255, 255)),
        'green': ((100, 180, 20), (190, 255, 150)),  # Green/Mint: covers RGB(41,223,152)=BGR(152,223,41) and RGB(112,224,147)=BGR(147,224,112)
        'rose': ((100, 90, 220), (160, 130, 255)),  # Medium pink/rose RGB(239,108,130) = BGR(130,108,239)
        'blue': ((150, 0, 0), (255, 80, 80)),
        'gray': ((50, 50, 50), (150, 150, 150)),
    }
    
    # Dark blue background range (used to detect empty blocks)
    # Dark blue background: very dark blue/black
    DARK_BACKGROUND_BGR = ((0, 0, 0), (60, 60, 60))  # Very dark, slightly blueish
    
    def __init__(self, game_region: Tuple[int, int, int, int] = None, unit_height: float = None):
        """
        Initialize image processor
        Args:
            game_region: (x1, y1, x2, y2) coordinates of game area
            unit_height: Calibrated height of one liquid unit in pixels
        """
        self.game_region = game_region
        self.unit_height = unit_height  # Calibrated unit height from user
        self.current_turn = 1  # Track current turn number for logging
        self.logs_dir = "logs"  # Base directory for logs
    
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
    
    def set_turn(self, turn: int):
        """Set the current turn number for logging"""
        self.current_turn = turn
    
    def _ensure_log_directories(self, turn: int, tube_idx: int):
        """Ensure log directories exist for a specific turn and tube"""
        turn_dir = os.path.join(self.logs_dir, f"turn{turn}")
        tube_dir = os.path.join(turn_dir, f"tube{tube_idx}")
        os.makedirs(tube_dir, exist_ok=True)
        return tube_dir
    
    def _save_block_image(self, block_img: np.ndarray, turn: int, tube_idx: int, block_idx: int, color_name: str):
        """Save a color block image to the log directory"""
        try:
            tube_dir = self._ensure_log_directories(turn, tube_idx)
            filename = f"block{block_idx}_{color_name}.png"
            filepath = os.path.join(tube_dir, filename)
            cv2.imwrite(filepath, block_img)
        except Exception as e:
            print(f"Warning: Could not save block image: {e}")
    
    def _save_tube_image(self, tube_img: np.ndarray, turn: int, tube_idx: int):
        """Save the full tube image for debugging"""
        try:
            tube_dir = self._ensure_log_directories(turn, tube_idx)
            filename = f"tube{tube_idx}_full.png"
            filepath = os.path.join(tube_dir, filename)
            cv2.imwrite(filepath, tube_img)
        except Exception as e:
            print(f"Warning: Could not save tube image: {e}")
    
    def extract_tube_colors(self, image: np.ndarray, tube_rect: Tuple[int, int, int, int], tube_idx: int = 0) -> List[str]:
        """
        SUPER SIMPLE: Get exactly 5 images per tube (1 full + 4 blocks)
        - Start at 10% from bottom
        - Jump 20% up 4 times
        - Get pixel, get color, save picture, move to next block
        
        Args:
            image: Full game image
            tube_rect: (x, y, width, height) of the tube
            tube_idx: Index of the tube (for logging)
        Returns: List of color names from bottom to top (non-empty blocks only)
        """
        x, y, w, h = tube_rect
        
        # Extract tube image
        tube_img = image[y:y+h, x:x+w].copy()
        if tube_img.size == 0:
            return []
        
        # Create annotated copy for drawing block indices
        annotated_tube = tube_img.copy()
        
        # Setup: center X, start at 10% from bottom, jump 20% each time
        center_x = w // 2
        jump_distance = h * 0.2  # 20% of tube height
        start_y = int(h - (h * 0.1))  # 10% from bottom
        
        colors = []
        block_positions = []  # Store positions for annotation
        
        # Process exactly 4 blocks (Images 2-5)
        for block_idx in range(4):
            # Calculate Y position: start at 10%, then jump 20% up each time
            block_y = int(start_y - (block_idx * jump_distance))
            
            # Ensure Y is within bounds
            block_y = max(0, min(h - 1, block_y))
            
            # Store position for annotation
            block_positions.append((center_x, block_y))
            
            # Get pixel at center X, calculated Y
            pixel_bgr = tube_img[block_y, center_x]
            b, g, r = int(pixel_bgr[0]), int(pixel_bgr[1]), int(pixel_bgr[2])
            
            # Get color
            detected_color = self._match_color_rgb(pixel_bgr)
            
            # If empty (darkbackground or None), use 'empty' as color name for saving
            color_name = detected_color if detected_color and detected_color != 'darkbackground' else 'empty'
            
            # Save block image (always save, even if empty)
            pixel_img = np.zeros((10, 10, 3), dtype=np.uint8)
            pixel_img[:, :] = pixel_bgr
            # self._save_block_image(pixel_img, self.current_turn, tube_idx, block_idx, color_name)
            # print(f"✓ Tube {tube_idx}: Saved block{block_idx}_{color_name}.png")
            
            # Only add non-empty colors to result list
            if detected_color and detected_color != 'darkbackground':
                colors.append(detected_color)
        
        # Draw block index numbers in red at each sampling point
        for block_idx, (px_x, px_y) in enumerate(block_positions):
            # Draw red text showing block index
            # Use a visible font size based on tube dimensions
            font_scale = max(0.5, min(w, h) / 100.0)
            thickness = max(1, int(font_scale * 2))
            
            # Draw the number in red (BGR format: (0, 0, 255) = red)
            cv2.putText(annotated_tube, str(block_idx), (px_x, px_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
        
        # Save annotated full tube image (Image 1/5)
        # self._save_tube_image(annotated_tube, self.current_turn, tube_idx)
        # print(f"✓ Tube {tube_idx}: Saved annotated full tube image with block indices")
        
        return colors
        
        # # ===================================================================
        # # STEP 3: Define inner region to avoid borders
        # # Tube borders are light gray, so we exclude edges to sample only liquid color
        # # ===================================================================
        # border_margin_x = max(2, int(w * 0.15))  # Horizontal margin to exclude borders (~15% from each side)
        # border_margin_y = max(2, int(h * 0.05))    # Small vertical margin (~5% from top/bottom)
        
        # inner_x1 = border_margin_x
        # inner_x2 = w - border_margin_x
        # inner_w = inner_x2 - inner_x1
        
        # print(f"\n🔲 Border exclusion:")
        # print(f"   Horizontal margins: {border_margin_x}px from each side")
        # print(f"   Inner region: x=[{inner_x1}, {inner_x2}], width={inner_w}px")
        
        # # Sample region: center of inner area, very small to get only color
        # center_x = inner_x1 + inner_w // 2
        # sample_size = max(3, min(10, inner_w // 3))  # Very small sample (3-10 pixels)
        # sample_x1 = center_x - sample_size // 2
        # sample_x2 = center_x + sample_size // 2
        
        # print(f"   Sample region: x=[{sample_x1}, {sample_x2}], size={sample_size}px")
        
        # # ===================================================================
        # # STEP 4: Calculate starting position (account for rounded bottom)
        # # ===================================================================
        # tube_bottom = h - 1
        # bottom_padding = max(5, int(h * 0.1))  # Skip rounded bottom area
        
        # print(f"\n📍 Starting position:")
        # print(f"   Tube bottom: y={tube_bottom}")
        # print(f"   Bottom padding (rounded base): {bottom_padding}px")
        
        # # ===================================================================
        # # STEP 5: Detect blocks from BOTTOM TO TOP (block 0 = bottom, block 3 = top)
        # # Each block is fixed size (unit_height), bounded by light gray borders
        # # ===================================================================
        # print(f"\n{'='*60}")
        # print(f"🎯 DETECTING BLOCKS (bottom to top):")
        # print(f"{'='*60}")
        
        # detected_blocks = []
        
        # for block_idx in range(max_blocks):
        #     print(f"\n--- BLOCK {block_idx} (position from bottom) ---")
            
        #     # ===============================================================
        #     # BLOCK DETECTION: Calculate block center Y position
        #     # Block positions jump by unit_height from bottom to top:
        #     # - Block 0 (bottom): center at (tube_bottom - bottom_padding - unit_height/2)
        #     # - Block 1: Block 0 center - unit_height
        #     # - Block 2: Block 0 center - 2*unit_height  
        #     # - Block 3 (top): Block 0 center - 3*unit_height
        #     # ===============================================================
        #     block_center_y = int(tube_bottom - bottom_padding - (block_idx * unit_height) - (unit_height / 2))
            
        #     print(f"   📍 Block center Y: {block_center_y}px")
            
        #     # Check if we've gone past the top of the tube
        #     if block_center_y < 0:
        #         print(f"   ⚠️  Block {block_idx} is beyond tube top - stopping")
        #         break
            
        #     # ===============================================================
        #     # COLOR SAMPLING: Sample a very small region at block center
        #     # We sample from inner area only to avoid light gray borders
        #     # ===============================================================
        #     sample_y_start = max(border_margin_y, block_center_y - 2)
        #     sample_y_end = min(h - border_margin_y, block_center_y + 3)
        #     sample_x_start = max(inner_x1, sample_x1)
        #     sample_x_end = min(inner_x2, sample_x2)
            
        #     print(f"   🔍 Sampling region: x=[{sample_x_start}, {sample_x_end}], y=[{sample_y_start}, {sample_y_end}]")
            
        #     if sample_y_end <= sample_y_start or sample_x_end <= sample_x_start:
        #         print(f"   ⚠️  Invalid sample region - stopping")
        #         break
            
        #     # Extract sample region from inner area and get median HSV
        #     sample_region_hsv = hsv_tube[sample_y_start:sample_y_end, sample_x_start:sample_x_end]
            
        #     if sample_region_hsv.size == 0:
        #         print(f"   ⚠️  Empty sample region - stopping")
        #         break
            
        #     # Get median HSV from the sample region (more robust than mean)
        #     if sample_region_hsv.ndim == 3:
        #         median_hsv = np.median(sample_region_hsv.reshape(-1, 3), axis=0).astype(np.uint8)
        #     else:
        #         median_hsv = sample_region_hsv.astype(np.uint8)
            
        #     if len(median_hsv) < 3:
        #         print(f"   ⚠️  Invalid HSV data - stopping")
        #         break
            
        #     print(f"   🎨 Median HSV: H={median_hsv[0]}, S={median_hsv[1]}, V={median_hsv[2]}")
            
        #     # ===============================================================
        #     # COLOR DETECTION: Match HSV to a known color name
        #     # ===============================================================
        #     detected_color = self._match_color_improved(median_hsv)
            
        #     # If no color detected, this block is empty (or we've reached the top)
        #     if not detected_color:
        #         print(f"   ⚪ Block {block_idx}: EMPTY (no color detected)")
        #         break
            
        #     print(f"   ✅ Block {block_idx}: Color detected = '{detected_color}'")
            
        #     # ===============================================================
        #     # BLOCK IMAGE EXTRACTION: Extract the full block image
        #     # Block boundaries: from (block_center_y - unit_height/2) to (block_center_y + unit_height/2)
        #     # We exclude borders to get only the liquid color
        #     # ===============================================================
        #     block_top_y = max(border_margin_y, int(block_center_y - unit_height / 2))
        #     block_bottom_y = min(h - border_margin_y, int(block_center_y + unit_height / 2))
            
        #     print(f"   📦 Block boundaries: top_y={block_top_y}, bottom_y={block_bottom_y}, height={block_bottom_y-block_top_y+1}px")
        #     print(f"   🖼️  Extracting inner block image (excluding borders): x=[{inner_x1}, {inner_x2}], y=[{block_top_y}, {block_bottom_y}]")
            
        #     # Extract the INNER block image (exclude borders, use inner width)
        #     # This gives us a clean block image without border contamination
        #     block_img = tube_img[block_top_y:block_bottom_y+1, inner_x1:inner_x2].copy()
            
        #     # Save block image for logging
        #     filename = f"block{block_idx}_{detected_color}.png"
        #     print(f"   💾 Saving block image: {filename}")
        #     self._save_block_image(block_img, self.current_turn, tube_idx, block_idx, detected_color)
            
        #     # Add color to result list (bottom to top order)
        #     colors.append(detected_color)
        #     print(f"   ✓ Block {block_idx} added: '{detected_color}'")
            
        #     # Store for debugging if needed
        #     detected_blocks.append((detected_color, block_top_y, block_bottom_y))
        
        # # ===================================================================
        # # FINAL RESULT: List of colors from bottom to top
        # # ===================================================================
        # print(f"\n{'='*60}")
        # print(f"✅ TUBE {tube_idx} DETECTION COMPLETE")
        # print(f"{'='*60}")
        # print(f"📊 Detected {len(colors)} blocks:")
        # for i, color in enumerate(colors):
        #     print(f"   Block {i} (bottom->top): '{color}'")
        # print(f"\n📋 Result (bottom to top): {colors}")
        # print(f"{'='*60}\n")
        
        # return colors
    
    # def calibrate_unit_height(self) -> float:
    #     """
    #     Calibrate unit height by asking user to click top and bottom of a single block
    #     Returns: The calibrated unit height in pixels
    #     """
    #     import pyautogui
        
    #     print("\n" + "=" * 60)
    #     print("UNIT HEIGHT CALIBRATION")
    #     print("=" * 60)
    #     print("\nPlease click on the BOTTOM of a single color block")
    #     print("(e.g., the bottom edge of one liquid unit)")
    #     print("You have 5 seconds to position your mouse...")
    #     time.sleep(2)
        
    #     try:
    #         from pynput import mouse
            
    #         bottom_clicked = False
    #         bottom_pos = None
            
    #         def on_click(x, y, button, pressed):
    #             nonlocal bottom_clicked, bottom_pos
    #             if pressed and button == mouse.Button.left:
    #                 bottom_pos = (x, y)
    #                 bottom_clicked = True
    #                 return False
            
    #         listener = mouse.Listener(on_click=on_click)
    #         listener.start()
            
    #         start_time = time.time()
    #         while not bottom_clicked and (time.time() - start_time) < 10:
    #             time.sleep(0.1)
            
    #         listener.stop()
            
    #         if not bottom_clicked or not bottom_pos:
    #             bottom_pos = pyautogui.position()
    #     except ImportError:
    #         input("Press Enter after clicking the BOTTOM of a block...")
    #         bottom_pos = pyautogui.position()
        
    #     print(f"✓ Bottom position recorded: {bottom_pos}")
        
    #     print("\nPlease click on the TOP of the SAME color block")
    #     print("(e.g., the top edge of the same liquid unit)")
    #     print("You have 5 seconds to position your mouse...")
    #     time.sleep(2)
        
    #     try:
    #         from pynput import mouse
            
    #         top_clicked = False
    #         top_pos = None
            
    #         def on_click(x, y, button, pressed):
    #             nonlocal top_clicked, top_pos
    #             if pressed and button == mouse.Button.left:
    #                 top_pos = (x, y)
    #                 top_clicked = True
    #                 return False
            
    #         listener = mouse.Listener(on_click=on_click)
    #         listener.start()
            
    #         start_time = time.time()
    #         while not top_clicked and (time.time() - start_time) < 10:
    #             time.sleep(0.1)
            
    #         listener.stop()
            
    #         if not top_clicked or not top_pos:
    #             top_pos = pyautogui.position()
    #     except ImportError:
    #         input("Press Enter after clicking the TOP of the block...")
    #         top_pos = pyautogui.position()
        
    #     print(f"✓ Top position recorded: {top_pos}")
        
    #     # Calculate unit height (absolute difference in y coordinates)
    #     if self.game_region:
    #         x1, y1, x2, y2 = self.game_region
    #         # Convert screen coordinates to relative coordinates
    #         bottom_y_rel = bottom_pos[1] - y1
    #         top_y_rel = top_pos[1] - y1
    #         unit_height = abs(bottom_y_rel - top_y_rel)
    #     else:
    #         unit_height = abs(bottom_pos[1] - top_pos[1])
        
    #     self.unit_height = unit_height
        
    #     print(f"\n✓ Unit height calibrated: {unit_height:.1f} pixels")
    #     print(f"  This will be used to count consecutive color blocks (1x, 2x, 3x, etc.)\n")
        
    #     return unit_height
    
    def _match_color_rgb(self, bgr_color: np.ndarray) -> Optional[str]:
        """
        REWRITTEN: Simple RGB/BGR color matching
        Matches BGR color to one of 7 colors or dark blue background
        Args:
            bgr_color: BGR color array [B, G, R] from OpenCV
        Returns:
            Color name or 'darkbackground' or None
        """
        # Extract BGR values
        if isinstance(bgr_color, np.ndarray):
            if bgr_color.ndim == 1:
                b, g, r = int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2])
            else:
                b, g, r = int(bgr_color[0][0]), int(bgr_color[0][1]), int(bgr_color[0][2])
        else:
            b, g, r = int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2])
        
        # First check: Dark blue background detection
        # Dark blue background means the block is empty
        bg_lower, bg_upper = self.DARK_BACKGROUND_BGR
        if (bg_lower[0] <= b <= bg_upper[0] and
            bg_lower[1] <= g <= bg_upper[1] and
            bg_lower[2] <= r <= bg_upper[2]):
            return 'darkbackground'
        
        # Check each of the 7 liquid colors
        for color_name, (lower_bgr, upper_bgr) in self.COLOR_RANGES_BGR.items():
            if (lower_bgr[0] <= b <= upper_bgr[0] and
                lower_bgr[1] <= g <= upper_bgr[1] and
                lower_bgr[2] <= r <= upper_bgr[2]):
                return color_name
        
        return None
    
    def _match_color_improved(self, hsv_color: np.ndarray) -> Optional[str]:
        """Legacy method - kept for compatibility"""
        return self._match_color_rgb(hsv_color)
    
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
        
        # Analyze ALL tubes (no skipping)
        for tube_idx, tube_rect in enumerate(tubes):
            colors = self.extract_tube_colors(image, tube_rect, tube_idx=tube_idx)
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
    
    def detect_next_button(self, image: np.ndarray = None) -> Optional[Tuple[int, int]]:
        """
        Detect the "Next" button on the completion screen
        Looks for a yellow button with brown border (rectangular, rounded corners)
        Returns: (x, y) center coordinates of the button in screen coordinates, or None if not found
        """
        if image is None:
            image = self.capture_screen()
        
        h, w = image.shape[:2]
        
        # Convert to BGR for color detection (yellow button)
        # Yellow button: RGB values around (255, 200-255, 0-50) = BGR(0-50, 200-255, 255)
        # Use BGR ranges for yellow
        yellow_lower = np.array([0, 180, 200], dtype=np.uint8)
        yellow_upper = np.array([60, 255, 255], dtype=np.uint8)
        
        # Create mask for yellow pixels
        yellow_mask = cv2.inRange(image, yellow_lower, yellow_upper)
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
        yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours of yellow regions
        contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Look for a reasonably sized rectangular yellow region (the button)
        button_candidates = []
        for contour in contours:
            x, y, bw, bh = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Button should be:
            # - Reasonably sized (not too small, not too large)
            # - Rectangular-ish (width/height ratio between 1.5:1 and 5:1)
            # - Located in lower-middle area of screen (bottom 40% of screen)
            if area > 1000 and area < 50000:  # Reasonable button size
                aspect_ratio = bw / bh if bh > 0 else 0
                if 1.5 <= aspect_ratio <= 5.0:  # Button-like aspect ratio
                    # Check if it's in the lower-middle area (bottom 40%)
                    center_y = y + bh // 2
                    if center_y > h * 0.6:  # In lower 40% of screen
                        button_candidates.append((x + bw // 2, y + bh // 2, area, bw, bh))
        
        if button_candidates:
            # Sort by area (largest first) and take the best candidate
            button_candidates.sort(key=lambda x: x[2], reverse=True)
            bx, by, _, _, _ = button_candidates[0]
            
            # Convert to screen coordinates
            if self.game_region:
                x1, y1, x2, y2 = self.game_region
                screen_x = int(x1 + bx)
                screen_y = int(y1 + by)
                return (screen_x, screen_y)
            else:
                return (int(bx), int(by))
        
        return None

