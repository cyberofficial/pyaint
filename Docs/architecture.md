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
├── canvas_calibration.py # Canvas calibration system
├── palette_generator.py # Advanced color analysis and palette generation
├── ui/
│   ├── __init__.py
│   ├── window.py        # Main application window
│   ├── setup.py         # Setup/configuration window
│   └── palette_window.py # Palette extraction interface
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

#### `canvas_calibration.py`

**Purpose**: Advanced canvas calibration system with cross-pattern detection

**Responsibilities**:
- Cross-pattern drawing for zoom detection
- Image-based measurement of drawn patterns
- Scale factor calculation and validation
- Brush size measurement and verification
- Calibration result persistence

**Key Functions**:
- `run_calibration(canvas_coords, intended_spacing, user_brush_size)`: Execute calibration process

#### `palette_generator.py`

**Purpose**: Sophisticated color analysis and palette generation system

**Responsibilities**:
- Multi-threaded image processing for large images
- HSV color space conversion and hue-based grouping
- K-Means clustering with K-Means++ initialization
- Weighted color sampling based on frequency
- Multi-algorithm palette generation
- Progress callbacks for long-running operations

**Key Classes**:
- `ColorPaletteGenerator`: Main palette generation class

**Key Methods**:
- `analyze_image()`: Analyze image and count color frequencies
- `get_palette(num_colors, algorithm)`: Generate palette using specified algorithm
- `export_gimp_css(colors, output_path)`: Export colors as GIMP-compatible CSS

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
- `start_test_draw_thread()`: Start test draw in background thread
- `start_simple_test_draw_thread()`: Start simple test draw in background thread
- `start_calibration_thread()`: Start calibration in background thread
- `start_draw_thread()`: Start drawing in background thread
- `_on_redraw_pick()`: Enter region picking mode
- `redraw_region()`: Execute region redraw
- `_set_img(image=None, path=None)`: Load and display image
- `load_config()`: Load configuration from file
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
- Color calibration overlay positioning

#### `ui/setup.py`

**Purpose**: Tool configuration interface

**Responsibilities**:
- Configure palette, canvas, custom colors
- Configure optional tools (New Layer, Color Button, Color Button Okay)
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
- `close()`: Close setup window and call completion callback

**InteractivePaletteExtractor Key Methods**:
- `__init__(parent, bot, current_tool, tool_name, valid_positions, palette_box, on_complete)`: Initialize extractor
- `_start_phase_1()`: Start phase 1: Region selection
- `_on_region_click(x, y, button, pressed)`: Handle region selection in phase 1
- `_capture_palette()`: Capture palette image from selected region
- `_start_phase_2()`: Start phase 2: Grid configuration
- `_on_set_grid()`: Handle grid dimension input
- `_start_phase_3()`: Start phase 3: Anchor placement
- `_on_extract_colors()`: Extract colors and complete extraction

**Key Features**:
- Manual color selection with valid/invalid toggling
- Precision estimate for automatic center calculation via InteractivePaletteExtractor
- Pick centers mode for manual center placement
- Auto-estimate centers with overlay visualization
- Three-phase interactive palette extraction:
  - Phase 1: Select palette region
  - Phase 2: Configure grid (rows, cols)
  - Phase 3: Place anchor points for interpolation
- Anchor point interpolation for accurate center estimation

#### `ui/palette_window.py`

**Purpose**: Color palette extraction and management interface

**Key Classes**:
- `PaletteWindow`: Palette extraction interface

**Key Features**:
- Multiple extraction algorithms (frequency, dominant shades, rare shades, K-Means)
- Real-time image analysis and color counting
- Configurable palette size and algorithm selection
- Color preview and selection with percentage display
- Multi-threaded K-Means clustering with progress tracking
- Export functionality for GIMP-compatible CSS palettes

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
              │     ├─> Palette
              │     ├─> Canvas
              │     ├─> Custom Colors
              │     ├─> New Layer
              │     ├─> Color Button
              │     ├─> Color Button Okay
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
  │     │     ├─> Click Color Button (if enabled)
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

#### Canvas Calibration

- **Purpose**: Detect canvas zoom level for accurate coordinate mapping
- **Process**: Draw cross-pattern, measure with image analysis, calculate scale factor
- **Storage**: Saved in canvas tool configuration
- **Usage**: Applied during coordinate transformation

---

## Threading Model

### Purpose

Run long operations (processing, drawing, calibration) in background threads to keep UI responsive.

### Thread Types

1. **Draw Thread**: Runs full drawing operation
2. **Test Draw Thread**: Runs test draw operation
3. **Simple Test Draw Thread**: Runs simple line test
4. **Pre-compute Thread**: Processes image for caching
5. **Calibration Thread**: Runs color calibration
6. **Redraw Region Thread**: Runs region-based drawing
7. **Keyboard Listener Thread**: Global keyboard monitoring

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
- Pixel Size (slider, 1-50)
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

---

## Performance Considerations

### Optimization Strategies

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

---

## See Also

- [API Reference](./api.md) - Complete API documentation
- [Configuration Guide](./configuration.md) - Configuration options
- [Tutorial](./tutorial.md) - Step-by-step usage guide
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions