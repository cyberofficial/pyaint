"""
Canvas Calibration Module

Single-dot diff-based canvas calibration.

The user is asked to clear their canvas, then one dot is drawn at the center
using their selected brush. The blank canvas and the dotted canvas are both
screenshotted; a pixel diff yields the dot's bounding box. The scale factor
is measured_dot_size / brush_size, directly capturing the app's zoom level.
"""

import datetime
import time

import pyautogui
from PIL import ImageChops, ImageGrab
from typing import Optional, Tuple


class CanvasCalibrator:
    """Canvas calibration using single-dot screenshot diffing."""

    def __init__(self, canvas_coords):
        """
        Initialize calibrator with canvas coordinates.

        Parameters:
            canvas_coords: tuple (x, y, width, height) of canvas area
        """
        self.canvas_x, self.canvas_y, self.canvas_w, self.canvas_h = canvas_coords

    @staticmethod
    def measure_dot_from_diff(screenshot_before, screenshot_after) -> Optional[Tuple[int, int]]:
        """
        Measure the bounding box of a drawn dot by diffing two screenshots.

        Parameters:
            screenshot_before: PIL Image of the blank canvas
            screenshot_after:  PIL Image of the canvas after drawing one dot

        Returns:
            Tuple (width, height) of the measured dot, or None if no
            difference was detected (dot did not render / same color).
        """
        before = screenshot_before.convert('RGB')
        after = screenshot_after.convert('RGB')

        diff = ImageChops.difference(before, after)
        bbox = diff.getbbox()  # (left, top, right, bottom) of changed pixels

        if bbox is None:
            print("[Calibration] No difference detected between screenshots")
            return None

        left, top, right, bottom = bbox
        measured_w = right - left
        measured_h = bottom - top

        print(f"[Calibration] Dot bounds: ({left}, {top}) to ({right}, {bottom})")
        print(f"[Calibration] Measured dot size: {measured_w}x{measured_h}px")

        if measured_w < 1 or measured_h < 1:
            print("[Calibration] WARNING: Measured dot size seems invalid")
            return None

        return (measured_w, measured_h)


def run_calibration(canvas_coords: tuple, brush_size: int) -> Optional[dict]:
    """
    Run single-dot diff-based canvas calibration.

    The canvas must be empty when this is called. A dot is drawn at the
    canvas center with the user's selected brush; before/after screenshots
    are diffed to measure the dot's rendered size.

    Parameters:
        canvas_coords: tuple (x, y, width, height) of the canvas on screen
        brush_size:    the brush size (px) selected in the paint app

    Returns:
        Dictionary with calibration results, or None if failed:
        {
            'scale_factor': float,
            'measured_spacing': float (avg dot size, kept for compat),
            'intended_spacing': int (brush size),
            'dot_size': (int, int),
            'user_brush_size': int,
            'dot_positions': list,
            'calibration_date': str
        }
    """
    calibrator = CanvasCalibrator(canvas_coords)

    canvas_x, canvas_y, canvas_w, canvas_h = canvas_coords
    center_x = canvas_x + canvas_w // 2
    center_y = canvas_y + canvas_h // 2

    print(f"[Calibration] Starting single-dot calibration")
    print(f"[Calibration] Canvas: ({canvas_coords})")
    print(f"[Calibration] Brush size: {brush_size}px")

    # Step 1: move cursor away and capture the blank canvas
    pyautogui.moveTo(canvas_x + canvas_w + 100, center_y)
    time.sleep(0.2)
    try:
        blank = ImageGrab.grab(
            bbox=(canvas_x, canvas_y, canvas_x + canvas_w, canvas_y + canvas_h))
    except Exception as e:
        print(f"[Calibration] Error capturing blank canvas: {e}")
        return None

    # Step 2: draw one dot at the canvas center
    print(f"[Calibration] Drawing dot at ({center_x}, {center_y})")
    pyautogui.moveTo(center_x, center_y)
    time.sleep(0.05)
    pyautogui.click(button='left')
    time.sleep(0.3)

    # Step 3: move cursor away (so it never pollutes the diff) and capture again
    pyautogui.moveTo(canvas_x + canvas_w + 100, center_y)
    time.sleep(0.5)
    try:
        dotted = ImageGrab.grab(
            bbox=(canvas_x, canvas_y, canvas_x + canvas_w, canvas_y + canvas_h))
    except Exception as e:
        print(f"[Calibration] Error capturing dotted canvas: {e}")
        return None

    # Step 4: measure the dot via pixel diff
    dot_size = calibrator.measure_dot_from_diff(blank, dotted)
    if dot_size is None:
        print("[Calibration] ERROR: Dot not detected. "
              "Make sure your selected color contrasts with the canvas background.")
        return None

    measured_dot_w, measured_dot_h = dot_size
    avg_dot_size = (measured_dot_w + measured_dot_h) / 2.0
    scale_factor = avg_dot_size / brush_size if brush_size > 0 else 1.0

    print(f"[Calibration] Scale factor: {scale_factor:.4f}")

    results = {
        'scale_factor': scale_factor,
        'measured_spacing': avg_dot_size,
        'intended_spacing': brush_size,
        'dot_size': (measured_dot_w, measured_dot_h),
        'user_brush_size': brush_size,
        'dot_positions': [(center_x, center_y)],
        'calibration_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    print(f"[Calibration] Calibration complete!")
    print(f"[Calibration] Scale factor: {scale_factor*100:.0f}%")

    return results
