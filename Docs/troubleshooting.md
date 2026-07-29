# Pyaint Troubleshooting Guide

## Drawing not starting
- **Check**: Palette and Canvas must be initialized (Setup → Initialize for each)
- **Check**: An image must be loaded in the preview panel

## Colors incorrect / wrong color selected
- Run Setup and verify palette colors are correctly captured
- Increase **Precision** setting for better color matching
- Run **Color Calibration** for custom color accuracy
- Verify valid positions include all needed palette colors
- Check that manual center points (if set) are accurate

## Palette not clicking correct colors
- Re-run Setup for the Palette tool
- Check that rows/cols match your actual palette layout
- Use Manual Color Selection to mark invalid cells
- Re-pick center points if using manual centers

## Custom colors not working
- Ensure Custom Colors box is configured in Setup
- Verify **Use Custom Colors** checkbox is enabled
- Run **Color Calibration** for best results

## Single Color mode not drawing
- Select "Single Color" from Draw Mode dropdown
- Configure it — click on your image background in the popup window
- Click **Confirm** before hitting Start
- The bot does NOT click palette colors in this mode — set your brush manually

## Slow drawing performance
- Increase **Pixel Size** (less detail, faster)
- Enable **Ignore White Pixels** for white-background images
- Use **Slotted** instead of **Layered** mode
- Disable **Use Custom Colors** if not needed

## Large cursor jumps during drawing
- Enable **Minimize cursor jumps** checkbox in Control Panel
- Increase **Jump Delay** to add more pause on jumps
- The path optimization reorders strokes to minimize jumps

## App unresponsive / frozen
- Press **ESC** to stop any running operation
- Increase **Delay** setting (0.3+ for slow systems)
- If truly frozen, close and restart

## Pre-compute fails
- Canvas must be initialized before pre-computing
- Ensure the image file is valid

## Drawing has gaps
- Decrease **Pixel Size** for more coverage
- Disable **Ignore White Pixels** if white areas should be drawn

## Calibration fails
- Ensure Custom Colors and Color Preview Spot are configured
- Set Calibration Step Size (default: 2, try 3-5 if calibration hangs)
- Make sure your drawing app doesn't block mouse input

## Palette / Canvas initialization fails
- Click EXACTLY on the corners, not near them
- Ensure the tool area is visible on screen
- Use primary monitor if using multiple displays

## Error Messages

| Message | Cause | Fix |
|---------|-------|-----|
| "Palette not initialized" | Palette not configured | Run Setup → Initialize Palette |
| "Canvas not initialized" | Canvas not configured | Run Setup → Initialize Canvas |
| "Custom colors not initialized" | Custom Colors not configured but checkbox enabled | Initialize Custom Colors or disable checkbox |
| "No valid colors selected" | All palette cells marked invalid | In Manual Color Selection, mark at least one green |
| "Config file missing or invalid" | Corrupt config | App uses defaults — re-run Setup |
| "Color calibration not found" | No color_calibration.json | Run Calibration |
