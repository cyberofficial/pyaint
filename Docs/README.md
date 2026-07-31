# Pyaint Documentation

Pyaint converts images into automated mouse movements for painting applications (MS Paint, Clip Studio Paint, GIMP, skribbl, etc.).

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

1. Click **Setup** — configure palette, canvas, custom colors
2. Load an image (URL or file)
3. **Pre-compute** to cache processing (recommended)
4. **Test Draw** to check brush alignment
5. Click **Start** to draw
6. Press **ESC** to stop, **P** (default) to pause/resume

## Features

- **3 Drawing Modes**: Slotted (fast), Layered (quality), Single Color (line art)
- **Path Optimization**: Reorders strokes so the cursor flows naturally
- **Custom Colors**: Spectrum-based color matching with calibration
- **Canvas Calibration**: Auto-detect zoom via single-dot measurement  
- **Pre-compute Cache**: Process once, draw instantly on rerun
- **Pause/Resume**: Mid-stroke recovery from exact interruption point
- **Region Redraw**: Select part of the image to redraw only
- **Color Palette Generator**: Extract palettes via frequency/K-Means

## Architecture

```
pyaint/
├── main.py                 # Entry point — keyboard listener + Window launch
├── bot.py                  # Core engine: Palette, Bot (state machine, 3 modes)
├── utils.py                # resource_path(), adjusted_img_size()
├── exceptions.py           # Custom error types
├── canvas_calibration.py   # Zoom detection via dot measurement
├── palette_generator.py    # Color analysis + palette generation
├── ui/
│   ├── window.py           # Main Tkinter GUI (Notebook tabs + panel wiring)
│   ├── config_manager.py   # ConfigManager — config.json I/O (batch mode)
│   ├── thread_manager.py   # ThreadManager/ThreadJob — background tasks
│   ├── settings_panel.py   # Settings tab
│   ├── image_panel.py      # Preview tab
│   ├── action_panel.py     # Actions tab
│   ├── status_bar.py       # Bottom status line
│   ├── setup.py            # Configuration wizard
│   ├── palette_window.py   # Palette generation UI
│   └── single_color_window.py  # Single Color config window
├── config.json             # All persisted settings
├── color_calibration.json  # Custom color RGB→screen map
└── cache/                  # Pre-computed image data
```

## Drawing Modes

| Mode | Description |
|------|-------------|
| **Slotted** | Fast per-color row segments. Good for simple images |
| **Layered** | Color-frequency sorted with stroke merging. Best quality |
| **Single Color** | For line art. Pick a background color to ignore (click your image). All other pixels get drawn. No palette clicking — you select your brush color manually. Tolerance slider controls how aggressively near-matches are ignored. |

## Single Color Mode Usage

1. Select "Single Color" from Draw Mode dropdown
2. Config window opens — **click on the image background** (the color to ignore)
3. Adjust **Tolerance** (higher = more aggressive removal)
4. Red overlay shows what will be drawn; transparent = ignored
5. Quick actions: White Background, Binarize, Black Background
6. Click **Confirm**, then **Start** drawing (bot won't touch palette colors)

## Path Optimization

- Toggle via **Minimize cursor jumps** checkbox in the Settings tab
- Greedy nearest-neighbor reorder — each stroke starts near where the last ended
- Works with all drawing modes
- If enabled during Pre-compute, optimized order is cached — Start skips re-optimization

## Configuration

Everything in `config.json` (auto-saved):

| Section | Purpose |
|---------|---------|
| `drawing_settings` | delay, pixel_size, precision, jump_delay, jump_threshold |
| `drawing_options` | ignore_white_pixels, use_custom_colors |
| `path_optimization` | Enable stroke reordering (default: true) |
| `pause_key` | Pause/resume key |
| `skip_first_color` | Skip first palette color |
| `calibration_settings` | step_size |
| Palette/Canvas/Custom Colors | Tool coordinates & grid config |
| New Layer/Color Button/Color Button Okay | Optional tools with modifier keys |
| `MSPaint Mode` | Double-click on palette |
| `color_preview_spot` | Calibration preview location |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Drawing not starting | Run Setup first (palette + canvas required) |
| Wrong colors | Run color calibration or check custom colors |
| Pre-compute fails | Canvas must be initialized |
| App frozen | Press **ESC** to stop |
| Single Color draws nothing | Configure it via the popup window |
| Palette still clicking in Single Color | Bug — ensure `single_color_mode_active` flag is set |
| Large cursor jumps | Enable **Minimize cursor jumps** checkbox |
