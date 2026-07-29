# Pyaint Tutorial

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Initial Setup

Every tool must be configured via the **Setup** button before drawing.

### Essential Tools

1. **Palette**: Click Initialize → click upper-left corner of your palette → click lower-right corner. Set rows/cols to match your palette grid.
2. **Canvas**: Click Initialize → click upper-left corner of your canvas area → click lower-right corner.

### Optional Tools

- **Custom Colors** — for unlimited color matching via a spectrum. Required if using "Use Custom Colors" checkbox
- **Color Preview Spot** — a single pixel where your drawing app previews the selected color. Required for calibration
- **New Layer** / **Color Button** / **Color Button Okay** — for apps needing extra clicks. Configure the button position once
- **MSPaint Mode** — enable double-click on palette (e.g., MS Paint)

### Advanced Palette Features

After initializing the palette, click **Manual Color Selection**:
- **Toggle Valid/Invalid**: Click cells to enable/disable (green = valid)
- **Pick Centers**: Click a cell, then click the exact center on your palette. Automatic advance to next cell
- **Auto-Estimate**: Grid-based center calculation
- **Interactive Palette Extraction**: Anchor-point based precision (3-phase: region → grid → anchors)

## Color Calibration

For better custom color accuracy:
1. Configure **Custom Colors** and **Color Preview Spot** in Setup
2. Set **Calibration Step Size** (1-10, lower = more accurate)
3. Click **Run Calibration**
4. Bot scans the spectrum, mapping RGB values to screen positions
5. Saved to `color_calibration.json` — auto-loaded on subsequent draws

## Drawing Modes

| Mode | Description |
|------|-------------|
| **Slotted** | Fast per-color row segments. Best for simple images |
| **Layered** | Color-frequency sorted, stroke merging. Better quality for complex images |
| **Single Color** | For line art. Pick a background color to ignore; everything else draws |

## Single Color Mode

1. Select "Single Color" from Draw Mode dropdown
2. Config window opens — **click on your image's background color**
3. Adjust **Tolerance** slider (higher = more aggressive background removal)
4. Red overlay shows what gets drawn; transparent areas are ignored
5. Quick actions: White Background, Binarize (high contrast), Black Background
6. Click **Confirm**, then **Start** — set your brush color manually; bot won't click palette

## Drawing Workflow

1. **Load image** — URL or file
2. **(Optional) Pre-compute** — caches processing for instant reruns. Also caches stroke optimization if enabled
3. **Test Draw** — draws first 20 lines to check brush alignment
4. **Simple Test Draw** — draws 5 horizontal lines with current brush color
5. **Start** — full drawing

### Controls

- **ESC**: Emergency stop
- **Pause Key** (default 'P'): Pause/resume at exact interruption point
- **Path Optimization checkbox**: Minimize cursor jumps (reorders strokes per color)
- **Pre-compute**: Run once, draw instantly on subsequent clicks

## Region-Based Redraw

1. Click **Pick Region** in Redraw Region section
2. Click upper-left → lower-right of the area to redraw
3. Click **Draw Region**

## Path Optimization

Toggle via **Minimize cursor jumps** checkbox. When enabled:
- Strokes within each color group are reordered (greedy nearest-neighbor)
- Cursor flows naturally instead of jumping across canvas
- If enabled during Pre-compute, the optimized order is cached — Start skips re-optimization

## Tips

- Always **Test Draw** first to verify brush size
- **Pre-compute** saves time on repeated draws
- Enable **Ignore White Pixels** for white/canvas-colored backgrounds
- **Pixel Size** controls detail, not brush size — adjust brush in your drawing app
- Use **Single Color mode** for line art and sketches
