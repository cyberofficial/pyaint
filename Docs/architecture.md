# Pyaint Architecture

System architecture for Pyaint — image-to-brush-strokes automation tool.

## Technology Stack

- **Python 3.12** — primary language
- **Pillow (PIL)** — image processing
- **PyAutoGUI** — mouse/keyboard automation
- **Pynput** — global keyboard event handling
- **Tkinter** — GUI framework
- **JSON** — configuration and cache storage
- **threading** — concurrent operations

## Module Overview

### `main.py` — Entry Point

Creates a `Bot` instance, starts a `pynput` keyboard listener, then opens the main `Window`. The listener handles ESC (terminate) and the configured pause key.

### `bot.py` — Core Engine

Contains `Palette` and `Bot` classes.

**Palette** (line 21): Extracts palette colors from a screenshot region. Builds an RGB→screen-coordinates dict. Provides `nearest_color()` for best-match pixel → palette color mapping (squared Euclidean distance).

**Bot** (line 92): State machine managing:
- `settings`: [delay, step(pixel_size), accuracy(precision), jump_delay]
- `options`: Bitmask flags (`IGNORE_WHITE`, `USE_CUSTOM_COLORS`)
- `draw_state`: Pause/resume recovery state (color_idx, line_idx, segment_idx)
- `path_optimization`: Stroke reordering flag (default: True)
- `single_color_*`: Single Color mode state (ignore color, tolerance, configured flag, mode_active flag)
- `mspaint_mode`: double-click toggle
- `color_button` / `color_button_okay`: optional tool click config
- Canvas calibration and color calibration state

**Key Methods:**

| Method | Description |
|--------|-------------|
| `process(file, flags, mode)` | Image → cmap (color→stroke-segments dict). Supports SLOTTED or LAYERED |
| `process_single_color(file, ignore_color, tolerance, flags)` | Like process but skips pixels matching ignore_color within tolerance |
| `generate_single_color_preview(file, ignore_color, tolerance)` | Returns RGBA image with red overlay showing drawn pixels |
| `process_region(file, region, flags, mode, canvas_target)` | Region-based processing (redraw) |
| `precompute(image_path, flags, mode)` | Process + cache to disk. Optimizes stroke order if enabled |
| `draw(cmap)` | Executes the full draw loop with pause/resume, color selection, stroke drawing |
| `test_draw(cmap, max_lines=20)` | Draw first N lines for brush-size testing |
| `simple_test_draw()` | Quick 5-line horizontal test (no color picking) |
| `optimize_stroke_order(cmap)` | Greedy nearest-neighbor reorder per color — minimizes cursor jump distance |
| `calibrate_custom_colors(grid_box, preview_point, step)` | Scans color spectrum to build RGB→position map |
| `get_calibrated_color_position(target_rgb, tolerance, k_neighbors)` | Lookup or interpolate calibrated color position |

**Drawing Flow:**

1. `process()` or `process_single_color()` → cmap dict
2. `draw()`: For each color in cmap:
   - Optionally click New Layer button + modifier keys
   - Optionally click Color Button + modifier keys  
   - **Skip color selection** if `single_color_mode_active` (user has manual brush)
   - Otherwise: palette click → spectrum/calibration → keyboard fallback
   - Optionally click Color Button Okay
   - For each stroke: check terminate/paused, check jump distance, mouseDown→drag→mouseUp
3. Close progress overlay, return result

### `utils.py`

- `resource_path(relative_path)` — resolves `sys._MEIPASS` for PyInstaller builds, or file-relative for dev
- `adjusted_img_size(img, ad)` — scale image to fit bounding box maintaining aspect ratio

### `exceptions.py`

- `NoToolError` — base for uninitialized tools
- `NoPaletteError`, `NoCanvasError`, `NoCustomColorsError` — inherit from NoToolError
- `CorruptConfigError` — inherits from Exception directly

### `canvas_calibration.py`

`CanvasCalibrator` class: draws a 9-dot cross-pattern on canvas, measures the actual spacing via screenshot analysis, calculates a scale factor for zoom/brush-size compensation.

