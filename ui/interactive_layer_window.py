"""
Interactive Layer Controller

Click-to-pick drawing controller. User clicks on the image to select a color,
adjusts flatness and stroke mode, then draws that layer. No auto-cycle.
Positioned to the left of the canvas area with an overlay on the canvas.
"""

import os
import tempfile
import time
import utils
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from bot import Palette


class InteractiveLayerController:
    """Controller for click-to-pick interactive drawing."""

    def __init__(self, parent, bot, image_path, draw_options, draw_mode):
        self.parent = parent
        self.bot = bot
        self.image_path = image_path
        self.draw_options = draw_options
        self.draw_mode = draw_mode

        self.source_color = None  # Color user clicked on image
        self.drawn_color = None   # Palette-mapped version of source
        self.flatness = 16
        self.overlay_window = None

        # Load image
        try:
            self._img_pil = Image.open(image_path).convert('RGB')
        except Exception:
            self._img_pil = Image.new('RGB', (400, 300), (200, 200, 200))

        # Create controller window
        self.window = tk.Toplevel(parent)
        self.window.title("Layer Controller — click image to pick color")
        self.window.attributes('-topmost', True)
        self.window.resizable(True, True)
        self.window.geometry("600x550")

        pad = {'padx': 10, 'pady': 5}

        # --- Image preview (click to pick) ---
        img_frame = ttk.LabelFrame(self.window, text="Click on the image to pick a color to draw", padding="5")
        img_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        self._img_canvas = tk.Canvas(img_frame, cursor="crosshair", bg="#555", height=250)
        self._img_canvas.pack(fill=tk.BOTH, expand=True)
        self._img_canvas.bind("<Button-1>", self._on_image_click)
        self._img_canvas.bind("<Configure>", lambda e: self._show_image())
        self._img_canvas.bind("<MouseWheel>", lambda e: self._on_mousewheel(e))
        # Linux scroll bindings
        self._img_canvas.bind("<Button-4>", lambda e: self._on_mousewheel_scroll(1))
        self._img_canvas.bind("<Button-5>", lambda e: self._on_mousewheel_scroll(-1))
        # Shift+drag pan support
        self._img_canvas.bind("<Shift-ButtonPress-1>", self._on_pan_start)
        self._img_canvas.bind("<Shift-B1-Motion>", self._on_pan_drag)
        self._pan_x = 0
        self._pan_y = 0
        self._canvas_img_w = 0
        self._canvas_img_h = 0
        self._zoom = 1.0

        # --- Controls ---
        ctrl_frame = ttk.Frame(self.window)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)

        # Color swatch
        color_row = ttk.Frame(ctrl_frame)
        color_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(color_row, text="Selected:", font=("", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self._color_swatch = tk.Canvas(color_row, width=40, height=25, bg="#ccc",
                                        highlightthickness=1)
        self._color_swatch.pack(side=tk.LEFT)
        self._color_label = ttk.Label(color_row, text="(click image)")
        self._color_label.pack(side=tk.LEFT, padx=5)

        # Flatness entry + Apply
        flat_row = ttk.Frame(ctrl_frame)
        flat_row.pack(fill=tk.X, pady=2)
        ttk.Label(flat_row, text="Flatness:", font=("", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self._flat_var = tk.StringVar(value=str(self.flatness))
        self._flat_entry = ttk.Entry(flat_row, textvariable=self._flat_var, width=6)
        self._flat_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(flat_row, text="Apply", command=self._on_flat_apply).pack(side=tk.LEFT)
        self._flat_entry.bind('<Return>', lambda e: self._on_flat_apply())

        # Stroke mode
        mode_row = ttk.Frame(ctrl_frame)
        mode_row.pack(fill=tk.X, pady=5)
        ttk.Label(mode_row, text="Stroke:", font=("", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self._mode_var = tk.StringVar(value="path")
        ttk.Radiobutton(mode_row, text="Raster", variable=self._mode_var,
                        value="raster", command=self._update_overlay).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_row, text="Path", variable=self._mode_var,
                        value="path", command=self._update_overlay).pack(side=tk.LEFT, padx=5)

        # Multi-color vs Strongest mode
        self._multi_color_var = tk.IntVar(value=1)
        self._multi_color_cb = ttk.Checkbutton(ctrl_frame, text="Multi Color Mode",
                                                variable=self._multi_color_var)
        self._multi_color_cb.pack(anchor="w", padx=10, pady=2)

        # Show Overlay toggle
        self._overlay_var = tk.IntVar(value=1)
        self._overlay_cb = ttk.Checkbutton(ctrl_frame, text="Show Overlay",
                                            variable=self._overlay_var, command=self._on_overlay_toggle)
        self._overlay_cb.pack(side=tk.LEFT, padx=10)

        # Zoom controls
        zoom_row = ttk.Frame(ctrl_frame)
        zoom_row.pack(fill=tk.X, pady=2)
        ttk.Label(zoom_row, text="Zoom:", font=("", 9)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(zoom_row, text="+", width=3, command=self._zoom_in).pack(side=tk.LEFT)
        ttk.Button(zoom_row, text="-", width=3, command=self._zoom_out).pack(side=tk.LEFT)
        self._zoom_label = ttk.Label(zoom_row, text="100%")
        self._zoom_label.pack(side=tk.LEFT, padx=5)

        # --- Action buttons ---
        btn_row = ttk.Frame(self.window)
        btn_row.pack(fill=tk.X, padx=10, pady=(5, 10))

        self._status_label = ttk.Label(btn_row, text="Click image to select a color")
        self._status_label.pack(side=tk.LEFT)

        ttk.Button(btn_row, text="Draw (Y)", command=self._draw_layer).pack(side=tk.RIGHT, padx=3)
        ttk.Button(btn_row, text="Draw Current", command=self._draw_current_color).pack(side=tk.RIGHT, padx=3)
        ttk.Button(btn_row, text="Clear", command=self._clear_color).pack(side=tk.RIGHT, padx=3)

        # Keyboard bindings
        self.window.bind('<y>', lambda e: self._draw_layer())
        self.window.bind('<Y>', lambda e: self._draw_layer())
        self.window.bind('<Escape>', lambda e: self._finish())
        self.window.protocol('WM_DELETE_WINDOW', self._finish)

        # Position to left of canvas
        self._position_window()

        # Initial image display
        self.window.after(100, self._show_image)

    def _get_drawn_color(self, color):
        """Return the actual color that will appear in the cmap."""
        if self.draw_options & self.bot.USE_CUSTOM_COLORS:
            interval = max((1 - self.bot.settings[self.bot.ACCURACY]) * 255, 1)
            r = min(int(round(color[0] / interval) * interval), 255)
            g = min(int(round(color[1] / interval) * interval), 255)
            b = min(int(round(color[2] / interval) * interval), 255)
            return (r, g, b)
        if self.bot._palette:
            return self.bot._palette.nearest_color(color)
        return color

    # --- Image display ---
    def _position_window(self):
        """Position controller to the left of the canvas."""
        canvas = self.bot._canvas
        if canvas:
            cx, cy, cw, ch = canvas
            self.window.geometry(f"+{max(0, cx - 620)}+{cy}")
        else:
            self.window.geometry("+10+200")

    def _show_image(self):
        self._img_canvas.update_idletasks()
        cw = max(self._img_canvas.winfo_width(), 100)
        ch = max(self._img_canvas.winfo_height(), 100)
        if cw <= 0 or ch <= 0:
            return
        ratio = min(cw / self._img_pil.width, ch / self._img_pil.height) * self._zoom
        self._canvas_img_w = int(self._img_pil.width * ratio)
        self._canvas_img_h = int(self._img_pil.height * ratio)
        if self._canvas_img_w <= 0 or self._canvas_img_h <= 0:
            return
        if hasattr(self, '_canvas_img_id'):
            self._img_canvas.delete(self._canvas_img_id)
        self._base_tk = ImageTk.PhotoImage(self._img_pil.resize((self._canvas_img_w, self._canvas_img_h)))
        self._canvas_img_id = self._img_canvas.create_image(0, 0, anchor=tk.NW, image=self._base_tk)
        self._img_canvas.configure(scrollregion=(0, 0, self._canvas_img_w, self._canvas_img_h))

    def _zoom_in(self):
        self._zoom = min(self._zoom * 1.25, 8.0)
        self._show_image()
        self._zoom_label.configure(text=f"{int(self._zoom * 100)}%")

    def _zoom_out(self):
        self._zoom = max(self._zoom / 1.25, 0.25)
        self._show_image()
        self._zoom_label.configure(text=f"{int(self._zoom * 100)}%")

    def _on_mousewheel(self, event):
        if event.state & 0x0001:  # Shift held
            if event.delta > 0:
                self._zoom_in()
            else:
                self._zoom_out()
        else:
            pass  # Regular scroll does nothing (no zoom without shift)

    def _on_mousewheel_scroll(self, direction):
        """Linux scroll handler (Button-4/Button-5)."""
        if direction > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _on_pan_start(self, event):
        self._img_canvas.scan_mark(event.x, event.y)

    def _on_pan_drag(self, event):
        self._img_canvas.scan_dragto(event.x, event.y, gain=1)

    # --- Color picking ---
    def _on_image_click(self, event):
        if event.state & 0x0001:  # Shift held — this is a pan, not a pick
            return
        if self._canvas_img_w <= 0:
            return
        # Use canvasx/canvasy to account for pan offset
        cx = self._img_canvas.canvasx(event.x)
        cy = self._img_canvas.canvasy(event.y)
        ix = min(int(cx * self._img_pil.width / self._canvas_img_w), self._img_pil.width - 1)
        iy = min(int(cy * self._img_pil.height / self._canvas_img_h), self._img_pil.height - 1)
        if ix < 0 or iy < 0:
            return
        self.source_color = self._img_pil.getpixel((ix, iy))
        self.drawn_color = self._get_drawn_color(self.source_color)
        # Debug: log click coords
        print(f"[Interactive] Click: canvas=({event.x:.0f},{event.y:.0f}) → scroll=({cx:.0f},{cy:.0f}) → pixel=({ix},{iy}) → {self.source_color}")
        # Display source color in swatch (what user clicked), show drawn color in label
        hexcol = '#%02x%02x%02x' % self.source_color
        self._color_swatch.configure(bg=hexcol)
        if self.source_color != self.drawn_color:
            self._color_label.configure(text=f"RGB {self.source_color} → draws as {self.drawn_color}")
        else:
            self._color_label.configure(text=f"RGB {self.source_color}")
        self._status_label.configure(text=f"Color selected — adjust flatness, then click Draw")
        self._update_overlay()

    def _clear_color(self):
        self.source_color = None
        self.drawn_color = None
        self._color_swatch.configure(bg="#ccc")
        self._color_label.configure(text="(click image)")
        self._status_label.configure(text="Click image to select a color")
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None

    # --- Overlay ---
    def _update_overlay(self):
        if not self._overlay_var.get():
            return
        if self.source_color is None:
            return
        try:
            overlay = self.bot.generate_layer_overlay(self.image_path, self.source_color, self.flatness)
        except Exception:
            return

        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None

        canvas = self.bot._canvas
        if not canvas:
            return
        cx, cy, cw, ch = canvas

        self.overlay_window = tk.Toplevel(self.window)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.overrideredirect(True)
        self.overlay_window.wm_attributes('-transparentcolor', 'magenta')
        self.overlay_window.geometry(f"{cw}x{ch}+{cx}+{cy}")
        self.overlay_window.lift()

        overlay_resized = overlay.resize((cw, ch), Image.NEAREST)
        self._overlay_tk = ImageTk.PhotoImage(overlay_resized)
        ov_canvas = tk.Canvas(self.overlay_window, width=cw, height=ch,
                               highlightthickness=0, bg='magenta')
        ov_canvas.pack()
        ov_canvas.create_image(0, 0, anchor=tk.NW, image=self._overlay_tk)

    def _on_overlay_toggle(self):
        if not self._overlay_var.get():
            if self.overlay_window:
                self.overlay_window.destroy()
                self.overlay_window = None
        else:
            self._update_overlay()

    def _on_flat_apply(self):
        try:
            self.flatness = int(self._flat_var.get())
        except ValueError:
            self._flat_var.set(str(self.flatness))
            return
        self.flatness = max(0, min(128, self.flatness))
        self._flat_var.set(str(self.flatness))
        self._update_overlay()

    # --- Drawing ---
    def _draw_current_color(self):
        """Draw using the currently selected brush color — skip palette clicking."""
        self.bot.single_color_mode_active = True
        try:
            self._draw_layer()
        finally:
            self.bot.single_color_mode_active = False

    def _draw_layer(self):
        if self.source_color is None:
            self._status_label.configure(text="Click image first to pick a color")
            return
        # Always read flatness from the entry field (not cached value)
        try:
            self.flatness = int(self._flat_var.get())
        except ValueError:
            self.flatness = 16
        self.flatness = max(0, min(128, self.flatness))
        self._flat_var.set(str(self.flatness))

        color = self.source_color
        mapped_color = self.drawn_color

        # Close overlay
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None

        # Process the full image, then filter strokes to only matching pixels
        print(f"[Interactive] Drawing: {color} → {mapped_color} (flatness={self.flatness})")
        try:
            cmap = self.bot.process(self.image_path, flags=self.draw_options, mode=self.draw_mode)
        except Exception as e:
            print(f"[Interactive] Process failed: {e}")
            return

        # Post-process: keep only strokes whose original pixel matches the clicked color
        tol_sq = self.flatness ** 2
        orig_pix = self._img_pil.load()
        img_w, img_h = self._img_pil.size

        # Calculate canvas-to-image coordinate mapping
        try:
            cx, cy, cw, ch = self.bot._canvas
        except:
            print("[Interactive] Canvas not initialized")
            return
        step = int(self.bot.settings[self.bot.STEP])
        scale = self.bot.canvas_calibration.get('scale_factor', 1.0)
        if scale != 1.0:
            step = int(round(step * scale))
        tw, th = tuple(int(p // step) for p in utils.adjusted_img_size(self._img_pil, (cw, ch)))
        x_off = cx + (cw - tw * step) // 2
        y_off = cy + (ch - th * step) // 2

        # Filter each color's strokes
        total_before = 0
        filtered = {}
        for col_key, lines in cmap.items():
            kept = []
            for start, end in lines:
                # Map canvas start position back to image pixel
                ix = int((start[0] - x_off) / step)
                iy = int((start[1] - y_off) / step)
                if 0 <= ix < tw and 0 <= iy < th:
                    # Map to original image coords
                    ox = int(ix * self._img_pil.width / tw)
                    oy = int(iy * self._img_pil.height / th)
                    ox = min(ox, img_w - 1)
                    oy = min(oy, img_h - 1)
                    pixel = orig_pix[ox, oy]
                    dist = (pixel[0] - color[0]) ** 2 + (pixel[1] - color[1]) ** 2 + (pixel[2] - color[2]) ** 2
                    if dist <= tol_sq:
                        kept.append((start, end))
                total_before += 1
            if kept:
                filtered[col_key] = kept

        if not filtered or total_before == 0:
            print("[Interactive] No matching pixels")
            self._status_label.configure(text="No matching pixels — try higher flatness")
            return

        cmap = filtered
        print(f"[Interactive] Filtered: kept {sum(len(v) for v in cmap.values())} of {total_before} strokes")

        # If Multi Color Mode is off, keep only the most frequent color
        if not self._multi_color_var.get() and cmap:
            # Find the color with the most strokes
            best_color = max(cmap.keys(), key=lambda k: len(cmap[k]))
            cmap = {best_color: cmap[best_color]}
            print(f"[Interactive] Strongest color only: {best_color} with {len(cmap[best_color])} strokes")

        if not cmap:
            print(f"[Interactive] No matching pixels")
            self._status_label.configure(text="No matching pixels — try higher flatness")
            return

        if self._mode_var.get() == "path":
            cmap = self.bot.optimize_stroke_order(cmap)

        # Warn if flatness is too broad
        total_strokes = sum(len(lines) for lines in cmap.values())
        if total_strokes > 5000:
            self._status_label.configure(
                text=f"Warning: {total_strokes} strokes — flatness is very broad. Drawing anyway..."
            )
        else:
            self._status_label.configure(text=f"Drawing {total_strokes} strokes...")

        self.bot.terminate = False
        self.bot.paused = False
        self.bot.drawing = False
        self.bot.draw_state = {
            'color_idx': 0, 'line_idx': 0, 'segment_idx': 0,
            'current_color': None, 'was_paused': False
        }
        # Bypass skip_first_color — user explicitly chose this color
        saved_skip = self.bot.skip_first_color
        self.bot.skip_first_color = False
        try:
            result = self.bot.draw(cmap)
        finally:
            self.bot.skip_first_color = saved_skip
        print(f"[Interactive] Draw result: {result}")
        self._status_label.configure(text=f"Drawn — click new color or Draw again")

    # --- Cleanup ---
    def _finish(self):
        self.bot.terminate = True
        self.bot.color_remap_enabled = False
        self.bot.color_remap_entries = []
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
        self.window.destroy()
