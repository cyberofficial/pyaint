"""
Canvas Calibration Module

Handles canvas calibration using cross-pattern dot drawing approach.
Calibrates canvas to detect zoom level and adjust pixel size accordingly.
"""

import time
import pyautogui
from PIL import ImageGrab, Image
from typing import Optional, Tuple


class CanvasCalibrator:
    """Canvas calibration using cross-pattern dot measurement"""
    
    def __init__(self, canvas_coords):
        """
        Initialize calibrator with canvas coordinates.
        
        Parameters:
            canvas_coords: tuple (x, y, width, height) of canvas area
        """
        self.canvas_x, self.canvas_y, self.canvas_w, self.canvas_h = canvas_coords
        
    def dot_size_from_screenshot(self, center_x: int, center_y: int) -> Optional[Tuple[int, int]]:
        """
        Measure the size of a dot centered at given coordinates.
        
        Parameters:
            center_x, center_y: Expected center of dot
            
        Returns:
            Tuple (width, height) of measured dot, or None if failed
        """
        print(f"[Calibration] Measuring dot size at ({center_x}, {center_y})")
        
        # Capture screenshot
        try:
            canvas_screenshot = ImageGrab.grab(
                bbox=(self.canvas_x, self.canvas_y, 
                       self.canvas_x + self.canvas_w, self.canvas_y + self.canvas_h)
            )
        except Exception as e:
            print(f"[Calibration] Error capturing screenshot: {e}")
            return None
        
        # Convert to RGB
        if canvas_screenshot.mode != 'RGB':
            canvas_screenshot = canvas_screenshot.convert('RGB')
        
        # Get pixel data
        pixels = canvas_screenshot.load()
        img_w, img_h = canvas_screenshot.size
        
        # Get relative center position
        rel_center_x = center_x - self.canvas_x
        rel_center_y = center_y - self.canvas_y
        
        # Validate center position
        if not (0 <= rel_center_x < img_w and 0 <= rel_center_y < img_h):
            print(f"[Calibration] Center position out of bounds: ({rel_center_x}, {rel_center_y})")
            return None
        
        # Get reference color from center
        reference_color = pixels[rel_center_x, rel_center_y]
        print(f"[Calibration] Reference color: {reference_color}")
        
        # Find dot boundaries by scanning outward from center
        tolerance = 60  # Color tolerance for matching
        min_x, max_x = rel_center_x, rel_center_x
        min_y, max_y = rel_center_y, rel_center_y
        
        # Scan left - find left edge
        found_left = False
        for x in range(rel_center_x - 1, -1, -1):
            if x < 0:
                break
            try:
                r, g, b = pixels[x, rel_center_y]
                color_diff = abs(r - reference_color[0]) + abs(g - reference_color[1]) + abs(b - reference_color[2])
                if color_diff > tolerance:
                    min_x = x + 1
                    found_left = True
                    break
            except IndexError:
                break
        
        # Scan right - find right edge  
        for x in range(rel_center_x + 1, img_w):
            try:
                r, g, b = pixels[x, rel_center_y]
                color_diff = abs(r - reference_color[0]) + abs(g - reference_color[1]) + abs(b - reference_color[2])
                if color_diff > tolerance:
                    max_x = x - 1
                    break
            except IndexError:
                break
        
        # Scan up - find top edge
        found_top = False
        for y in range(rel_center_y - 1, -1, -1):
            if y < 0:
                break
            try:
                r, g, b = pixels[rel_center_x, y]
                color_diff = abs(r - reference_color[0]) + abs(g - reference_color[1]) + abs(b - reference_color[2])
                if color_diff > tolerance:
                    min_y = y + 1
                    found_top = True
                    break
            except IndexError:
                break
        
        # Scan down - find bottom edge
        for y in range(rel_center_y + 1, img_h):
            try:
                r, g, b = pixels[rel_center_x, y]
                color_diff = abs(r - reference_color[0]) + abs(g - reference_color[1]) + abs(b - reference_color[2])
                if color_diff > tolerance:
                    max_y = y - 1
                    break
            except IndexError:
                break
        
        # Calculate dot dimensions
        measured_w = max_x - min_x + 1
        measured_h = max_y - min_y + 1
        
        print(f"[Calibration] Dot bounds: ({min_x}, {min_y}) to ({max_x}, {max_y})")
        print(f"[Calibration] Measured dot size: {measured_w}x{measured_h}px")
        
        # Validate measurement
        if measured_w < 1 or measured_h < 1:
            print("[Calibration] WARNING: Measured dot size seems invalid")
            return None
        
        if not found_left or not found_top:
            print("[Calibration] WARNING: Could not find all edges clearly")
            # Still try to use what we found
        
        return (measured_w, measured_h)
    
    def measure_spacing(self, center_pos: Tuple[int, int], 
                   left_pos: Tuple[int, int], 
                   top_pos: Tuple[int, int]) -> Optional[Tuple[float, float]]:
        """
        Measure spacing between three dot centers.
        
        Parameters:
            center_pos: (x, y) center dot
            left_pos: (x, y) left dot
            top_pos: (x, y) top dot
            
        Returns:
            Tuple (horizontal_spacing, vertical_spacing) or None if failed
        """
        print(f"[Calibration] Measuring spacing between dots")
        
        def find_dot_center(abs_pos: Tuple[int, int]):
            """Find center of a dot"""
            rel_x = abs_pos[0] - self.canvas_x
            rel_y = abs_pos[1] - self.canvas_y
            
            try:
                canvas_screenshot = ImageGrab.grab(
                    bbox=(self.canvas_x, self.canvas_y,
                           self.canvas_x + self.canvas_w, self.canvas_y + self.canvas_h)
                )
            except Exception as e:
                print(f"[Calibration] Error capturing screenshot: {e}")
                return None
            
            if canvas_screenshot.mode != 'RGB':
                canvas_screenshot = canvas_screenshot.convert('RGB')
            
            pixels = canvas_screenshot.load()
            img_w, img_h = canvas_screenshot.size
            
            if not (0 <= rel_x < img_w and 0 <= rel_y < img_h):
                return None
            
            # Get reference color
            reference_color = pixels[rel_x, rel_y]
            
            # Find dot boundaries
            tolerance = 60
            min_x, max_x = rel_x, rel_x
            min_y, max_y = rel_y, rel_y
            
            # Scan edges
            for x in range(rel_x, img_w):
                try:
                    r, g, b = pixels[x, rel_y]
                    color_diff = abs(r - reference_color[0]) + abs(g - reference_color[1]) + abs(b - reference_color[2])
                    if color_diff > tolerance:
                        max_x = x - 1
                        break
                except IndexError:
                    break
            
            for y in range(rel_y, img_h):
                try:
                    r, g, b = pixels[rel_x, y]
                    color_diff = abs(r - reference_color[0]) + abs(g - reference_color[1]) + abs(b - reference_color[2])
                    if color_diff > tolerance:
                        max_y = y - 1
                        break
                except IndexError:
                    break
            
            # Calculate center
            center = ((min_x + max_x) // 2, (min_y + max_y) // 2)
            return center
        
        # Find centers of all three dots
        center_center = find_dot_center(center_pos)
        left_center = find_dot_center(left_pos)
        top_center = find_dot_center(top_pos)
        
        if None in (center_center, left_center, top_center):
            print("[Calibration] Could not find all dot centers")
            return None
        
        # Calculate actual spacing
        h_spacing = abs(left_center[0] - center_center[0])
        v_spacing = abs(top_center[1] - center_center[1])
        
        print(f"[Calibration] Measured spacing: horizontal={h_spacing}px, vertical={v_spacing}px")
        
        return (h_spacing, v_spacing)


def run_calibration(canvas_coords: tuple, intended_spacing: int = 10, 
                 user_brush_size: int = None) -> dict:
    """
    Run complete canvas calibration process.
    
    Parameters:
        canvas_coords: tuple (x, y, width, height) of canvas
        intended_spacing: int - The pixel size/spacing to use for calibration
        user_brush_size: int - The brush size selected in paint app (optional)
    
    Returns:
        Dictionary with calibration results, or None if failed:
        {
            'scale_factor': float,
            'measured_spacing': float,
            'intended_spacing': int,
            'dot_size': (int, int),
            'user_brush_size': int,
            'dot_positions': list,
            'calibration_date': str
        }
    """
    calibrator = CanvasCalibrator(canvas_coords)
    
    print(f"[Calibration] Starting calibration")
    print(f"[Calibration] Canvas: ({canvas_coords})")
    print(f"[Calibration] Intended spacing: {intended_spacing}px")
    print(f"[Calibration] User brush size: {user_brush_size}px")
    
    # Calculate canvas center
    center_x = canvas_coords[0] + canvas_coords[2] // 2
    center_y = canvas_coords[1] + canvas_coords[3] // 2
    
    # Step 1: Draw center dot
    print(f"[Calibration] Step 1: Drawing center dot")
    pyautogui.moveTo(center_x, center_y)
    time.sleep(0.05)
    pyautogui.click(button='left')
    time.sleep(1.0)
    
    # Measure center dot
    dot_size = calibrator.dot_size_from_screenshot(center_x, center_y)
    if dot_size is None:
        print("[Calibration] ERROR: Failed to measure center dot")
        return None
    
    measured_dot_w, measured_dot_h = dot_size
    avg_dot_size = int(round((measured_dot_w + measured_dot_h) / 2))
    print(f"[Calibration] Measured dot size: {measured_dot_w}x{measured_dot_h}, avg: {avg_dot_size}")
    
    # Step 2: Calculate cross pattern positions
    dot_spacing = intended_spacing * 6  # Scale dot positions based on step size
    dot_positions = [
        (center_x, center_y),  # Center (already drawn)
        (center_x - 2 * dot_spacing, center_y - 2 * dot_spacing),  # Top-left
        (center_x + 2 * dot_spacing, center_y - 2 * dot_spacing),  # Top-right
        (center_x - 2 * dot_spacing, center_y + 2 * dot_spacing),  # Bottom-left
        (center_x + 2 * dot_spacing, center_y + 2 * dot_spacing),  # Bottom-right
        (center_x - dot_spacing, center_y),  # Left
        (center_x + dot_spacing, center_y),  # Right
        (center_x, center_y - dot_spacing),  # Top
        (center_x, center_y + dot_spacing),  # Bottom
    ]
    
    # Step 3: Draw remaining dots
    print(f"[Calibration] Step 2: Drawing {len(dot_positions)-1} additional dots")
    
    # Move cursor away first to avoid blocking view
    print(f"[Calibration] Moving cursor away from canvas")
    pyautogui.moveTo(canvas_coords[0] + canvas_coords[2] + 100, center_y)
    time.sleep(0.1)
    
    for i, (dot_x, dot_y) in enumerate(dot_positions[1:], 1):
        print(f"[Calibration] Drawing dot {i} at ({dot_x}, {dot_y})")
        pyautogui.moveTo(dot_x, dot_y)
        time.sleep(0.02)
        pyautogui.click(button='left')
        time.sleep(0.15)
    
    # Step 4: Wait for canvas to finish
    print(f"[Calibration] Step 3: Waiting 5 seconds for canvas to catch up")
    time.sleep(5.0)
    
    # Step 5: Measure spacing
    measured_spacing = calibrator.measure_spacing(
        dot_positions[0],  # center
        dot_positions[5],  # left
        dot_positions[6]   # top
    )
    
    if measured_spacing is None:
        print("[Calibration] ERROR: Failed to measure dot spacing")
        return None
    
    horiz_spacing, vert_spacing = measured_spacing
    avg_measured_spacing = (horiz_spacing + vert_spacing) / 2
    
    # Calculate scale factor
    scale_factor = avg_measured_spacing / intended_spacing
    
    print(f"[Calibration] Measured spacing: h={horiz_spacing}, v={vert_spacing}, avg={avg_measured_spacing:.2f}")
    print(f"[Calibration] Intended spacing: {intended_spacing}")
    print(f"[Calibration] Scale factor: {scale_factor:.4f}")
    
    import datetime
    calibration_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    results = {
        'scale_factor': scale_factor,
        'measured_spacing': avg_measured_spacing,
        'intended_spacing': intended_spacing,
        'dot_size': (int(round(measured_dot_w)), int(round(measured_dot_h))),
        'user_brush_size': user_brush_size if user_brush_size else 0,
        'dot_positions': dot_positions,
        'calibration_date': calibration_date
    }
    
    print(f"[Calibration] Calibration complete!")
    print(f"[Calibration] Scale factor: {scale_factor*100:.0f}%")
    
    return results