### `palette_generator.py`

`ColorPaletteGenerator` class: analyzes image color frequencies. Supports 4 algorithms:
- Frequency (most common colors)
- Dominant Shades (most dominant per hue group)
- Rare Shades (least dominant per hue group)
- K-Means (multi-threaded clustering)

Exports to GIMP-compatible CSS.

### `ui/window.py` — Main GUI

~1100-line Tkinter window with a `ttk.Notebook` layout and dedicated panels:
- **Settings tab** (`ui/settings_panel.py`): draw-mode selector, sliders, misc checkboxes, feature toggles
- **Preview tab** (`ui/image_panel.py`): image display, URL/file input
- **Actions tab** (`ui/action_panel.py`): action buttons, redraw region, file management
- **StatusBar** (`ui/status_bar.py`): bottom status messages, progress updates
- `_process_image()` helper routes to `process()` or `process_single_color()` based on `_mode`
- `@is_free` decorator prevents concurrent operations
- Config persistence delegated to `ConfigManager` (`ui/config_manager.py`); `Window.tools` is a live alias of its data dict
- Background operations run through `ThreadManager` (`ui/thread_manager.py`); panel state is exposed via the `_mode`, `draw_options`, and `_imname` properties

### `ui/setup.py` — Configuration Wizard

`SetupWindow` class: Toplevel window for initializing tools via mouse-click selection. Supports:
- Region capture (2-click: upper-left, lower-right)
- Single-click tools (New Layer, Color Button, etc.)
- Palette editing (valid/invalid toggle, center picking, auto-estimate)
- `InteractivePaletteExtractor`: 3-phase palette extraction with anchor points

### `ui/single_color_window.py` — Single Color Config

`SingleColorWindow` class: Toplevel with click-to-pick background color, tolerance slider, red-overlay preview, pixel count, and quick-action buttons (White/Binarize/Black). Sets `bot.single_color_ignore`, `bot.single_color_tolerance`, `bot.single_color_configured`.

### `ui/palette_window.py` — Palette Generator UI

`PaletteWindow` class: algorithm selection, color swatches, tie resolution, GIMP CSS export.

## Drawing Modes

### Slotted
Per-color row segments. Each stroke is a horizontal line between color transitions. Simple, fast.

### Layered
Builds row-based color tables, then merges segments by color frequency (most frequent colors drawn last = on top). Better visual quality for complex images.

### Single Color
User picks a background color to ignore (click on their image). Everything else gets processed normally. No palette clicking — the user selects their brush color manually. The `single_color_mode_active` flag guards against all automated color selection, and `skip_first_color` is bypassed.

## Path Optimization

When enabled (default), `optimize_stroke_order()` reorders strokes within each color group using a greedy nearest-neighbor algorithm:
- Start with any stroke
- Find the nearest remaining stroke by start or end point
- Optionally reverse the stroke direction for a shorter jump
- Repeat until all strokes ordered

This eliminates the "scanline" jumping that makes raster-order drawing look robotic. The optimization runs during `precompute()` if enabled and is cached. On cache load, it skips re-optimization if the cached cmap was already optimized.

## Configuration

All settings persist to `config.json`. A `resource_path()` helper ensures correct file resolution in both development and PyInstaller builds. `ConfigManager` (`ui/config_manager.py`) is the single I/O point: it auto-saves on any mutation, and `begin_batch()`/`end_batch()` suppress saves during initialization. Config is auto-saved on any toggle, slider change, or setup action.

## Threading

Long operations run via background threads launched by `ThreadManager` (`ui/thread_manager.py`), which polls them through `root.after`:
- Pre-compute, Test Draw, Simple Test Draw, Full Draw, Calibration
- `@is_free` decorator in window.py prevents concurrent operations; thread targets clear the `busy` flag in their `finally`
- Jobs with bespoke progress UIs (calibration overlay) supply a custom `poll_fn`
- Progress overlay shows stroke count + ETA during drawing

## Error Handling

print-based logging throughout. Custom exceptions in `exceptions.py` — callers handle at the UI level with messagebox popups.
