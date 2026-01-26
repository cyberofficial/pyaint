# Pyaint Architecture

System architecture and design documentation for Pyaint.

## Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Drawing Pipeline](#drawing-pipeline)
- [Color System](#color-system)
- [Progress Overlay System](#progress-overlay-system)
- [Calibration System](#calibration-system)
- [Threading Model](#threading-model)
- [Configuration Management](#configuration-management)
- [UI Architecture](#ui-architecture)
- [Control Flow](#control-flow)

---

## Overview

Pyaint is a drawing automation tool that converts images into precise mouse movements for painting applications. The system is built with a modular architecture that separates concerns between drawing logic, user interface, and configuration management.

### Core Principles

1. **Separation of Concerns**: Drawing logic, UI, and configuration are independent
2. **Automation-First**: Automated mouse/keyboard control through pynput and pyautogui
3. **Configurability**: All behaviors configurable via JSON
4. **Extensibility**: Modular design allows easy feature additions

### Technology Stack

- **Python**: Primary language (3.8+)
- **Pillow (PIL)**: Image processing
- **PyAutoGUI**: Mouse and keyboard automation
- **Pynput**: Global keyboard event handling
- **Tkinter**: GUI framework
- **Threading**: Concurrent operations for long-running tasks
- **JSON**: Configuration and cache storage

---

## System Components

### Module Structure

```
pyaint/
├── main.py              # Application entry point
├── bot.py               # Core drawing automation engine
├── utils.py             # Utility functions
├── exceptions.py        # Custom exception classes
├── ui/
│   ├── __init__.py
│   ├── window.py        # Main application window
│   └── setup.py         # Setup/configuration window
├── assets/              # Preview images and assets
├── cache/               # Pre-computed image cache
├── config.json          # Persistent configuration
└── color_calibration.json  # Color calibration data
```

### Component Responsibilities

#### `main.py`

**Purpose**: Application entry point and keyboard control setup

**Responsibilities**:
- Initialize Bot instance
- Set up pynput keyboard listener for global hotkeys
- Handle ESC key for termination
- Handle pause_key for pause/resume
- Launch main Window
- Clean up on exit

**Key Features**:
- Non-blocking keyboard listener
- ESC terminates all operations
- Configurable pause/resume key (default: 'p')

#### `bot.py`

**Purpose**: Core drawing automation engine

**Responsibilities**:
- Image processing and analysis
- Color matching and selection
- Mouse movement and click automation
- Drawing execution (full, test, simple test, region)
- Pause/resume handling with state preservation
- Color calibration with advanced interpolation
- Progress overlay management
- Pre-computation caching
- Jump delay detection and application

**Key Classes**:
- `Bot`: Main automation class
- `Palette`: Palette color management

**Key Constants**:
- `Bot.DELAY`, `Bot.STEP`, `Bot.ACCURACY`, `Bot.JUMP_DELAY`: Settings indices
- `Bot.SLOTTED`, `Bot.LAYERED`: Drawing mode constants
- `Bot.IGNORE_WHITE`, `Bot.USE_CUSTOM_COLORS`: Option flags

**Key Methods**:
- `draw(cmap)`: Full image drawing with progress overlay
- `test_draw(cmap, max_lines=20)`: Test sample drawing
- `simple_test_draw()`: Simple line test
- `process(file, flags=0, mode=LAYERED)`: Image to color map conversion
- `process_region(file, region, flags=0, mode=LAYERED, canvas_target=None)`: Region-based processing
- `precompute(image_path, flags=0, mode=LAYERED)`: Image preprocessing and caching
- `calibrate_custom_colors(grid_box, preview_point, step=2)`: Color spectrum calibration
- `get_calibrated_color_position(target_rgb, tolerance=20, k_neighbors=4)`: Advanced color lookup with interpolation
- `create_progress_overlay()`: Create progress display window
- `update_progress_overlay(completed, total, eta_seconds)`: Update progress in real-time
- `close_progress_overlay()`: Clean up progress window
- `get_cached_status(image_path, flags=0, mode=LAYERED)`: Check cache validity
- `load_cached(cache_file)`: Load cached computation
- `get_cache_filename(image_path, flags=0, mode=LAYERED)`: Generate cache filename
- `estimate_drawing_time(cmap)`: Calculate drawing time estimate
- `_estimate_drawing_time_seconds(cmap)`: Internal helper for time calculation

#### `utils.py`

**Purpose**: Utility functions for image processing

**Responsibilities**:
- Image dimension calculations
- Aspect ratio handling

**Key Functions**:
- `adjusted_img_size(img, ad)`: Calculate dimensions to fit space

#### `exceptions.py`

**Purpose**: Custom exception classes

**Responsibilities**:
- Define error hierarchy
- Provide specific error types

**Exception Classes**:
- `NoToolError`: Base exception for uninitialized tools
- `CorruptConfigError`: Configuration file corruption or invalid format
- `NoPaletteError`: Palette not initialized (subclass of NoToolError)
- `NoCanvasError`: Canvas not initialized (subclass of NoToolError)
- `NoCustomColorsError`: Custom colors not initialized (subclass of NoToolError)

#### `ui/window.py`

**Purpose**: Main application UI

**Responsibilities**:
- Display main interface
- Handle user input
- Coordinate with Bot instance
- Display status and progress
- Manage drawing threads
- Handle configuration loading/saving
- Region redraw functionality
- File management (remove calibration, reset config)

**Key Classes**:
- `Window`: Main application window

**Key Methods**:
- `__init__(title, bot, w, h, x, y)`: Initialize and run main application
- `setup()`: Open setup configuration dialog
- `start_precompute_thread()`: Start pre-computation in background thread
- `precompute()`: Execute pre-computation
- `start_test_draw_thread()`: Start test draw in background thread
- `test_draw()`: Execute test draw
- `start_simple_test_draw_thread()`: Start simple test draw in background thread
- `simple_test_draw()`: Execute simple test draw
- `start_calibration_thread()`: Start calibration in background thread
- `_calibration_thread()`: Execute calibration
- `_redraw_draw_thread()`: Start redraw in background thread
- `redraw_region()`: Execute region redraw
- `_on_redraw_pick()`: Enter region picking mode
- `start()`: Start full drawing operation
- `_on_delete_calibration()`: Remove color calibration file
- `_on_reset_config()`: Reset configuration to defaults
- `_set_img(image=None, path=None)`: Load and display image
- `update_preview()`: Update image preview (via `_set_img`)
- `save_config()`: Save current configuration (via `tools` dict)
- `load_config()`: Load configuration from file
- `start_draw_thread()`: Start drawing in background thread
- `_on_check(index, option)`: Handle drawing option checkbox toggle
- `_on_newlayer_toggle()`: Handle new layer checkbox toggle
- `_on_colorbutton_toggle()`: Handle color button checkbox toggle
- `_on_skip_first_color_toggle()`: Handle skip first color checkbox toggle
- `_on_mspaint_mode_toggle()`: Handle MSPaint mode checkbox toggle
- `_on_delay_entry_change(event=None)`: Handle delay setting changes
- `_on_slider_move(index, val)`: Handle slider changes
- `_on_jump_threshold_change(event=None)`: Handle jump threshold changes
- `_on_calib_step_change(event=None)`: Handle calibration step changes
- `_on_pause_key_entry_press(event)`: Handle pause key changes
- `_draw_thread`: Drawing thread (method target)
- `_test_draw_thread`: Test draw thread (Thread object)
- `_simple_test_thread_obj`: Simple test thread (Thread object)
- `_precompute_thread_obj`: Pre-compute thread (Thread object)
- `_calibration_thread_obj`: Calibration thread (Thread object)
- `_redraw_thread`: Redraw region thread (Thread object)
- `_manage_draw_thread()`: Monitor draw thread progress
- `_manage_test_draw_thread()`: Monitor test draw thread progress
- `_manage_simple_test_draw_thread()`: Monitor simple test thread progress
- `_manage_precompute_thread()`: Monitor pre-compute thread progress
- `_manage_calibration_thread()`: Monitor calibration thread progress
- `_manage_redraw_thread()`: Monitor redraw thread progress

**Key Features**:
- Control panel for settings
- Preview panel for images
- Tooltip panel for status
- Real-time progress tracking
- Thread management for long operations
- Redraw region functionality
- File management buttons
- MSPaint Mode support
- Color Button Okay support
- Color calibration overlay positioning above custom colors box

#### `ui/setup.py`

**Purpose**: Tool configuration interface

**Responsibilities**:
- Configure palette, canvas, custom colors
- Configure optional tools (New Layer, Color Button, Color Button Okay, MSPaint Mode)
- Capture screen regions
- Manage tool state
- Interactive palette extraction with anchor points

**Key Classes**:
- `SetupWindow`: Setup configuration window
- `InteractivePaletteExtractor`: Advanced palette center estimation with anchor point interpolation

**SetupWindow Key Methods**:
- `__init__(parent, bot, tools, on_complete, title='Child Window', w=1600, h=900, x=5, y=5)`: Initialize setup window
- `_start_listening(name, tool)`: Start mouse click listener for region capture
- `_start_manual_color_selection(name, tool)`: Start manual color selection for palette
- `_set_preview(name)`: Show tool preview image
- `_on_click(x, y, _, pressed)`: Handle mouse clicks for region capture
- `_validate_dimensions(value)`: Validate rows/cols input
- `_on_invalid_dimensions()`: Handle invalid dimensions input
- `_on_update_dimensions(event)`: Update dimensions on focus out/return
- `_validate_delay(value)`: Validate delay input (0.01-5.0)
- `_on_invalid_delay()`: Handle invalid delay input
- `_on_update_delay(event)`: Update Color Button delay
- `_on_update_delay_okay(event, tool_name)`: Update Color Button Okay delay
- `_on_enable_toggle(tool_name, intvar)`: Handle enable toggle for tools
- `_on_modifier_toggle(tool_name, modifier_name, intvar)`: Handle modifier key toggles
- `close()`: Close setup window and call completion callback
- `_open_color_selection_window()`: Open manual color selection UI
- `_draw_grid_with_indicators()`: Draw palette grid with valid/invalid indicators
- `_on_grid_canvas_click(event)`: Handle click on grid to toggle valid/invalid
- `_toggle_grid_cell(index)`: Toggle grid cell validity
- `_select_all_colors()`: Mark all colors as valid
- `_deselect_all_colors()`: Deselect all colors
- `_set_toggle_mode()`: Set mode to toggle valid/invalid cells
- `_set_pick_centers_mode()`: Set mode to pick exact center points
- `_pick_center(index)`: Pick center point for specific color cell
- `_auto_estimate_centers()`: Auto-estimate all color centers
- `_show_centers_overlay()`: Show overlay of estimated centers
- `_show_custom_centers_overlay()`: Show overlay of custom centers
- `_start_precision_estimate()`: Start interactive palette extraction
- `_on_extraction_complete(manual_centers)`: Handle palette extraction completion
- `_on_color_selection_done()`: Save manual color selection results
- `_on_center_pick_click(x, y, _, pressed)`: Handle click for center picking
- `_on_key_press(key)`: Handle keyboard events (ESC)
- `_on_escape_press(event)`: Handle ESC to cancel picking

**InteractivePaletteExtractor Key Methods**:
- `__init__(parent, bot, current_tool, tool_name, valid_positions, palette_box, on_complete)`: Initialize extractor
- `_setup_ui()`: Setup main UI layout
- `_update_controls()`: Update control buttons based on current phase
- `_start_phase_1()`: Start phase 1: Region selection
- `_on_region_click(x, y, button, pressed)`: Handle region selection in phase 1
- `_capture_palette()`: Capture palette image from selected region
- `_start_phase_2()`: Start phase 2: Grid configuration
- `_on_set_grid()`: Handle grid dimension input
- `_start_phase_3()`: Start phase 3: Anchor placement
- `_draw_palette_with_grid()`: Draw palette with grid overlay
- `_on_canvas_click(event)`: Handle click for anchor placement
- `_get_required_anchors()`: Get minimum number of required anchors based on grid
- `_get_corner_indices()`: Get indices of corner positions based on grid
- `_recalculate_interpolation()`: Recalculate interpolated positions from anchors
- `_clear_anchors()`: Clear all anchor points
- `_back_to_phase_2()`: Go back to grid configuration
- `_back_to_phase_1()`: Go back to region selection
- `_on_extract_colors()`: Extract colors and complete extraction
- `_save_temp()`: Save current state to temp file
- `_try_restore()`: Try to restore state from temp file
- `_on_close()`: Handle window close

**Key Features**:
- Manual color selection with valid/invalid toggling
- Precision estimate for automatic center calculation via InteractivePaletteExtractor
- Pick centers mode for manual center placement
- Auto-estimate centers with overlay visualization
- Custom centers overlay display
- Modifier key support (ctrl, alt, shift)
- Three-phase interactive palette extraction:
  - Phase 1: Select palette region
  - Phase 2: Configure grid (rows, cols)
  - Phase 3: Place anchor points for interpolation
- Anchor point interpolation for accurate center estimation
- State persistence to temp file for session restoration

---

## Data Flow

### Application Startup Flow

```
main.py
  │
  ├─> Create Bot instance (no parameters)
  │
  ├─> Setup pynput keyboard listener
  │     ├─> ESC key → set bot.terminate = True
  │     └─> pause_key → toggle bot.paused
  │
  └─> Launch Window (main UI)
        │
        └─> Load config.json
              ├─> Parse drawing_settings
              │     ├─> delay
              │     ├─> pixel_size
              │     ├─> precision
              │     ├─> jump_delay
              │     └─> jump_threshold
              ├─> Parse drawing_options
              │     ├─> ignore_white_pixels
              │     └─> use_custom_colors
              ├─> Parse tool configurations
              │     ├─> Palette (with manual_centers)
              │     ├─> Canvas
              │     ├─> Custom Colors
              │     ├─> New Layer
              │     ├─> Color Button
              │     ├─> Color Button Okay
              │     ├─> MSPaint Mode
              │     └─> color_preview_spot
              ├─> Parse pause_key
              ├─> Parse skip_first_color
              ├─> Parse calibration_settings
              │     └─> step_size
              └─> Apply to Bot instance
```

### Drawing Flow

```
User Action (Click "Start")
  │
  ├─> Validate prerequisites
  │     ├─> Check palette initialized
  │     ├─> Check canvas initialized
  │     └─> Check image loaded
  │
  ├─> Check for cached computation
  │     ├─> Cache valid?
  │     │     ├─> Yes: Load from cache
  │     │     └─> No: Process image
  │     │           ├─> Load PIL Image
  │     │           ├─> Apply drawing mode (slotted/layered)
  │     │           └─> Generate color map
  │     │
  │     └─> Estimate drawing time
  │
  ├─> Create progress overlay (positioned at top center of screen)
  │
  ├─> Execute drawing (in thread)
  │     ├─> For each color in color map:
  │     │     ├─> Check skip_first_color (skip if enabled and first color)
  │     │     ├─> Click New Layer button (if enabled)
  │     │     │     └─> Press modifiers (ctrl/alt/shift)
  │     │     ├─> Click Color Button (if enabled)
  │     │     │     └─> Press modifiers (ctrl/alt/shift)
  │     │     ├─> Select color:
  │     │     │     ├─> Check Color Button Okay
  │     │     │     │     ├─> Enabled: Select in spectrum only
  │     │     │     │     └─> Not enabled: Select in spectrum or palette
  │     │     │     ├─> Try calibration map first
  │     │     │     │     ├─> Exact match (within tolerance)
  │     │     │     │     └─> K-nearest neighbors interpolation
  │     │     │     ├─> MSPaint Mode: Double-click
  │     │     │     └─> Normal Mode: Single-click
  │     │     ├─> Click Color Button Okay (if enabled)
  │     │     │     └─> Press modifiers (ctrl/alt/shift)
  │     │     └─> For each line segment:
  │     │           ├─> Check terminate flag (ESC pressed)
  │     │           │     └─> If set: Stop drawing
  │     │           ├─> Check paused flag (pause_key pressed)
  │     │           │     └─> If set: Wait for resume
  │     │           ├─> Check jump distance
  │     │           │     └─> If > jump_threshold: Apply jump_delay
  │     │           ├─> Move mouse to position
  │     │           ├─> Click and drag (delay seconds)
  │     │           ├─> Update progress overlay
  │     │           └─> Update ETA
  │     │
  │     └─> Close progress overlay
  │
  └─> Show results (time comparison)
```

### Region Redraw Flow

```
User Action (Click "Pick Region")
  │
  ├─> Enter picking mode
  │
  ├─> Wait for two mouse clicks
  │     ├─> First click: Upper-left corner
  │     └─> Second click: Lower-right corner
  │
  ├─> Store region coordinates
  │
  └─> Display region info

User Action (Click "Draw Region")
  │
  ├─> Convert canvas region to image region
  │
  ├─> Process only selected region
  │
  ├─> Draw at target canvas location
  │
  └─> Show results
```

### Calibration Flow

```
User Action (Click "Run Calibration")
  │
  ├─> Validate prerequisites
  │     ├─> Custom Colors configured?
  │     └─> Color Preview Spot configured?
  │
  ├─> Create calibration progress overlay (positioned above custom colors box)
  │
  ├─> Minimize main window
  │
  ├─> Execute calibration (in thread)
  │     ├─> Press mouse down at spectrum start
  │     ├─> For each position in spectrum:
  │     │     ├─> Move to position
  │     │     ├─> Capture RGB from preview spot
  │     │     ├─> Store mapping: RGB → (x, y)
  │     │     ├─> Update progress overlay
  │     │     ├─> Check termination (ESC)
  │     │     └─> Calculate ETA
  │     ├─> Release mouse up
  │     └─> Save to color_calibration.json
  │
  └─> Restore main window
```

---

## Drawing Pipeline

### Processing Modes

#### Slotted Mode

**Purpose**: Simple color-to-lines mapping

**Process**:
1. Group pixels by color
2. Create line segments for each color
3. Draw all segments of color A, then color B, etc.

**Advantages**:
- Faster processing
- Less memory usage
- Simpler implementation

**Best For**: Simple images with few colors

#### Layered Mode (Default)

**Purpose**: Advanced color layering with frequency sorting

**Process**:
1. Group pixels by color
2. Sort colors by frequency (most common first)
3. Create line segments
4. Merge segments to reduce strokes
5. Draw in frequency order

**Advantages**:
- Better visual results
- Fewer color switches
- Optimized for complex images

**Best For**: Complex images with many colors

### Drawing Execution

```
For each color in sorted order:
  ├─> Check skip_first_color (skip if enabled and first color)
  │
  ├─> Click New Layer button (if enabled)
  │     └─> Press modifiers (ctrl/alt/shift) before click
  │     └─> Release modifiers after click
  │
  ├─> Click Color Button (if enabled)
  │     └─> Press modifiers (ctrl/alt/shift) before click
  │     └─> Release modifiers after click
  │     └─> Wait configured delay
  │
  ├─> Select color:
  │     ├─> If Color Button Okay enabled:
  │     │     └─> Select color in spectrum only
  │     │           └─> Do NOT click palette
  │     │           └─> Use calibration or spectrum scanning
  │     └─> Else (normal mode):
  │           ├─> Try palette first
  │           │     └─> MSPaint Mode: Double-click
  │           │     └─- Normal Mode: Single-click
  │           └─> Try custom colors (if enabled)
  │                 ├─> Use calibration map if available
  │                 │     ├─> Exact match (Manhattan distance, tolerance=20)
  │                 │     └─> K-nearest neighbors interpolation (4 neighbors)
  │                 │           └─> Inverse distance weighting
  │                 └─> Fallback to spectrum scanning
  │
  ├─> Click Color Button Okay (if enabled)
  │     └─> Press modifiers (ctrl/alt/shift) before click
  │     └─> Release modifiers after click
  │     └─> Wait configured delay
  │
  └─> For each line segment of this color:
        ├─> Check terminate flag (ESC)
        ├─> Check paused flag (pause_key)
        ├─> Calculate movement
        ├─> Check jump distance
        │     ├─> If > jump_threshold: Apply jump_delay
        │     └─> Else: No delay
        ├─> Move mouse to position
        ├─> Click and drag (delay seconds)
        ├─> Update progress overlay
        └─> Update ETA calculation
```

### Pause/Resume Mechanism

**Pause State**:
- `bot.paused` flag set to True
- Drawing loop checks flag at each iteration
- State preserved (current position, color, line index)
- Can pause between colors or between lines
- Modifier keys released during pause

**Resume State**:
- `bot.paused` flag set to False
- Replays current stroke to ensure clean result
- Continues from exact interruption point
- No re-initialization needed

**Draw State Tracking**:
- `color_idx`: Current color index
- `line_idx`: Current line index within color
- `segment_idx`: Current segment within line (for mid-stroke pause)
- `current_color`: Currently selected color
- `was_paused`: Flag to trigger stroke replay

---

## Color System

### Color Sources

#### Palette Colors

**Source**: Predefined color palette in drawing application

**Configuration**:
- Grid-based layout (rows x columns)
- Clickable color cells
- Valid/invalid positions (can exclude colors)
- Manual center points (override automatic calculation)
- Manual color selection UI with canvas-based grid display

**Selection Process**:
1. Check if color is in valid positions
2. If manual center exists: Use manual center
3. Else: Calculate automatic center of grid cell
4. Clamp coordinates to valid range
5. Get RGB color at center
6. Click on palette cell
7. MSPaint Mode: Double-click with delay
8. Normal Mode: Single-click

**Interactive Color Selection UI**:
- Toggle valid/invalid cells via canvas grid
- Pick centers mode for manual center placement
- Auto-estimate centers with overlay visualization
- Precision estimate via InteractivePaletteExtractor
- Select all / Deselect all buttons
- Show custom centers overlay
- Canvas-based grid display with palette image background
- Color indicator dots (green=valid, red=invalid)

#### Custom Colors

**Source**: Custom color spectrum in drawing application

**Configuration**:
- Continuous spectrum area
- Color-to-position mapping
- Calibration data (optional)
- Color preview spot for calibration

**Selection Process**:
1. Try calibration map first (if exists)
   - Exact match within tolerance (Manhattan distance)
   - K-nearest neighbors interpolation (4 neighbors)
   - Inverse distance weighting for position averaging
2. If no calibration: Scan spectrum for nearest color
3. Click on spectrum position
4. MSPaint Mode: Double-click with delay
5. Normal Mode: Single-click
6. Fallback to keyboard input (tab + RGB values)

### Color Matching Algorithm

#### Palette Matching

```python
def find_nearest_palette_color(target_rgb, palette):
    min_distance = infinity
    nearest_color = None
    
    for color in palette.colors:
        # Skip invalid positions
        if color not in valid_positions:
            continue
        
        # Calculate squared Euclidean distance in RGB space
        distance = Palette.dist(color, target_rgb)
        
        if distance < min_distance:
            min_distance = distance
            nearest_color = color
    
    return nearest_color
```

#### Custom Color Matching (Advanced Calibration)

**Exact Match (Manhattan Distance)**:
```python
for color, pos in calibration_map:
    diff = abs(r1-r2) + abs(g1-g2) + abs(b1-b2)
    if diff <= tolerance:  # Default: 20
        return pos
```

**K-Nearest Neighbors Interpolation**:
```python
# Find 4 nearest colors by Euclidean distance
color_distances = []
for color, pos in calibration_map:
    distance = sqrt(
        (r1-r2)^2 + (g1-g2)^2 + (b1-b2)^2
    )
    color_distances.append((distance, color, pos))

color_distances.sort()  # Ascending by distance
neighbors = color_distances[:k_neighbors]  # k=4

# Calculate inverse distance weights
weights = [1.0 / (dist + epsilon) for dist, _, _ in neighbors]
total_weight = sum(weights)
normalized_weights = [w / total_weight for w in weights]

# Calculate weighted position
weighted_x = sum(w * pos[0] for w, (_, _, pos) in zip(...))
weighted_y = sum(w * pos[1] for w, (_, _, pos) in zip(...))

return (int(weighted_x), int(weighted_y))
```

### Color Calibration

**Purpose**: Create precise RGB → (x, y) mapping

**Process**:
1. Configure Custom Colors (spectrum area)
2. Configure Color Preview Spot
3. Set calibration step size (1-10, default: 2)
4. Run calibration:
   - Press mouse at spectrum start
   - Drag through entire spectrum step by step
   - At each step, capture RGB from Preview Spot
   - Build calibration map: RGB → (x, y)
   - Release mouse
   - Show progress with ETA (overlay positioned above custom colors box)
   - Can be cancelled with ESC
5. Save to `color_calibration.json`
6. Load automatically during drawing

**Usage During Drawing**:
1. Check calibration map for exact match (tolerance=20)
2. If found: Use calibrated position
3. If not found: Use k-nearest neighbors with interpolation
4. Update progress overlay during calibration

---

## Progress Overlay System

### Purpose

Real-time progress display during long operations (drawing, calibration).

### Architecture

**Window Properties**:
- Always on top
- No window decorations (frameless)
- Semi-transparent background
- Drawing overlay: Fixed size: 240x20 pixels, positioned at top center of screen
- Calibration overlay: Fixed size: 400x20 pixels, positioned above custom colors box
- Green text on dark background

**Content**:
- Stroke count: "X/Y Strokes"
- ETA: "(ETA: Xs/Xm/Xh)"

### Implementation

**Create Overlay**:
```python
def create_progress_overlay():
    window = Toplevel()
    window.overrideredirect(True)  # Frameless
    window.attributes("-topmost", True)  # Always on top
    window.geometry(f"{width}x{height}+{x}+{y}")
    
    # Create label with progress text
    label = Label(window, text="Initializing...", 
                  bg="#2c2c2c", fg="#00ff00")
    label.pack()
    
    return window, label
```

**Update Progress**:
```python
def update_progress_overlay(completed, total, eta_seconds):
    progress_text = f"{completed}/{total} Strokes (ETA: {format_time(eta_seconds)})"
    label.config(text=progress_text)
    window.update()
```

**Close Overlay**:
```python
def close_progress_overlay():
    if window:
        window.destroy()
        window = None
        label = None
```

### Usage Scenarios

1. **Full Drawing**: Shows stroke progress and ETA
2. **Test Draw**: Shows test line progress
3. **Calibration**: Shows calibration progress with colors mapped (overlay above custom colors box)
4. **Region Redraw**: Shows region progress

---

## Calibration System

### Purpose

The calibration system provides precise RGB-to-position mapping for custom colors, enabling accurate color selection without keyboard input.

### Components

#### Color Calibration Map

- **Storage**: `color_calibration.json`
- **Structure**: Dictionary mapping RGB strings to (x, y) coordinates
- **Persistence**: Saved to disk, loaded on startup
- **Validation**: Loaded if file exists and is valid

#### Color Preview Spot

- **Purpose**: Capture the RGB value currently shown in color picker
- **Location**: Single pixel coordinate where selected color appears
- **Usage**: During calibration, capture RGB at this point for each spectrum position

#### Spectrum Scanning

- **Purpose**: Scan custom color spectrum to create initial mapping
- **Implementation**: Sample spectrum at regular intervals
- **Fallback**: Used when calibration map doesn't contain exact match

### Calibration Process

```
1. Initialize calibration
   ├─> Reset terminate flag
   ├─> Clear previous calibration map
   └─> Store grid parameters

2. Extract grid coordinates
   ├─> Get custom colors box
   ├─> Get preview point coordinates
   └─> Calculate grid dimensions

3. Execute scanning
   ├─> Press mouse down at spectrum start
   ├─> For each position (x, y):
   │     ├─> Move mouse to (x, y)
   │     ├─> Wait for UI update
   │     ├─> Capture 1x1 pixel at preview point
   │     ├─> Extract RGB value
   │     ├─> Store in map: RGB → (x, y)
   │     ├─> Update progress overlay (positioned above custom colors box)
   │     ├─> Calculate ETA
   │     └─> Check for termination (ESC)
   ├─> Release mouse up
   └─> Show completion message

4. Save calibration
   ├─> Convert tuple keys to strings for JSON
   ├─> Save to color_calibration.json
   └─> Print summary

5. Load for drawing
   ├─> Check if file exists
   ├─> Load JSON into memory
   ├─> Convert string keys back to tuples
   └─> Use for color position lookup
```

### Color Lookup During Drawing

```
1. Need to select color (r, g, b)
2. Check calibration map exists?
   ├─> No: Fall back to spectrum scanning
   └─> Yes: Try exact match
       ├─> Find exact match within tolerance (Manhattan distance ≤ 20)
       ├─> Found? Use calibrated position
       └─> Not found? Use k-nearest neighbors
             ├─> Find 4 nearest colors by Euclidean distance
             ├─> Calculate inverse distance weights
             ├─> Compute weighted position
             └─> Use interpolated position
3. Click on spectrum at calculated position
```

---

## Threading Model

### Purpose

Run long operations (processing, drawing, calibration) in background threads to keep UI responsive.

### Thread Types

1. **Draw Thread** (`_draw_thread`):
   - Runs full drawing operation
   - Updates progress overlay
   - Handles terminate/pause flags
   - Returns result on completion

2. **Test Draw Thread** (`_test_draw_thread_obj`):
   - Runs test draw operation
   - Limited to max_lines (default: 20)
   - Updates UI progress

3. **Simple Test Draw Thread** (`_simple_test_thread_obj`):
   - Runs simple line test
   - No color selection
   - Quick brush size verification

4. **Pre-compute Thread** (`_precompute_thread_obj`):
   - Processes image for caching
   - Saves to disk
   - Shows progress percentage

5. **Calibration Thread** (`_calibration_thread_obj`):
   - Runs color calibration
   - Shows progress overlay (positioned above custom colors box)
   - Supports cancellation (ESC)

6. **Redraw Region Thread** (`_redraw_thread`):
   - Runs region-based drawing
   - Shows progress overlay
   - Handles terminate/pause flags

7. **Keyboard Listener Thread** (`pynput_listener`):
   - Global keyboard monitoring
   - Handles ESC (terminate)
   - Handles pause_key (pause/resume)
   - Non-blocking operation

### Thread Management

**Starting a Thread**:
```python
def start_draw_thread():
    self._draw_thread = Thread(target=self.start)
    self._draw_thread.start()
    self._manage_draw_thread()  # Monitor progress
```

**Thread Monitor**:
```python
def _manage_draw_thread():
    if self._draw_thread.is_alive() and self.busy:
        self._root.after(500, self._manage_draw_thread)
        self.tlabel['text'] = f"Processing image: {self.bot.progress:.2f}%"
```

**Thread Safety**:
- Bot state modified with flags (`terminate`, `paused`, `drawing`)
- Progress updated via UI thread-safe methods
- Modifier keys handled carefully during pause/resume
- Resource cleanup on thread termination

---

## Configuration Management

### Configuration File Structure

**File**: `config.json`

**Sections**:
1. `drawing_settings`: Core drawing parameters
2. `drawing_options`: Feature toggles
3. `pause_key`: Pause/resume hotkey
4. `skip_first_color`: Skip first color drawing
5. `calibration_settings`: Calibration parameters
6. Tool configurations (Palette, Canvas, Custom Colors, etc.)
7. Tool options (New Layer, Color Button, Color Button Okay, MSPaint Mode, etc.)
8. `color_preview_spot`: Color preview spot for calibration
9. `last_image_url`: Recently used image URL

### Configuration Lifecycle

```
Application Start
  │
  ├─> Load config.json
  │     ├─> Exists: Parse and apply
  │     └─> Missing: Use defaults
  │
  ├─> User makes changes
  │     ├─> Drawing settings changed
  │     ├─> Checkboxes toggled
  │     └─> Tools configured
  │
  └─> Save to config.json
        (Automatic on each change)
```

### Tool Configuration

Each tool has a configuration structure:

```python
{
    "status": bool,           # Is tool initialized
    "box": [x1, y1, x2, y2], # Screen coordinates (for region-based tools)
    "coords": [x, y],         # Click coordinates (for point-based tools)
    "enabled": bool,           # Is feature active
    "modifiers": {             # Key modifiers
        "ctrl": bool,
        "alt": bool,
        "shift": bool
    },
    "delay": float,            # Delay after click (seconds)
    "preview": string          # Preview image path
}
```

**Special Tool Configurations**:

**Palette**:
```python
{
    "status": bool,
    "box": [x1, y1, x2, y2],
    "rows": int,              # Number of rows
    "cols": int,              # Number of columns
    "color_coords": {         # RGB to position mapping
        "(r,g,b)": [x, y]
    },
    "valid_positions": [      # Valid cell indices
        0, 1, 2, ...
    ],
    "manual_centers": {       # Manual center overrides
        "0": [x, y]
    },
    "preview": string
}
```

**Color Preview Spot**:
```python
{
    "name": "Color Preview Spot",
    "status": bool,
    "coords": [x, y],
    "enabled": bool,
    "modifiers": {ctrl, alt, shift}
}
```

**MSPaint Mode**:
```python
{
    "enabled": bool,
    "delay": float              # Delay between double-clicks (seconds)
}
```

---

## UI Architecture

### Main Window Structure

```
┌─────────────────────────────────────────────────────┐
│              Pyaint Main Window            │
├──────────────┬──────────────────────────────┤
│              │                              │
│   Control    │      Preview Panel           │
│    Panel     │                              │
│              │                              │
│  - Settings  │                              │
│  - Actions   │                              │
│  - Options   │                              │
│              │                              │
├──────────────┴──────────────────────────────┤
│         Tooltip / Status Panel              │
└─────────────────────────────────────────────┘
```

### Control Panel Components

**Drawing Settings**:
- Delay (text entry, 0.01-10.0s)
- Pixel Size (slider, 3-50)
- Precision (slider, 0.0-1.0)
- Jump Delay (slider, 0.0-2.0s)
- Jump Threshold (text entry, 1-100)

**Drawing Options** (checkboxes):
- Ignore White Pixels
- Use Custom Colors
- Skip First Color
- Enable New Layer
- Enable Color Button
- Enable Color Button Okay
- Enable MSPaint Mode (double-click on palette/spectrum)

**Additional Settings**:
- MSPaint Delay (entry, 0.01-5.0s)
- Calibration Step (entry, 1-10)
- Jump Threshold (entry, 1-100)
- Pause Key (entry field)

**Drawing Mode**:
- Slotted Mode (dropdown/OptionMenu)
- Layered Mode (dropdown/OptionMenu, default)

**Actions**:
- Setup
- Pre-compute
- Simple Test Draw
- Test Draw
- Run Calibration
- Start

**Redraw Region**:
- Redraw Pick (select region)
- Draw Region (draw selected region)

**File Management**:
- Remove Calibration
- Reset Config

### Setup Window Structure

Multi-tab configuration interface for tools:
- Palette configuration (with manual color selection using canvas-based grid)
- Canvas configuration
- Custom Colors configuration
- Color Preview Spot configuration
- New Layer configuration
- Color Button configuration
- Color Button Okay configuration
- MSPaint Mode configuration

**Manual Color Selection UI Features**:
- Canvas-based grid display with palette image background
- Toggle valid/invalid cells (green=valid, red=invalid)
- Pick centers mode for manual center placement
- Auto-estimate centers with overlay visualization (InteractivePaletteExtractor)
- Precision Estimate for advanced palette extraction
- Show Custom Centers overlay
- Select All / Deselect All buttons
- Done button to save changes

---

## Control Flow

### Keyboard Control

**Global Listener** (pynput):
```python
def on_pynput_key(key):
    # Handle ESC
    if key == Key.esc:
        bot.terminate = True
    
    # Handle pause key during drawing
    if bot.drawing:
        key_name = extract_key_name(key)
        if key_name == pause_key.lower():
            bot.paused = not bot.paused
```

### Drawing Control Loop

```python
def draw_loop():
    for command in drawing_commands:
        # Check termination
        if terminate:
            break
        
        # Check pause
        while paused:
            time.sleep(0.1)
            if terminate:
                break
        
        # Execute command
        execute_command(command)
        
        # Update progress overlay
        update_progress_overlay(completed, total, eta)
        
        # Update ETA calculation
        recalculate_eta()
```

### Error Handling

```python
try:
    operation()
except NoToolError as e:
    show_error("Tool not initialized")
except NoPaletteError as e:
    show_error("Palette not configured")
except NoCanvasError as e:
    show_error("Canvas not configured")
except NoCustomColorsError as e:
    show_error("Custom colors not configured")
except CorruptConfigError as e:
    show_error("Configuration file is corrupt")
except Exception as e:
    show_error(f"Unexpected error: {e}")
    traceback.print_exc()
```

---

## Design Patterns

### Observer Pattern

**Usage**: Progress updates and status changes

**Implementation**:
- Window observes Bot state
- Tooltip updates based on state changes
- Progress overlay reflects drawing progress

### Strategy Pattern

**Usage**: Drawing modes (Slotted vs Layered)

**Implementation**:
- Different image processing strategies
- User selects mode at runtime
- Bot delegates to appropriate strategy

### Factory Pattern

**Usage**: Tool configuration creation

**Implementation**:
- Setup window creates tool configurations
- Standardized configuration structures
- Extensible to new tools

### Singleton Pattern

**Usage**: Bot instance

**Implementation**:
- Single Bot instance created in main.py
- Shared across UI components
- Centralized drawing control

### Thread-Per-Task Pattern

**Usage**: Long-running operations

**Implementation**:
- Each operation runs in separate thread
- Main thread remains responsive
- Thread monitors update UI

---

## Performance Considerations

### Caching Strategy

**Pre-computed Images**:
- Process once, draw multiple times
- Stored in `cache/` directory
- Validated on load (settings match, < 24 hours old)
- Significant speedup for repeated drawings

**Color Maps**:
- Palette color coordinates cached
- Custom color spectrum cached
- Calibration map loaded from file
- Cached during session

### Optimization Techniques

1. **Color Grouping**: Group pixels by color to minimize color switches
2. **Frequency Sorting**: Draw most common colors first (Layered mode)
3. **Region Processing**: Draw only needed areas (Region redraw)
4. **Pixel Size Tuning**: Balance detail vs. speed
5. **Threading**: Keep UI responsive during long operations
6. **Progress Overlay**: Real-time feedback without blocking
7. **Jump Delay Optimization**: Only apply delay when cursor moves significantly

---

## Extensibility

### Adding New Tools

To add a new tool:

1. Define configuration structure in `config.json`
2. Add UI elements in `ui/setup.py`
3. Add activation logic in `bot.py`
4. Add modifier key support if needed
5. Update documentation

### Adding New Drawing Modes

To add a new drawing mode:

1. Define processing algorithm
2. Add to drawing mode selection UI (OptionMenu/dropdown)
3. Implement in Bot class (process method)
4. Update documentation

### Adding New Calibration Features

To add new calibration features:

1. Extend calibration methods in Bot class
2. Add UI configuration in setup.py
3. Update calibration progress tracking
4. Update documentation

---

## See Also

- [API Reference](./api.md) - Complete API documentation
- [Configuration Guide](./configuration.md) - Configuration options
- [Tutorial](./tutorial.md) - Step-by-step usage guide
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions