# Pyaint Configuration Guide

Settings are stored in `config.json` in the project root. Auto-saved on changes.

## Drawing Settings

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| Delay | 0.01-10.0s | 0.1 | Duration of each brush stroke |
| Pixel Size | 3-50 | 12 | Step between sample pixels (lower = more detail) |
| Precision | 0.0-1.0 | 0.9 | Color quantization precision (custom colors only) |
| Jump Delay | 0.0-2.0s | 0.5 | Delay when cursor jumps > threshold |
| Jump Threshold | 1-100px | 5 | Distance that triggers jump delay |

## Config File Structure

```json
{
  "drawing_settings": {"delay": 0.1, "pixel_size": 12, "precision": 0.9, "jump_delay": 0.5, "jump_threshold": 5},
  "drawing_options": {"ignore_white_pixels": true, "use_custom_colors": false},
  "path_optimization": true,
  "pause_key": "p",
  "skip_first_color": false,
  "calibration_settings": {"step_size": 2},
  "Palette": {"status": true, "box": [x1,y1,x2,y2], "rows": 6, "cols": 8, "color_coords": {...}, "valid_positions": [...], "manual_centers": {...}},
  "Canvas": {"status": true, "box": [x1,y1,x2,y2], "calibration": {"scale_factor": 1.0, ...}},
  "Custom Colors": {"status": true, "box": [x1,y1,x2,y2]},
  "New Layer": {"status": true, "coords": [x,y], "enabled": false, "modifiers": {...}},
  "Color Button": {"status": true, "coords": [x,y], "enabled": false, "delay": 0.1, "modifiers": {...}},
  "Color Button Okay": {"status": true, "coords": [x,y], "enabled": false, "delay": 0.1, "modifiers": {...}},
  "MSPaint Mode": {"enabled": false, "delay": 0.5},
  "color_preview_spot": {"name": "Color Preview Spot", "coords": [x,y], ...}
}
```

## Tool Configuration

Each tool has fields: `status` (initialized?), `box`/`coords` (screen region), optional `modifiers` (ctrl/alt/shift), optional `enabled` toggle, optional `delay`.

### Essential Tools

- **Palette**: Grid layout with rows/cols, color_coords mapping RGB→screen position, valid_positions for enabling/disabling cells, manual_centers for precise placement
- **Canvas**: Drawing area coordinates. Optional `calibration` object with `scale_factor` for zoom compensation

### Optional Tools

- **Custom Colors**: Spectrum area box. Must be configured before enabling "Use Custom Colors"
- **New Layer**: Single-click tool. Click the "new layer" button in your app
- **Color Button**: Click a color picker button before palette selection. Configurable delay
- **Color Button Okay**: Click a confirmation button after color selection
- **MSPaint Mode**: Double-click palette instead of single click, with configurable delay
- **color_preview_spot**: Location where your drawing app shows the selected color (used for calibration)

## Calibration Settings

`calibration_settings.step_size` (1-10, default: 2): Pixel step when scanning the color spectrum. Lower = more accurate but slower.

## File Management

| File | Purpose |
|------|---------|
| `config.json` | All settings and tool configurations (auto-saved) |
| `color_calibration.json` | Custom color RGB→position map (created by "Run Calibration") |
| `palette_extraction_temp.json` | Temporary file for interactive palette extraction |
