"""
Single Color Mode Configuration Window

Allows user to pick a background/ignore color and tolerance,
with live preview of which pixels will be drawn.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


class SingleColorWindow:
    """Window for configuring Single Color drawing mode."""

    def __init__(self, parent, bot, image_path):
        self.parent = parent
        self.bot = bot
        self.image_path = image_path

        # Initialize from bot state if already configured
        if bot.single_color_configured:
            self.ignore_color = bot.single_color_ignore
            self.tolerance = bot.single_color_tolerance
        else:
            self.ignore_color = (255, 255, 255)  # default white
            self.tolerance = 16

        self.window = tk.Toplevel(parent)
        self.window.title("Single Color Mode - Pick Background to Ignore")
        self.window.geometry("960x700")
        self.window.resizable(True, True)

        # Top instruction label
        instr = ttk.Label(self.window, text="Click on the image below to pick the background color you want to IGNORE. "
                           "Adjust tolerance to catch near-matches. The red overlay shows what WILL be drawn.",
                           wraplength=900, font=("", 10, "bold"))
        instr.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Main content area
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- Left: Image with click-to-pick ---
        left_frame = ttk.LabelFrame(main_frame, text="Click to pick background color", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(left_frame, cursor="crosshair", bg="#333")
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.bind("<Button-1>", self._on_canvas_click)

        try:
            self._img_pil = Image.open(image_path).convert('RGB')
        except Exception:
            self._img_pil = Image.new('RGB', (400, 300), (200, 200, 200))

        self._canvas_img_w = 0
        self._canvas_img_h = 0
        self._pending_preview = False  # Track whether overlay needs to be drawn
        # Delay initial display until the window is mapped and measured
        self.window.after(100, self._resize_image)
        self._canvas.bind('<Configure>', lambda e: self._resize_image())

        # --- Right: Controls ---
        right_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Color pick info
        ttk.Label(right_frame, text="Background Color:", font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))
        color_row = ttk.Frame(right_frame)
        color_row.pack(anchor="w", pady=(0, 15))
        self._color_swatch = tk.Canvas(color_row, width=50, height=50, bg="#ffffff",
                                        highlightthickness=2, highlightbackground="#666")
        self._color_swatch.pack(side=tk.LEFT)
        self._color_label = ttk.Label(color_row, text="R: 255\nG: 255\nB: 255",
                                      font=("Consolas", 9), justify=tk.LEFT)
        self._color_label.pack(side=tk.LEFT, padx=(10, 0))

        # Tolerance slider
        ttk.Label(right_frame, text="Tolerance:", font=("", 10, "bold")).pack(anchor="w")
        self._tol_var = tk.IntVar(value=self.tolerance)
        self._tol_scale = ttk.Scale(right_frame, from_=0, to=128, variable=self._tol_var,
                                     orient=tk.HORIZONTAL, command=self._on_tolerance_change)
        self._tol_scale.pack(fill=tk.X, pady=5)
        self._tol_label = ttk.Label(right_frame, text=f"Value: {self.tolerance}")
        self._tol_label.pack(anchor="w")
        ttk.Label(right_frame, text="Higher = more aggressive at removing near-background pixels",
                  font=("", 8), foreground="gray").pack(anchor="w", pady=(0, 10))

        # Quick actions
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(right_frame, text="Quick Actions:", font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        ttk.Button(right_frame, text="White Background", command=self._set_white_bg).pack(fill=tk.X, pady=2)
        ttk.Label(right_frame, text="Sets ignore to pure white (255,255,255)",
                  font=("", 8), foreground="gray").pack(anchor="w", pady=(0, 5))

        ttk.Button(right_frame, text="Binarize / High Contrast", command=self._set_binarize).pack(fill=tk.X, pady=2)
        ttk.Label(right_frame, text="Wider tolerance for near-white artifacts, ideal for scanned line art",
                  font=("", 8), foreground="gray").pack(anchor="w", pady=(0, 5))

        ttk.Button(right_frame, text="Black Background", command=self._set_black_bg).pack(fill=tk.X, pady=2)
        ttk.Label(right_frame, text="Sets ignore to pure black (0,0,0)",
                  font=("", 8), foreground="gray").pack(anchor="w", pady=(0, 10))

        # Pixel count info
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self._pixel_info = ttk.Label(right_frame, text="Pixels to draw: -\nTotal pixels: -",
                                      font=("", 9), justify=tk.LEFT)
        self._pixel_info.pack(anchor="w", pady=(0, 5))

        # Confirm / Cancel
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Confirm", style="Accent.TButton",
                   command=self._on_confirm).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT)

        # Force an initial preview
        self._update_preview()

    def _resize_image(self):
        """Recalculate image display dimensions to fit the canvas."""
        self._canvas.update_idletasks()
        cw = max(self._canvas.winfo_width(), 100)
        ch = max(self._canvas.winfo_height(), 100)
        if cw <= 0 or ch <= 0:
            return
        ratio = min(cw / self._img_pil.width, ch / self._img_pil.height)
        self._canvas_img_w = int(self._img_pil.width * ratio)
        self._canvas_img_h = int(self._img_pil.height * ratio)
        if self._canvas_img_w <= 0 or self._canvas_img_h <= 0:
            return
        self._draw_current_image()

    def _draw_current_image(self):
        """Draw the base image (with overlay if preview is active) at current canvas dimensions."""
        if self._pending_preview:
            # Draw with red overlay
            try:
                overlay = self.bot.generate_single_color_preview(
                    self.image_path, self.ignore_color, self.tolerance
                )
            except Exception:
                overlay = None
            if overlay is not None:
                base_rgba = self._img_pil.convert('RGBA')
                if overlay.size != base_rgba.size:
                    overlay = overlay.resize(base_rgba.size, Image.NEAREST)
                combined = base_rgba.copy()
                combined.paste(overlay, (0, 0), overlay)
                img_tk = ImageTk.PhotoImage(combined.resize((self._canvas_img_w, self._canvas_img_h)))
                self._preview_tk = img_tk
                self._canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
                return
        # Fall back to plain base image
        img_tk = ImageTk.PhotoImage(self._img_pil.resize((self._canvas_img_w, self._canvas_img_h)))
        self._base_tk = img_tk
        self._canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

    def _on_canvas_click(self, event):
        if self._canvas_img_w <= 0 or self._canvas_img_h <= 0:
            return
        # Map canvas coords to image coords
        ix = min(int(event.x * self._img_pil.width / self._canvas_img_w), self._img_pil.width - 1)
        iy = min(int(event.y * self._img_pil.height / self._canvas_img_h), self._img_pil.height - 1)
        if ix < 0 or iy < 0:
            return
        self.ignore_color = self._img_pil.getpixel((ix, iy))
        hexcol = '#%02x%02x%02x' % self.ignore_color
        self._color_swatch.configure(bg=hexcol)
        self._color_label.configure(text=f"R: {self.ignore_color[0]}\nG: {self.ignore_color[1]}\nB: {self.ignore_color[2]}")
        self._update_preview()

    def _on_tolerance_change(self, val):
        self.tolerance = int(float(val))
        self._tol_label.configure(text=f"Value: {self.tolerance}")
        self._update_preview()

    def _update_preview(self):
        """Draw red overlay on top of the base image showing which pixels will be drawn."""
        self._pending_preview = True
        if self._canvas_img_w > 0 and self._canvas_img_h > 0:
            self._draw_current_image()

        # Count non-ignored pixels (always recompute at full resolution)
        base_rgba = self._img_pil.convert('RGBA')
        w, h = base_rgba.size
        pix = base_rgba.load()
        tol_sq = self.tolerance ** 2
        pix = base_rgba.load()
        tol_sq = self.tolerance ** 2
        total = w * h
        drawn = 0
        for y in range(h):
            for x in range(w):
                r, g, b = pix[x, y][:3]
                if sum((s - q) ** 2 for s, q in zip((r, g, b), self.ignore_color)) > tol_sq:
                    drawn += 1
        pct = (drawn / total * 100) if total else 0
        self._pixel_info.configure(text=f"Pixels to draw: {drawn:,} of {total:,}\n({pct:.1f}%)")

    # --- Quick actions ---
    def _set_white_bg(self):
        self.ignore_color = (255, 255, 255)
        self._color_swatch.configure(bg='#ffffff')
        self._color_label.configure(text="R: 255\nG: 255\nB: 255")
        self._tol_var.set(16)
        self.tolerance = 16
        self._tol_label.configure(text="Value: 16")
        self._update_preview()

    def _set_binarize(self):
        self.ignore_color = (255, 255, 255)
        self._color_swatch.configure(bg='#ffffff')
        self._color_label.configure(text="R: 255\nG: 255\nB: 255")
        self._tol_var.set(64)
        self.tolerance = 64
        self._tol_label.configure(text="Value: 64")
        self._update_preview()

    def _set_black_bg(self):
        self.ignore_color = (0, 0, 0)
        self._color_swatch.configure(bg='#000000')
        self._color_label.configure(text="R: 0\nG: 0\nB: 0")
        self._tol_var.set(16)
        self.tolerance = 16
        self._tol_label.configure(text="Value: 16")
        self._update_preview()

    # --- Confirm / Cancel ---
    def _on_confirm(self):
        self.bot.single_color_ignore = self.ignore_color
        self.bot.single_color_tolerance = self.tolerance
        self.bot.single_color_configured = True
        self.window.destroy()

    def _on_cancel(self):
        self.window.destroy()
