# Pyaint API Reference

## Bot Class (`bot.py`)

### Constructor
```python
Bot(config_file='config.json')
```

### Constants

| Name | Value | Description |
|------|-------|-------------|
| `SLOTTED` | `'slotted'` | Simple color-to-lines mapping |
| `LAYERED` | `'layered'` | Color-frequency sorted with stroke merging |
| `SINGLE_COLOR` | `'single_color'` | Background-ignore mode for line art |
| `IGNORE_WHITE` | `1 << 0` | Bitmask flag to skip white pixels |
| `USE_CUSTOM_COLORS` | `1 << 1` | Bitmask flag for custom color matching |

### Settings (list accessed by index)

| Index | Constant | Type | Description |
|-------|----------|------|-------------|
| 0 | `Bot.DELAY` | float | Stroke duration (seconds) |
| 1 | `Bot.STEP` | int | Pixel step size (detail) |
| 2 | `Bot.ACCURACY` | float | Color accuracy threshold (0.0-1.0) |
| 3 | `Bot.JUMP_DELAY` | float | Delay on large cursor jumps |

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `terminate` | bool | Set True to stop drawing |
| `paused` | bool | Toggle pause/resume |
| `drawing` | bool | True while actively drawing |
| `pause_key` | str | Key for pause/resume (default: 'p') |
| `skip_first_color` | bool | Skip first palette color |
| `jump_threshold` | int | Pixel distance triggering jump delay (default: 5) |
| `progress` | float | 0-100 progress percentage |
| `total_strokes` | int | Total strokes in current draw |
| `completed_strokes` | int | Strokes drawn so far |
| `path_optimization` | bool | Enable stroke reordering (default: True) |
| `single_color_ignore` | tuple | (R,G,B) color to ignore in Single Color mode |
| `single_color_tolerance` | int | Tolerance for ignore color matching |
| `single_color_configured` | bool | True after Single Color config confirmed |
| `single_color_mode_active` | bool | True during Single Color draw (skips palette clicks) |

### Image Processing

```python
process(file, flags=0, mode=LAYERED) -> dict
```
Process image into color map. Returns `{color: [(start,end), ...]}`.

```python
process_single_color(file, ignore_color, tolerance=16, flags=0) -> dict
```
Process image skipping pixels matching ignore_color within tolerance.

```python
process_region(file, region, flags=0, mode=LAYERED, canvas_target=None) -> dict
```
Process a cropped region of an image.

```python
generate_single_color_preview(file, ignore_color, tolerance=16) -> PIL.Image
```
Return RGBA image overlay showing drawn pixels in red, ignored as transparent.

### Drawing

```python
draw(cmap) -> 'success' | 'terminated'
```
Execute full drawing loop with pause/resume, color selection, progress overlay.

```python
test_draw(cmap, max_lines=20) -> 'success' | 'terminated'
```
Draw first N lines for brush calibration.

```python
simple_test_draw() -> 'success'
```
Draw 5 horizontal lines using current brush color (no palette).

### Stroke Optimization

```python
optimize_stroke_order(cmap) -> dict
```
Greedy nearest-neighbor reorder of strokes per color. Minimizes cursor jump distance. Can reverse strokes for shorter travel.

### Pre-compute / Cache

```python
precompute(image_path, flags=0, mode=LAYERED) -> str
```
Process and cache image. Saves to `cache/{hash}_{hash}.json`. If `path_optimization` is enabled, optimizes before caching.

```python
load_cached(cache_file) -> dict | None
```
Load and validate cache. Returns dict with 'cmap', 'settings', 'path_optimization', etc.

```python
get_cache_filename(image_path, flags=0, mode=LAYERED) -> str | None
```
Generate cache filename from image hash + settings hash.

```python
get_cached_status(image_path, flags=0, mode=LAYERED) -> (bool, str | None)
```
Check if valid cache exists.

### Calibration

```python
calibrate_custom_colors(grid_box, preview_point, step=2) -> dict
```
Scan color spectrum, build RGB→position map.

```python
save_color_calibration(filepath) -> bool
load_color_calibration(filepath) -> bool
```
Persist/restore color calibration JSON.

```python
get_calibrated_color_position(target_rgb, tolerance=20, k_neighbors=4) -> (x,y) | None
```
Lookup or interpolate calibrated color position.

### Progress Overlay

```python
create_progress_overlay()
update_progress_overlay(completed, total, eta_seconds)
close_progress_overlay()
```
Manage the floating progress window showing stroke count and ETA.

## Palette Class (`bot.py`)

```python
Palette(colors_pos=None, box=None, rows=None, columns=None, valid_positions=None, manual_centers=None)
```

