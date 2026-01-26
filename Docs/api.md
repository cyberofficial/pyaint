# Pyaint API Reference

Complete API documentation for Pyaint's core components.

## Table of Contents

- [Bot Class](#bot-class)
- [Palette Class](#palette-class)
- [Utility Functions](#utility-functions)
- [Exception Classes](#exception-classes)
- [UI Components](#ui-components)
- [Configuration](#configuration)

---

## Bot Class

The main `Bot` class handles all drawing automation operations.

### Constructor

```python
Bot(config_file='config.json')
```

Creates a new Bot instance.

**Parameters:**
- `config_file` (str) - Path to config file (default: 'config.json')

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `config_file` | str | Path to configuration file |
| `terminate` | bool | Flag to stop all operations |
| `paused` | bool | Flag to pause/resume drawing |
| `drawing` | bool | Flag indicating if currently drawing |
| `pause_key` | str | Key for pause/resume (default: 'p') |
| `skip_first_color` | bool | Skip first color when drawing (default: False) |
| `jump_threshold` | int | Pixel distance threshold for jump detection (default: 5) |
| `options` | int | Drawing feature flags (bitmask) |
| `progress` | float | Processing progress (0-100) |
| `total_strokes` | int | Total number of strokes in current drawing |
| `completed_strokes` | int | Number of completed strokes in current drawing |
| `start_time` | float | Start time for drawing operations |
| `estimated_time_seconds` | float | Estimated drawing time in seconds |

#### Settings List

Drawing settings are stored as a list accessible via the `settings` property:

| Index | Constant | Type | Description |
|-------|----------|------|-------------|
| 0 | `DELAY` | float | Duration of each brush stroke (seconds) |
| 1 | `STEP` | int | Detail level - pixels between sample points |
| 2 | `ACCURACY` | float | Color accuracy threshold (0.0 - 1.0) |
| 3 | `JUMP_DELAY` | float | Delay on cursor jumps > jump_threshold |

**Note:** `jump_threshold` is a separate attribute (not in settings list).

Access via property: `bot.settings[Bot.DELAY]`, `bot.settings[Bot.STEP]`, etc.

#### State Tracking Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `draw_state` | dict | State tracking for pause/resume with keys: color_idx, line_idx, segment_idx, current_color, cmap, was_paused |
| `new_layer` | dict | New layer configuration with keys: enabled, coords, modifiers |
| `color_button` | dict | Color button configuration with keys: status, coords, enabled, delay, modifiers |
| `color_button_okay` | dict | Color button okay configuration with keys: status, coords, enabled, delay, modifiers |
| `mspaint_mode` | dict | MSPaint mode configuration with keys: enabled, delay |
| `color_calibration_map` | dict or None | RGB to (x, y) coordinate mapping |

#### Internal Tool References

| Attribute | Type | Description |
|-----------|------|-------------|
| `_canvas` | tuple or None | Canvas coordinates (left, top, width, height) |
| `_palette` | Palette or None | Palette object instance |
| `_custom_colors` | tuple or None | Custom colors spectrum coordinates |
| `_spectrum_map` | dict or None | Spectrum color-to-position map |
| `_overlay_window` | tk.Toplevel or None | Overlay window reference |
| `_overlay_label` | tk.Label or None | Overlay label reference |
| `_calibration_grid_box` | tuple or dict | Grid box coordinates for calibration |
| `_calibration_preview_point` | tuple or dict | Preview point coordinates for calibration |
| `_calibration_progress` | dict | Calibration progress tracking with keys: total, current |

#### Drawing Options (Bitmask Flags)

| Flag | Value | Description |
|------|-------|-------------|
| `IGNORE_WHITE` | 1 << 0 | Skip drawing white pixels |
| `USE_CUSTOM_COLORS` | 1 << 1 | Use custom color spectrum |

#### Drawing Modes

| Constant | Value | Description |
|----------|-------|-------------|
| `SLOTTED` | 'slotted' | Simple color-to-lines mapping |
| `LAYERED` | 'layered' | Advanced color layering with frequency sorting (default) |

### Methods

#### Initialization Methods

##### `init_palette(pbox=None, prows=None, pcols=None, colors_pos=None, valid_positions=None, manual_centers=None)`

Initialize the palette configuration.

**Parameters:**
- `pbox` (tuple, optional): Palette box as (x1, y1, x2, y2) or (x, y, w, h)
- `prows` (int, optional): Number of rows in palette grid
- `pcols` (int, optional): Number of columns in palette grid
- `colors_pos` (dict, optional): Pre-computed color-to-position mapping
- `valid_positions` (set, optional): Set of valid palette cell indices
- `manual_centers` (dict, optional): Manual center point overrides {index: (x, y)}

**Returns:** `Palette` object

**Behavior:**
- Creates palette from screen capture using box coordinates
- Scans palette colors and creates RGB-to-position mapping
- Supports valid position filtering and manual center points

##### `init_canvas(cabox)`

Initialize the canvas configuration.

**Parameters:**
- `cabox` (tuple): Canvas box as (x1, y1, x2, y2)

**Returns:** None

**Behavior:**
- Stores canvas coordinates for drawing
- Coordinates define the drawing area

##### `init_custom_colors(ccbox)`

Initialize the custom colors spectrum configuration.

**Parameters:**
- `ccbox` (tuple): Custom colors box as (x1, y1, x2, y2)

**Returns:** None

**Behavior:**
- Stores custom colors spectrum coordinates
- Scans spectrum to create color-to-position map
- Enables unlimited color options

#### Drawing Methods

##### `draw(cmap)`

Draws an image using pre-processed color map.

**Parameters:**
- `cmap` (dict): Color map from process() method

**Returns:** 'success', 'terminated', or 'paused'

**Behavior:**
- Executes drawing with current settings
- Supports pause/resume functionality
- Can be interrupted with ESC
- Shows progress overlay with ETA
- Supports jump delay for large cursor movements
- Handles Color Button Okay mode
- Supports MSPaint Mode (double-click on palette/spectrum)

##### `test_draw(cmap, max_lines=20)`

Draws a test sample of the image.

**Parameters:**
- `cmap` (dict): Color map from process() method
- `max_lines` (int, optional): Maximum number of lines to draw (default: 20)

**Returns:** 'success' or 'terminated'

**Behavior:**
- Draws first N lines of the image
- Includes color switching
- Useful for testing brush size and settings

##### `simple_test_draw()`

Draws simple horizontal lines without color picking.

**Parameters:** None

**Returns:** 'success'

**Behavior:**
- Draws 5 horizontal lines at upper-left corner
- Each line is 1/4 of canvas width
- Uses currently selected color only
- Useful for testing brush size only

#### Processing Methods

##### `process(file, flags=0, mode=LAYERED)`

Processes an image into a color map for drawing.

**Parameters:**
- `file` (str): Path to image file
- `flags` (int, optional): Drawing feature flags (default: 0)
- `mode` (str, optional): Drawing mode 'slotted' or 'layered' (default: LAYERED)

**Returns:** Dictionary mapping colors to line segments

**Behavior:**
- Loads and processes image
- Converts pixels to draw commands
- Applies drawing mode (slotted or layered)
- Respects drawing flags (ignore white, use custom colors)

##### `process_region(file, region, flags=0, mode=LAYERED, canvas_target=None)`

Processes a specific region of an image for drawing.

**Parameters:**
- `file` (str): Path to image file
- `region` (tuple): Region bounds as (x1, y1, x2, y2) in image coordinates
- `flags` (int, optional): Drawing feature flags (default: 0)
- `mode` (str, optional): Drawing mode 'slotted' or 'layered' (default: LAYERED)
- `canvas_target` (tuple, optional): Target canvas area (x, y, w, h) (default: None)

**Returns:** Dictionary mapping colors to line segments for region

**Behavior:**
- Crops image to specified region
- Processes only region pixels
- Supports targeting specific canvas location

##### `precompute(image_path, flags=0, mode=LAYERED)`

Pre-computes image and caches results for faster subsequent draws.

**Parameters:**
- `image_path` (str): Path to image file
- `flags` (int, optional): Drawing feature flags (default: 0)
- `mode` (str, optional): Drawing mode 'slotted' or 'layered' (default: LAYERED)

**Returns:** Path to cache file

**Behavior:**
- Processes image based on current settings
- Caches results to disk
- Validates cache on subsequent loads (24 hour expiration)

##### `get_cached_status(image_path, flags=0, mode=LAYERED)`

Check if valid cached computation exists.

**Parameters:**
- `image_path` (str): Path to image file
- `flags` (int, optional): Drawing feature flags (default: 0)
- `mode` (str, optional): Drawing mode 'slotted' or 'layered' (default: LAYERED)

**Returns:** Tuple of (has_cache: bool, cache_file: str or None)

**Behavior:**
- Validates cache file exists
- Checks if settings match
- Verifies cache is not expired

##### `load_cached(cache_file)`

Load and validate cached computation results.

**Parameters:**
- `cache_file` (str): Path to cache file

**Returns:** Cache data dict or None if invalid

**Behavior:**
- Loads JSON cache file
- Validates settings match
- Checks cache age (< 24 hours)
- Validates canvas dimensions match

##### `get_cache_filename(image_path, flags=0, mode=LAYERED)`

Generate a unique cache filename based on image and settings.

**Parameters:**
- `image_path` (str): Path to image file
- `flags` (int, optional): Drawing feature flags (default: 0)
- `mode` (str, optional): Drawing mode 'slotted' or 'layered' (default: LAYERED)

**Returns:** Path to cache file or None if canvas not initialized

##### `estimate_drawing_time(cmap)`

Estimate how long drawing might take based on coordinate data.

**Parameters:**
- `cmap` (dict): Color map from process() method

**Returns:** Formatted time string (e.g., "~5 minutes")

**Behavior:**
- Calculates stroke count
- Estimates time per stroke
- Includes color switching overhead
- Includes jump delays
- Returns human-readable time estimate

#### Color Methods

**Note:** Color selection is handled inline in `draw()` and `test_draw()` methods.
- Palette color selection uses `Palette.nearest_color()` and direct mouse clicks
- Custom color selection uses `get_calibrated_color_position()` for position lookup
- No separate `pick_palette_color()` or `pick_custom_color()` methods exist

#### Calibration Methods

##### `calibrate_custom_colors(grid_box, preview_point, step=2)`

Runs color calibration by scanning the custom color spectrum.

**Parameters:**
- `grid_box` (tuple or dict): Grid box as [x1, y1, x2, y2] or dict with x, y, width, height
- `preview_point` (tuple or dict): Preview point as [x, y] or dict with x, y
- `step` (int, optional): Pixel step size for scanning (default: 2)

**Returns:** Dictionary mapping RGB tuples to (x, y) coordinates

**Behavior:**
- Presses mouse down at spectrum start
- Drags through entire spectrum step by step
- Captures RGB values at each step from preview spot
- Creates RGB to coordinate mapping
- Releases mouse up
- Can be cancelled with ESC key
- Shows progress with ETA

##### `save_color_calibration(filepath)`

Save the color calibration map to a JSON file.

**Parameters:**
- `filepath` (str): Path to the JSON file to save

**Returns:** True on success, False on failure

**Behavior:**
- Converts tuple keys to string format for JSON
- Saves calibration map to file
- Includes timestamp metadata

##### `load_color_calibration(filepath)`

Load color calibration data from a JSON file.

**Parameters:**
- `filepath` (str): Path to the JSON file to load

**Returns:** True on success, False on failure

**Behavior:**
- Loads JSON file
- Converts string keys back to tuples
- Loads calibration map into memory
- Prints loaded color count

##### `get_calibrated_color_position(target_rgb, tolerance=20, k_neighbors=4)`

Find the exact calibrated color position for a target RGB value.

**Parameters:**
- `target_rgb` (tuple): Target color as (r, g, b)
- `tolerance` (int, optional): Maximum color difference for exact match (default: 20)
- `k_neighbors` (int, optional): Number of nearest neighbors for interpolation (default: 4)

**Returns:** (x, y) coordinates or None if no calibration data

**Behavior:**
- First tries exact match within tolerance (Manhattan distance)
- Falls back to k-nearest neighbors with spatial interpolation
- Uses inverse distance weighting for position averaging
- Logs matching details for debugging

#### Progress Overlay Methods

##### `create_progress_overlay()`

Create and show an always-on-top progress overlay window.

**Parameters:** None

**Returns:** Overlay window object or None if disabled

**Behavior:**
- Creates transparent overlay window
- Shows stroke count and ETA
- Positioned at top center of screen
- Always on top during drawing

##### `update_progress_overlay(completed, total, eta_seconds)`

Update progress overlay with current progress and ETA.

**Parameters:**
- `completed` (int): Number of completed strokes
- `total` (int): Total number of strokes
- `eta_seconds` (float): Estimated remaining time in seconds

**Returns:** None

**Behavior:**
- Updates overlay text with progress
- Formats ETA time string
- Forces window update

##### `close_progress_overlay()`

Close progress overlay window and cleanup resources.

**Parameters:** None

**Returns:** None

**Behavior:**
- Destroys overlay window
- Clears overlay references
- Handles errors gracefully

#### Private Methods

**Note:** Most operations are implemented inline within public methods rather than as separate private helper methods. The Bot class focuses on direct automation logic using pyautogui and pynput libraries.

Key private attributes manage state (pause, terminate, drawing flags) and configuration data.

---

## Palette Class

Manages palette color information and nearest color matching.

### Constructor

```python
Palette(colors_pos=None, box=None, rows=None, columns=None, valid_positions=None, manual_centers=None)
```

**Parameters:**
- `colors_pos` (dict, optional): Pre-computed color-to-position mapping
- `box` (tuple, optional): Palette box coordinates
- `rows` (int, optional): Number of rows
- `columns` (int, optional): Number of columns
- `valid_positions` (set, optional): Set of valid cell indices
- `manual_centers` (dict, optional): Manual center point overrides

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `box` | tuple | Palette box coordinates |
| `rows` | int | Number of rows in palette |
| `columns` | int | Number of columns in palette |
| `colors_pos` | dict | RGB to (x, y) coordinate mappings |
| `colors` | set | Set of available colors |

### Methods

#### `nearest_color(query)`

Find the nearest color in the palette to the target color.

**Parameters:**
- `query` (tuple): Target RGB color (r, g, b)

**Returns:** Nearest RGB color tuple

**Behavior:**
- Uses squared Euclidean distance for performance
- Returns the color with minimum distance

#### `dist(colx, coly)`

Calculate squared Euclidean distance between two RGB colors.

**Parameters:**
- `colx` (tuple): First color (r, g, b)
- `coly` (tuple): Second color (r, g, b)

**Returns:** Squared distance value

**Note:** Returns squared distance to avoid expensive square root operation since relative order is preserved.

---

## Utility Functions

### `adjusted_img_size(img, ad)`

Recalculates image dimensions to fit within available space.

**Parameters:**
- `img` (PIL.Image): Source image
- `ad` (tuple): Available dimensions as (width, height)

**Returns:** Tuple of (adjusted_width, adjusted_height)

**Behavior:**
- Maintains aspect ratio
- Returns dimensions that fit within available space
- May result in dead space if aspect ratios don't match

---

## Exception Classes

### `NoToolError`

Base exception class for uninitialized tools. Raised when a required tool is not initialized or configured.

**Example:**
```python
raise NoToolError("Tool not initialized")
```

### `NoPaletteError`

Subclass of `NoToolError`. Raised specifically when palette is not initialized.

### `NoCanvasError`

Subclass of `NoToolError`. Raised specifically when canvas is not initialized.

### `NoCustomColorsError`

Subclass of `NoToolError`. Raised when custom colors are required but not initialized.

### `CorruptConfigError`

Subclass of `NoToolError`. Raised specifically when the configuration file is corrupted or invalid.

**Example:**
```python
raise CorruptConfigError("Configuration file is corrupted")
```

---

## UI Components

### Window Class

Main application window (`ui/window.py`).

#### Constructor

```python
Window(title, bot, w, h, x, y)
```

**Parameters:**
- `title` (str): Window title
- `bot` (Bot): Bot instance
- `w` (int): Window width
- `h` (int): Window height
- `x` (int): Screen x offset
- `y` (int): Screen y offset

**Note:** The window runs its mainloop immediately in `__init__`, so there is no separate `run()` method. Status updates are done via direct assignment to `self.tlabel['text']`.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `bot` | Bot | Bot instance for automation |
| `busy` | bool | Flag indicating if operations are in progress |
| `tools` | dict | Configuration data for all tools |
| `draw_options` | int | Drawing feature flags (bitmask) |
| `_initializing` | bool | Flag to prevent config saving during UI setup |
| `tlabel` | tk.Label | Status/tooltip label |
| `_imname` | str | Current image name/path |
| `_last_url` | str | Last loaded image URL |
| `_mode` | str | Current drawing mode |
| `_delay_var` | tk.StringVar | Delay input value |
| `_mspaint_delay_var` | tk.StringVar | MSPaint Mode delay value |
| `_calib_step_var` | tk.StringVar | Calibration step size value |
| `_jump_threshold_var` | tk.StringVar | Jump threshold value |
| `_redraw_region` | tuple or None | Selected redraw region (x1, y1, x2, y2) |
| `_redraw_picking` | bool | Flag for redraw region selection mode |

#### `is_free` Decorator

Decorator function at module scope that only executes a function when `self.busy` is False.

**Usage:**
```python
@is_free
def some_method(self):
    # This will only execute if not busy
    self.busy = True
    # ... do work ...
```

#### `__del__` Method

Cleans up cache directory on application exit.

**Behavior:**
- Removes `cache/` directory if it exists
- Ensures cleanup on program termination

#### Thread Management

The Window class manages several background threads for long-running operations:

| Thread Attribute | Thread Target | Description |
|------------------|----------------|-------------|
| `_draw_thread` | `self.start` | Main drawing operation |
| `_test_draw_thread_obj` | `self.test_draw` | Test drawing (limited lines) |
| `_simple_test_thread_obj` | `self.simple_test_draw` | Simple test (no color picking) |
| `_precompute_thread_obj` | `self.precompute` | Image pre-computation/caching |
| `_calibration_thread_obj` | `self._calibration_thread` | Color calibration |
| `_redraw_thread` | `self.redraw_region` | Region-based redrawing |

Each thread has a corresponding monitor method that updates the UI and manages thread lifecycle.

#### Key Public Methods

##### `setup()`

Opens the Setup window for tool configuration (decorated with `@is_free` to prevent concurrent operations).

##### `load_config()`

Loads configuration from `config.json` file.

##### `start()`

Initiates the full drawing operation by starting `_draw_thread`.

##### `test_draw()`

Performs a test drawing (method called by `_test_draw_thread_obj`).

##### `simple_test_draw()`

Performs a simple test drawing without color picking (method called by `_simple_test_thread_obj`).

##### `precompute()`

Pre-computes and caches image data (method called by `_precompute_thread_obj`).

##### `redraw_region()`

Redraws a selected region of the image (method called by `_redraw_thread`).

#### Thread Starter Methods

These methods start the corresponding background threads:

- `start_precompute_thread()`
- `start_test_draw_thread()`
- `start_simple_test_draw_thread()`
- `start_calibration_thread()`
- `start_draw_thread()`
- `start_redraw_draw_thread()` - Starts region redraw thread

#### Private Methods

- `_set_busy(val)` - Sets the busy flag for thread management
- `_canvas_to_image_region(canvas_region)` - Converts canvas coordinates to image coordinates for redraw
- `_capture_redraw_points()` - Captures mouse clicks for redraw region selection
- `_get_redraw_region_manual()` - Gets redraw region coordinates via manual input
- `_cancel_redraw_pick()` - Cancels redraw region selection
- `_create_calibration_overlay()` - Creates progress overlay for color calibration
- `_close_calibration_overlay()` - Closes calibration progress overlay
- `_calibration_thread()` - Executes color calibration process
- `_manage_calibration_thread()` - Manages calibration thread and updates progress
- `_manage_precompute_thread()` - Manages precompute thread progress
- `_manage_test_draw_thread()` - Manages test draw thread progress
- `_manage_simple_test_draw_thread()` - Manages simple test draw thread progress
- `_manage_draw_thread()` - Manages main draw thread progress
- `_manage_redraw_thread()` - Manages redraw thread progress
- `_init_tpanel()` - Initializes tooltip panel
- `_init_cpanel()` - Initializes control panel
- `_init_ipanel()` - Initializes image preview panel
- `_cpanel_cvs_config(event)` - Canvas configuration callback
- `_cpanel_frm_config(event)` - Frame configuration callback
- `_update_mode(selection)` - Updates drawing mode selection
- `_set_etext(e, txt)` - Sets entry text field value
- `_set_img(image=None, path=None)` - Sets preview image
- `_fetch_remote_image(url, timeout=10, retries=3)` - Fetches remote image with error handling
- `_on_complete_setup()` - Handles setup window completion

#### Event Handler Methods (Private)

Key event handlers use `_on_` prefix:

- `_on_redraw_pick()` - Handles region picking mode
- `_on_redraw_click()` - Handles region selection clicks
- `_on_delete_calibration()` - Handles calibration file deletion
- `_on_reset_config()` - Handles config file reset
- `_on_search_img()` - Handles image URL search
- `_on_open_file()` - Handles file open dialog
- `_on_check()` - Handles checkbox changes
- `_on_slider_move()` - Handles slider changes
- `_on_delay_entry_change()` - Handles delay entry changes
- `_on_newlayer_toggle()` - Handles New Layer checkbox toggle
- `_on_colorbutton_toggle()` - Handles Color Button checkbox toggle
- `_on_skip_first_color_toggle()` - Handles Skip First Color checkbox toggle
- `_on_mspaint_mode_toggle()` - Handles MSPaint Mode checkbox toggle
- `_on_mspaint_delay_change()` - Handles MSPaint Mode delay changes
- `_on_pause_key_entry_press()` - Handles pause key entry changes
- `_on_calib_step_change()` - Handles calibration step size changes
- `_on_jump_threshold_change()` - Handles jump threshold changes

### SetupWindow Class

Setup window for configuring tools (`ui/setup.py`).

#### Key Methods

##### `run()`

Opens and runs the setup configuration dialog.

**Returns:** None

### InteractivePaletteExtractor Class

Interactive palette extraction tool with anchor point placement and interpolation (`ui/setup.py`).

#### Constructor

```python
InteractivePaletteExtractor(parent, bot, current_tool, tool_name, valid_positions, palette_box, on_complete)
```

**Parameters:**
- `parent`: Parent window
- `bot` (Bot): Bot instance
- `current_tool` (dict): Current tool configuration
- `tool_name` (str): Name of tool being configured
- `valid_positions` (set): Set of valid palette cell indices
- `palette_box` (tuple): Palette box coordinates
- `on_complete` (callable): Callback function when complete

#### Key Methods

##### `_start_phase_1()`

Start phase 1: Region selection.

##### `_start_phase_2()`

Start phase 2: Grid configuration.

##### `_start_phase_3()`

Start phase 3: Anchor placement.

##### `_on_extract_colors()`

Extract colors and complete extraction.

---

## Configuration

### Configuration File Structure

Pyaint uses `config.json` for persistent configuration.

```json
{
  "drawing_settings": {
    "delay": 0.1,
    "pixel_size": 12,
    "precision": 0.9,
    "jump_delay": 0.5,
    "jump_threshold": 5
  },
  "drawing_options": {
    "ignore_white_pixels": false,
    "use_custom_colors": false
  },
  "pause_key": "p",
  "skip_first_color": false,
  "calibration_settings": {
    "step_size": 2
  },
  "Palette": {
    "status": true,
    "box": [x1, y1, x2, y2],
    "rows": 6,
    "cols": 8,
    "color_coords": {
      "(r,g,b)": [x, y]
    },
    "valid_positions": [0, 1, 2, ...],
    "manual_centers": {
      "0": [x, y]
    },
    "preview": "assets/Palette_preview.png"
  },
  "Canvas": {
    "status": true,
    "box": [x1, y1, x2, y2],
    "preview": "assets/Canvas_preview.png"
  },
  "Custom Colors": {
    "status": true,
    "box": [x1, y1, x2, y2],
    "preview": "assets/Custom Colors_preview.png"
  },
  "New Layer": {
    "status": true,
    "coords": [x, y],
    "enabled": false,
    "modifiers": {
      "ctrl": false,
      "alt": false,
      "shift": true
    }
  },
  "Color Button": {
    "status": true,
    "coords": [x, y],
    "enabled": false,
    "delay": 0.1,
    "modifiers": {
      "ctrl": false,
      "alt": false,
      "shift": false
    }
  },
  "Color Button Okay": {
    "status": true,
    "coords": [x, y],
    "enabled": false,
    "delay": 0.1,
    "modifiers": {
      "ctrl": false,
      "alt": false,
      "shift": false
    }
  },
  "MSPaint Mode": {
    "enabled": false,
    "delay": 0.5
  },
  "color_preview_spot": {
    "name": "Color Preview Spot",
    "button": null,
    "status": true,
    "coords": [x, y],
    "enabled": false,
    "modifiers": {
      "ctrl": false,
      "alt": false,
      "shift": false
    }
  },
  "last_image_url": "https://..."
}
```

### Configuration Loading

Configuration is loaded automatically from `config.json` on startup.

If the file is missing or invalid, default values are used.

### Configuration Saving

Configuration is saved automatically:
- After tool configuration completion
- After drawing setting changes
- After checkbox toggles

### Color Calibration File

Color calibration data is stored in `color_calibration.json`.

Structure:
```json
{
  "r,g,b": [x, y],
  ...
}
```

Each key is a string representation of an RGB tuple, value is the (x, y) coordinate.

---

## Main Entry Point

### `main.py`

The main entry point for the application.

**Behavior:**
1. Creates Bot instance
2. Sets up pynput keyboard listener for ESC and pause key
3. Launches main Window
4. Cleans up listener on exit

**Controls:**
- ESC: Terminates all operations
- pause_key: Toggles pause/resume during drawing

---

## Module Overview

### `bot.py`

Contains the `Bot` and `Palette` classes - the core drawing automation engine.

### `utils.py`

Utility functions for image processing.

### `exceptions.py`

Custom exception classes for error handling.

### `main.py`

Application entry point with keyboard control setup.

### `ui/window.py`

Main application window and UI.

### `ui/setup.py`

Setup window for tool configuration and interactive palette extraction.

---

## See Also

- [Architecture Documentation](./architecture.md) - System architecture details
- [Configuration Guide](./configuration.md) - Configuration options
- [Tutorial](./tutorial.md) - Step-by-step usage guide
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions