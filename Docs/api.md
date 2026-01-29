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

##### `init_palette(colors_pos=None, prows=None, pcols=None, pbox=None, valid_positions=None, manual_centers=None)`

Initialize the palette configuration.

**Parameters:**
- `colors_pos` (dict, optional): Pre-computed color-to-position mapping
- `prows` (int, optional): Number of rows in palette grid
- `pcols` (int, optional): Number of columns in palette grid
- `pbox` (tuple, optional): Palette box as (x1, y1, x2, y2) or (x, y, w, h)
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

##### `calibrate_custom_colors(grid_box: Any, preview_point: Any, step: int = 2) -> Dict[Tuple[int, int, int], Tuple[int, int]]`

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

##### `get_calibrated_color_position(target_rgb: Tuple[int, int, int], tolerance: int = 20, k_neighbors: int = 4) -> Optional[Tuple[int, int]]`

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

#### Canvas Calibration Methods

##### `calibrate_canvas(pattern_size=(50, 50))`

Calibrate canvas by drawing a checkerboard pattern and measuring dot spacing.

**Parameters:**
- `pattern_size` (tuple, optional): Checkerboard pattern dimensions as (width, height) (default: (50, 50))

**Returns:** None

**Behavior:**
- Draws a checkerboard pattern on the canvas
- Measures dot spacing to detect zoom level
- Adjusts pixel size based on measured spacing
- Can be cancelled with ESC key

##### `apply_canvas_calibration()`

Apply canvas calibration results to adjust pixel size.

**Parameters:** None

**Returns:** None

**Behavior:**
- Uses measured spacing to calculate adjusted pixel size
- Updates Bot settings with new pixel size

##### `save_canvas_calibration(filepath='canvas_calibration.json')`

Save canvas calibration data to a JSON file.

**Parameters:**
- `filepath` (str, optional): Path to save calibration data (default: 'canvas_calibration.json')

**Returns:** None

**Behavior:**
- Saves measured spacing and calculated pixel size
- Includes timestamp metadata

##### `load_canvas_calibration(filepath='canvas_calibration.json')`

Load canvas calibration data from a JSON file.

**Parameters:**
- `filepath` (str, optional): Path to load calibration data (default: 'canvas_calibration.json')

**Returns:** None

**Behavior:**
- Loads measured spacing and pixel size
- Applies calibration to Bot settings
- Prints loaded calibration details

#### Private Methods

**Note:** Most operations are implemented inline within public methods rather than as separate private helper methods. The Bot class focuses on direct automation logic using pyautogui and pynput libraries.

Key private attributes manage state (pause, terminate, drawing flags) and configuration data.

##### `_draw_checkerboard_pattern(canvas_x, canvas_y, canvas_w, canvas_h, pattern_size)`

Draw a checkerboard pattern for canvas calibration.

**Parameters:**
- `canvas_x` (int): Canvas left coordinate
- `canvas_y` (int): Canvas top coordinate
- `canvas_w` (int): Canvas width
- `canvas_h` (int): Canvas height
- `pattern_size` (tuple): Pattern dimensions as (width, height)

**Returns:** None

##### `_measure_drawn_pattern()`

Measure the drawn checkerboard pattern to determine dot spacing.

**Parameters:** None

**Returns:** Measured spacing between dots

##### `_estimate_drawing_time_seconds(cmap)`

Estimate drawing time in seconds (internal helper method).

**Parameters:**
- `cmap` (dict): Color map from process() method

**Returns:** Estimated time in seconds

##### `_format_time(seconds)`

Format seconds into human-readable time string.

**Parameters:**
- `seconds` (float): Time in seconds

**Returns:** Formatted time string (e.g., "5m 30s")

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

#### Constructor

```python
SetupWindow(parent, bot, tools, on_complete, title='Child Window', w=1600, h=900, x=5, y=5)
```

**Parameters:**
- `parent`: Parent window
- `bot` (Bot): Bot instance
- `tools` (dict): Configuration data for all tools
- `on_complete` (callable): Callback function when setup is complete
- `title` (str, optional): Window title (default: 'Child Window')
- `w` (int, optional): Window width (default: 1600)
- `h` (int, optional): Window height (default: 900)
- `x` (int, optional): Screen x offset (default: 5)
- `y` (int, optional): Screen y offset (default: 5)

