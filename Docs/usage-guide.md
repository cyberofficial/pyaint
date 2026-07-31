# Pyaint Usage Guide

## Setup Process

Click **Setup** to open the configuration wizard. Each tool has an **Initialize** button — click it, then click the relevant area in your drawing app.

### Palette

1. Set **Rows** and **Columns** matching your palette grid
2. Click **Initialize**
3. Click **upper-left corner** of palette → click **lower-right corner**
4. The screenshot captures all colors into a RGB→position map

**Post-init options:**
- **Manual Color Selection**: Toggle valid/invalid cells, pick exact center points
- **Auto-Estimate**: Quick grid-based center calculation
- **Edit Colors**: Opens Interactive Palette Extractor with anchor-point placement (3-phase: region → grid → anchors)

### Canvas

1. Click **Initialize**
2. Click upper-left → lower-right corners of your drawing area
3. (Optional) Run **Calibrate Canvas** — draws a single dot at the center, diffs before/after screenshots, calculates the zoom scale factor

### Custom Colors (Optional)

1. Click **Initialize**
2. Click upper-left → lower-right corners of the color spectrum in your app

### Color Preview Spot (Optional for Calibration)

1. Click **Initialize**
2. Click the exact pixel where your app previews the selected color

### New Layer / Color Button / Color Button Okay (Optional)

Each is a single-click tool: Initialize → click the button location in your app. Configure modifier keys (Ctrl/Alt/Shift) if the app requires keyboard shortcuts.

## Drawing Flow

1. **Load image** — enter URL and click Search, or click Open File
2. **Select mode** — Slotted, Layered, or Single Color
3. **Adjust settings** — Delay, Pixel Size, Precision, Jump Delay
4. **Enable options** — Ignore White Pixels, Use Custom Colors, Skip First Color, etc.
5. **(Optional) Pre-compute** — runs processing + stroke optimization (if enabled), saves to cache
6. **Test Draw** — draws first 20 lines to verify brush alignment
7. **Simple Test Draw** — draws 5 horizontal lines (no color picking)
8. **Start** — full drawing. App minimizes during drawing. ESC to stop, pause key to pause/resume

## Single Color Mode

For line art and images where background removal is needed:

1. Select "Single Color" from **Draw Mode** dropdown
2. Config window opens with your loaded image
3. **Click on the background color** you want to ignore
4. Adjust **Tolerance** slider — controls color match strictness
5. Live preview shows red overlay on drawn pixels, transparent on ignored
6. Quick actions: **White Background** (tolerance 16), **Binarize** (tolerance 64, for high-contrast), **Black Background**
7. Click **Confirm** to save settings
8. Click **Start** — bot draws all non-background pixels. You pick your brush color manually

**Note**: In Single Color mode, the bot skips all palette clicking, Color Button clicks, and New Layer clicks. The `skip_first_color` setting is also bypassed. Set your brush color in your drawing app before starting.

## Path Optimization

Toggle **Minimize cursor jumps** in the Settings tab. When enabled:
- Stroke order is optimized per color group using nearest-neighbor algorithm
- Can reverse stroke direction for shorter cursor travel
- Eliminates scanline jump patterns
- If on during Pre-compute, optimized order is cached
- Works with all drawing modes

## Canvas Calibration

Detects zoom level and brush size for consistent results:

1. Draw a test line to set your brush size
2. In Setup, click **Calibrate Canvas**
3. Click upper-left → lower-right of your canvas
4. Bot draws 1 dot at the center (make sure the canvas is clear first)
5. Measures the dot's actual size via before/after screenshot diff
6. Calculates scale factor applied to pixel size during drawing

## Color Calibration

Creates a precise RGB→screen-position map for custom colors:

1. Configure **Custom Colors** (spectrum area)
2. Configure **Color Preview Spot** (where selected color appears)
3. Set **Calibration Step Size** (1-10, default: 2)
4. Click **Run Calibration**
5. Bot drags through the spectrum, capturing RGB at each step
6. Saved to `color_calibration.json` — auto-loaded during draws

## Region-Based Redraw

1. Click **Pick Region**
2. Click upper-left → lower-right corners on the preview image
3. Click **Draw Region** to draw only that area

## File Management

- **Remove Calibration**: Deletes `color_calibration.json`
- **Reset Config**: Deletes `config.json` (requires restart and re-setup)

## Keyboard Controls

| Key | Action |
|-----|--------|
| **ESC** | Emergency stop |
| **Pause Key** (default 'P') | Pause/resume drawing at exact point |

## Settings Reference

| Setting | Range | Default | Control |
|---------|-------|---------|---------|
| Delay | 0.01-10.0s | 0.1 | Text entry |
| Pixel Size | 3-50 | 12 | Slider |
| Precision | 0.0-1.0 | 0.9 | Slider |
| Jump Delay | 0.0-2.0s | 0.5 | Slider |
| Jump Threshold | 1-100 | 5 | Text entry |
| Calibration Step | 1-10 | 2 | Text entry |
| Path Optimization | on/off | On | Checkbox |