| Method | Description |
|--------|-------------|
| `nearest_color(query_rgb)` | Find closest palette color by squared Euclidean distance |

## Utility Functions (`utils.py`)

```python
resource_path(relative_path) -> str
```
Resolve paths relative to `sys._MEIPASS` (PyInstaller) or `utils.py` directory (dev).

```python
adjusted_img_size(img, bounding_box) -> (width, height)
```
Scale image to fit within dimensions while preserving aspect ratio.

## Exception Classes (`exceptions.py`)

| Exception | Parent | Raised When |
|-----------|--------|-------------|
| `NoToolError` | Exception | Base for uninitialized tools |
| `NoPaletteError` | NoToolError | Palette not initialized |
| `NoCanvasError` | NoToolError | Canvas not initialized |
| `NoCustomColorsError` | NoToolError | Custom colors not initialized |
| `CorruptConfigError` | Exception | Config JSON is invalid |

## Window Class (`ui/window.py`)

```python
Window(title, bot, width, height, screen_x, screen_y)
```

### Key Methods

| Method | Description |
|--------|-------------|
| `load_config()` | Load settings from config.json |
| `_process_image()` | Route to process() or process_single_color() based on `_mode` |
| `start_precompute_thread()` | Pre-compute in background thread |
| `start_test_draw_thread()` | Test draw in background thread |
| `start_draw_thread()` | Full draw in background thread |
| `start_simple_test_draw_thread()` | Simple 5-line test |
| `start_calibration_thread()` | Color calibration in background |
| `_on_check(index, option)` | Toggle drawing option checkboxes |
| `_on_newlayer_toggle()` / `_on_colorbutton_toggle()` / etc. | Tool toggle handlers |
| `_open_single_color_window()` | Open Single Color config (prevents duplicates) |

### UI Panels

- **Control Panel** (left): Settings sliders, checkboxes, mode dropdown, action buttons
- **Preview Panel** (right): Image display, URL/file input
- **Tooltip Panel** (bottom): Status messages, progress updates

## SetupWindow Class (`ui/setup.py`)

```python
SetupWindow(parent, bot, tools, on_complete, title='Child Window', w=1600, h=900, x=5, y=5)
```

Configures tools via mouse-click selection. Each tool has Initialize/Preview buttons.
- Region tools (Palette, Canvas, Custom Colors): 2 clicks (upper-left, lower-right)
- Point tools (New Layer, Color Button, Color Button Okay, Color Preview Spot): 1 click

## InteractivePaletteExtractor (`ui/setup.py`)

3-phase palette extraction:
1. **Region Selection**: Click palette corners
2. **Grid Configuration**: Set rows/cols
3. **Anchor Placement**: Click on palette image, enter cell number. System interpolates all positions

## SingleColorWindow Class (`ui/single_color_window.py`)

```python
SingleColorWindow(parent, bot, image_path)
```

Config window for Single Color mode. Features:
- Click-to-pick background color on image
- Tolerance slider (0-128, default 16)
- Red overlay preview showing drawn vs. ignored pixels
- Pixel count and percentage display
- Quick actions: White Background, Binarize, Black Background

## PaletteWindow Class (`ui/palette_window.py`)

```python
PaletteWindow(parent, image_path, bot)
```

Color palette generator with algorithm selection and GIMP CSS export.

## CanvasCalibrator Class (`canvas_calibration.py`)

```python
CanvasCalibrator(canvas_coords)
```

- `dot_size_from_screenshot(center_x, center_y)` — measure a dot on canvas
- `measure_spacing(center_pos, intended_spacing)` — measure cross-pattern spacing

## ColorPaletteGenerator Class (`palette_generator.py`)

```python
ColorPaletteGenerator(image_path, ignore_white=True)
```

| Method | Description |
|--------|-------------|
| `analyze_image()` | Count color frequencies |
| `get_palette(num_colors, algorithm, progress_callback)` | Extract palette (frequency/dominant_shades/rare_shades/kmeans) |
| `export_gimp_css(colors, output_path)` | Save as GIMP-compatible CSS |
| `find_ties(num_colors)` | Find tied colors at selection boundary |
| `rgb_to_hsv(rgb)` | Convert RGB to HSV |
| `group_colors_by_hue(num_bins)` | Group by hue ranges |
| `get_color_stats()` | Statistics for extracted palette |

## `run_calibration()` (`canvas_calibration.py`)

```python
run_calibration(canvas_coords, intended_spacing, user_brush_size) -> dict
```

Full canvas calibration: draws cross-pattern, measures spacing, returns scale factor.