#### Key Methods

##### `_init_tools_panel()`

Initialize the tools configuration panel.

##### `_init_preview_panel()`

Initialize the preview panel for tool visualization.

##### `_set_preview(name)`

Set the preview for a specific tool.

**Parameters:**
- `name` (str): Tool name

##### `_start_listening(name, tool)`

Start mouse listener for tool configuration.

**Parameters:**
- `name` (str): Tool name
- `tool` (dict): Tool configuration

##### `_start_manual_color_selection(name, tool)`

Start manual color selection for palette configuration.

**Parameters:**
- `name` (str): Tool name
- `tool` (dict): Tool configuration

##### `_open_color_selection_window()`

Open window for manually selecting valid palette colors.

##### `_draw_grid_with_indicators()`

Draw palette grid with selection indicators.

##### `_draw_grid_for_pick_centers()`

Draw palette grid for picking center points.

##### `_on_grid_canvas_click_pick_centers(event)`

Handle grid canvas click for picking center points.

##### `_on_grid_canvas_click(event)`

Handle grid canvas click for color selection.

##### `_toggle_grid_cell(index)`

Toggle selection state of a grid cell.

**Parameters:**
- `index` (int): Cell index

##### `_select_all_colors()`

Select all palette colors.

##### `_deselect_all_colors()`

Deselect all palette colors.

##### `_set_toggle_mode()`

Set toggle mode for color selection.

##### `_set_pick_centers_mode()`

Set pick centers mode for manual center point selection.

##### `_pick_center(index)`

Pick center point for a palette cell.

**Parameters:**
- `index` (int): Cell index

##### `_on_key_press(key)`

Handle keyboard press events.

##### `_auto_estimate_centers()`

Automatically estimate palette cell centers.

##### `_start_precision_estimate()`

Start precision estimation for center points.

##### `_on_extraction_complete(manual_centers)`

Handle completion of palette extraction.

**Parameters:**
- `manual_centers` (dict): Manual center points

##### `_show_centers_overlay()`

Show overlay with estimated center points.

##### `_show_custom_centers_overlay()`

Show overlay with custom center points.

##### `_on_escape_press(event)`

Handle ESC key press.

##### `_on_center_pick_click(x, y, _, pressed)`

Handle click for picking center points.

##### `_on_color_selection_done()`

Handle completion of manual color selection.

##### `_on_click(x, y, _, pressed)`

Handle mouse clicks for tool configuration.

##### `_on_update_dimensions(event)`

Handle dimension updates.

##### `_validate_delay(value)`

Validate delay input value.

**Parameters:**
- `value` (str): Delay value to validate

**Returns:** True if valid, False otherwise

##### `_on_update_delay(event)`

Update delay value for Color Button and validate on focus out or return.

##### `_on_enable_toggle(tool_name, intvar)`

Handle enable toggle for a tool.

**Parameters:**
- `tool_name` (str): Tool name
- `intvar`: IntVar for toggle state

##### `_on_update_delay_okay(event, tool_name)`

Update delay value for Color Button Okay and validate on focus out or return.

**Parameters:**
- `event`: Event object
- `tool_name` (str): Tool name

##### `_on_modifier_toggle(tool_name, modifier_name, intvar)`

Handle modifier key toggle for a tool.

**Parameters:**
- `tool_name` (str): Tool name
- `modifier_name` (str): Modifier key name
- `intvar`: IntVar for toggle state

##### `_start_canvas_calibration(name, tool)`

Start canvas calibration process.

**Parameters:**
- `name` (str): Tool name
- `tool` (dict): Tool configuration

##### `_execute_calibration_wrapper()`

Execute calibration wrapper for thread management.

##### `_run_canvas_calibration(name, tool, canvas_x, canvas_y, canvas_w, canvas_h)`

Run canvas calibration process.

**Parameters:**
- `name` (str): Tool name
- `tool` (dict): Tool configuration
- `canvas_x` (int): Canvas left coordinate
- `canvas_y` (int): Canvas top coordinate
- `canvas_w` (int): Canvas width
- `canvas_h` (int): Canvas height

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

##### `_setup_ui()`

Set up the user interface for palette extraction.

##### `_update_controls()`

Update UI controls based on current phase.

##### `_start_phase_1()`

Start phase 1: Region selection.

##### `_on_region_click(x, y, button, pressed)`

Handle region selection click.

**Parameters:**
- `x` (int): X coordinate
- `y` (int): Y coordinate
- `button`: Button identifier
- `pressed` (bool): Whether button was pressed

##### `_capture_palette()`

Capture palette image from selected region.

##### `_start_phase_2()`

Start phase 2: Grid configuration.

##### `_on_set_grid()`

Handle grid dimension input.

##### `_start_phase_3()`

Start phase 3: Anchor placement.

##### `_draw_palette_with_grid()`

Draw palette with grid overlay.

##### `_on_canvas_click(event)`

Handle canvas click for anchor placement.

##### `_get_required_anchors()`

Get required anchor points for interpolation.

**Returns:** List of required anchor indices

##### `_get_corner_indices()`

Get corner indices of the palette grid.

**Returns:** List of corner indices

##### `_recalculate_interpolation()`

Recalculate color interpolation based on anchor points.

##### `_clear_anchors()`

Clear all placed anchor points.

##### `_back_to_phase_2()`

Return to phase 2 (grid configuration).

##### `_back_to_phase_1()`

Return to phase 1 (region selection).

##### `_on_extract_colors()`

Extract colors and complete extraction.

##### `_save_temp()`

Save current state to temp file.

##### `_try_restore()`

Try to restore state from temp file.

##### `_on_close()`

Handle window close event.

### PaletteWindow Class

Color palette generation window for analyzing images and extracting color palettes (`ui/palette_window.py`).

#### Constructor

```python
PaletteWindow(parent: tk.Tk, image_path: str, bot)
```

**Parameters:**
- `parent`: Parent Tkinter window
- `image_path` (str): Path to image file
- `bot` (Bot): Bot instance

#### Key Methods

##### `_init_ui()`

Initialize the user interface.

##### `_update_palette_preview()`

Update palette preview based on current size and algorithm.

##### `_draw_color_swatches()`

Draw color swatches on the canvas.

##### `_update_info()`

Update information display.

##### `_resolve_ties_dialog()`

Open dialog to resolve color ties.

##### `_export_palette()`

Export palette to GIMP CSS format.

---

## CanvasCalibrator Class

Canvas calibration using cross-pattern dot measurement (`canvas_calibration.py`).

#### Constructor

```python
CanvasCalibrator(canvas_coords)
```

**Parameters:**
- `canvas_coords` (tuple): Canvas coordinates (x, y, width, height)

#### Key Methods

##### `dot_size_from_screenshot(center_x: int, center_y: int) -> Optional[Tuple[int, int]]`

Measure dot size from screenshot at given center position.

**Parameters:**
- `center_x` (int): Center X coordinate
- `center_y` (int): Center Y coordinate

**Returns:** Tuple of (width, height) or None if measurement fails

##### `measure_spacing(center_pos: Tuple[int, int], intended_spacing: int = 10) -> Tuple[int, int]`

Measure spacing between dots in a cross pattern.

**Parameters:**
- `center_pos` (tuple): Center position as (x, y)
- `intended_spacing` (int, optional): Intended spacing between dots (default: 10)

**Returns:** Tuple of (horizontal_spacing, vertical_spacing)

---

## run_calibration Function

Run complete canvas calibration process (`canvas_calibration.py`).

```python
run_calibration(canvas_coords: tuple, intended_spacing: int = 10, pattern_size: tuple = (50, 50)) -> dict
```

**Parameters:**
- `canvas_coords` (tuple): Canvas coordinates (x, y, width, height)
- `intended_spacing` (int, optional): Intended spacing between dots (default: 10)
- `pattern_size` (tuple, optional): Checkerboard pattern dimensions (default: (50, 50))

**Returns:** Dictionary with measured spacing and calculated pixel size

---

## ColorPaletteGenerator Class

Generates color palettes from images with multiple selection algorithms (`palette_generator.py`).

#### Constructor

```python
ColorPaletteGenerator(image_path: str, ignore_white: bool = True)
```

**Parameters:**
- `image_path` (str): Path to image file
- `ignore_white` (bool, optional): Whether to ignore white pixels (default: True)

#### Key Methods

##### `analyze_image() -> None`

Analyze the image and count color frequencies.

##### `rgb_to_hsv(rgb: Tuple[int, int, int]) -> Optional[Tuple[float, float, float]]`

Convert RGB color to HSV color space.

**Parameters:**
- `rgb` (tuple): RGB color as (r, g, b)

**Returns:** HSV color as (h, s, v) or None if conversion fails

##### `group_colors_by_hue(num_bins: int = 16) -> Dict[int, List[Tuple[Tuple[int, int, int], int]]]`

Group colors by hue bins.

**Parameters:**
- `num_bins` (int, optional): Number of hue bins (default: 16)

**Returns:** Dictionary mapping hue bins to color lists

##### `get_palette(num_colors: int, algorithm: str = "frequency", progress_callback=None) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]`

Get color palette using specified algorithm.

**Parameters:**
- `num_colors` (int): Number of colors to extract
- `algorithm` (str): Algorithm name - "frequency", "dominant_shades", "rare_shades", or "kmeans"
- `progress_callback` (callable, optional): Callback for progress updates

**Returns:** Tuple of (colors list, frequencies list, color percentage dict)

##### `_get_by_frequency(num_colors: int) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]`

Get palette by color frequency.

##### `_get_by_dominant_shades(num_colors: int) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]`

Get palette by dominant shades.

##### `_get_by_rare_shades(num_colors: int) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]`

Get palette by rare shades.

##### `_get_by_kmeans(num_colors: int) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]`

Get palette using K-Means clustering algorithm.

##### `find_ties(num_colors: int) -> Dict[int, List[Tuple[int, int, int]]]`

Find color ties at boundary positions.

**Parameters:**
- `num_colors` (int): Number of colors

**Returns:** Dictionary mapping boundary indices to tied colors

##### `get_color_percentage(count: int) -> float`

Calculate color percentage in image.

**Parameters:**
- `count` (int): Color count

**Returns:** Percentage value

##### `export_gimp_css(colors: List[Tuple[int, int, int]], output_path: str) -> None`

Export palette to GIMP CSS format.

**Parameters:**
- `colors` (list): List of RGB colors
- `output_path` (str): Output file path

##### `_kmeans_plus_plus_init(data: List[Tuple[int, int, int]], k: int) -> List[Tuple[float, float, float]]`

Initialize K-Means centroids using K-Means++ algorithm.

##### `_find_nearest_centroid(color: Tuple[int, int, int], centroids: List[Tuple[float, float, float]]) -> int`

Find nearest centroid for a color.

##### `_color_distance(color1: Tuple[int, int, int], color2: Tuple[float, float, float]) -> float`

Calculate color distance.

##### `_calculate_weighted_average(colors: List[Tuple[int, int, int]]) -> Tuple[float, float, float]`

Calculate weighted average of colors.

##### `_centroids_converged(old: List[Tuple[float, float, float]], new: List[Tuple[float, float, float]], threshold: float = 0.1) -> bool`

Check if centroids have converged.

##### `_count_colors_for_centroid(centroid_idx: int) -> int`

Count colors assigned to a centroid.

##### `_get_current_centroids() -> List[Tuple[float, float, float]]`

Get current centroids.

##### `get_color_stats() -> List[Dict]`

Get color statistics.

**Returns:** List of color statistics dictionaries

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

### `ui/palette_window.py`

Color palette generation window for analyzing images and extracting color palettes.

### `palette_generator.py`

Color palette generator module with multiple selection algorithms (frequency, dominant shades, rare shades, K-Means).

### `canvas_calibration.py`

Canvas calibration module using cross-pattern dot measurement to detect zoom level and adjust pixel size.

---

## See Also

- [Architecture Documentation](./architecture.md) - System architecture details
- [Configuration Guide](./configuration.md) - Configuration options
- [Tutorial](./tutorial.md) - Step-by-step usage guide
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions
- [Usage Guide](./usage-guide.md) - User guide for drawing operations