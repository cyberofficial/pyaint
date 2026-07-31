"""
Color Flattening Window

Allows user to import a palette file and map image colors to flat target colors.
Each target color has a source (sampled from the image) and tolerance.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk


class FlattenColorsWindow:
    """Window for flattening image colors to imported palette targets."""

    def __init__(self, parent, bot, image_path):
        self.parent = parent
        self.bot = bot
        self.image_path = image_path

        # Per-target mappings: list of {'target': (r,g,b), 'source': (r,g,b)|None, 'tolerance': int}
        self.mappings = []
        self._selected_idx = -1
        self._canvas_img_w = 0
        self._canvas_img_h = 0
        self._zoom = 1.0
        self._tol_labels = {}  # idx -> tolerance value label for in-place update

        self.window = tk.Toplevel(parent)
        self.window.title("Flatten Colors")
        self.window.geometry("1050x700")
        self.window.resizable(True, True)

        # Load image
        try:
            self._img_pil = Image.open(image_path).convert('RGB')
        except Exception:
            self._img_pil = Image.new('RGB', (400, 300), (200, 200, 200))

        # --- Top bar ---
        top_bar = ttk.Frame(self.window)
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 0))
        ttk.Button(top_bar, text="Import Palette", command=self._import_palette).pack(side=tk.LEFT, padx=(0, 10))
        self._zoom_label = ttk.Label(top_bar, text="100%", width=6)
        self._zoom_label.pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Button(top_bar, text="+", width=3, command=self._zoom_in).pack(side=tk.RIGHT)
        ttk.Button(top_bar, text="-", width=3, command=self._zoom_out).pack(side=tk.RIGHT, padx=(0, 5))
        self._status_label = ttk.Label(top_bar, text="No palette loaded — import one to start")
        self._status_label.pack(side=tk.LEFT)

        # --- Main content ---
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: image pane
        left_frame = ttk.LabelFrame(main_frame, text="Click to sample source color", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._img_canvas = tk.Canvas(left_frame, cursor="crosshair", bg="#555")
        self._img_canvas.pack(fill=tk.BOTH, expand=True)
        self._img_canvas.bind("<Configure>", lambda e: self._show_image())
        self._img_canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        # Pan/drag support
        self._img_canvas.bind("<ButtonPress-1>", self._on_press)
        self._img_canvas.bind("<B1-Motion>", self._on_drag)
        self._img_canvas.bind("<ButtonRelease-1>", self._on_release)
        self._pan_start_x = 0
        self._pan_start_y = 0
        self._is_dragging = False
        self._adding_target = False  # When True, image clicks add new target colors
        # Linux scroll bindings
        self._img_canvas.bind("<Button-4>", lambda e: self._zoom_in())
        self._img_canvas.bind("<Button-5>", lambda e: self._zoom_out())

        # Right: mappings list (scrollable)
        right_frame = ttk.LabelFrame(main_frame, text="Target Colors", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        ttk.Label(right_frame, text="Select a target below, then click the image",
                  wraplength=320, font=("", 9, "italic")).pack(pady=(0, 5))

        self._list_canvas = tk.Canvas(right_frame, width=340)
        self._list_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self._list_canvas.yview)
        self._list_frame = ttk.Frame(self._list_canvas)
        self._list_frame.bind("<Configure>",
                              lambda e: self._list_canvas.configure(scrollregion=self._list_canvas.bbox("all")))
        self._list_canvas.create_window((0, 0), window=self._list_frame, anchor=tk.NW)
        self._list_canvas.configure(yscrollcommand=self._list_scroll.set)
        self._list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Bottom buttons ---
        bottom_bar = ttk.Frame(self.window)
        bottom_bar.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(bottom_bar, text="Clear All Mappings", command=self._clear_all).pack(side=tk.LEFT)
        ttk.Button(bottom_bar, text="Add Target", command=self._start_add_target).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(bottom_bar, text="Export CSS", command=self._export_css).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(bottom_bar, text="Preview Flattened", command=self._preview).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(bottom_bar, text="Apply", command=self._on_apply).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bottom_bar, text="Cancel", command=self._on_close).pack(side=tk.RIGHT)

        # Initial image display
        self.window.after(100, self._show_image)

    # --- Image display ---
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
        # Remove previous image to prevent stacking
        if hasattr(self, '_canvas_img_id'):
            self._img_canvas.delete(self._canvas_img_id)
        self._base_tk = ImageTk.PhotoImage(self._img_pil.resize((self._canvas_img_w, self._canvas_img_h)))
        self._canvas_img_id = self._img_canvas.create_image(0, 0, anchor=tk.NW, image=self._base_tk)
        self._img_canvas.configure(scrollregion=(0, 0, self._canvas_img_w, self._canvas_img_h))
        self._zoom_label.configure(text=f"{int(self._zoom * 100)}%")

    def _zoom_in(self):
        self._zoom = min(self._zoom * 1.25, 8.0)
        self._show_image()

    def _zoom_out(self):
        self._zoom = max(self._zoom / 1.25, 0.25)
        self._show_image()

    def _on_mousewheel(self, event):
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _on_press(self, event):
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self._is_dragging = False
        self._img_canvas.scan_mark(event.x, event.y)

    def _on_drag(self, event):
        dx = abs(event.x - self._pan_start_x)
        dy = abs(event.y - self._pan_start_y)
        if dx > 3 or dy > 3:
            self._is_dragging = True
        self._img_canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_release(self, event):
        if self._is_dragging:
            return  # Was a pan, not a click
        if self._canvas_img_w <= 0:
            return
        # Convert window coords to canvas coords (accounts for scroll/pan offset)
        cx = self._img_canvas.canvasx(event.x)
        cy = self._img_canvas.canvasy(event.y)
        ix = min(int(cx * self._img_pil.width / self._canvas_img_w), self._img_pil.width - 1)
        iy = min(int(cy * self._img_pil.height / self._canvas_img_h), self._img_pil.height - 1)
        if ix < 0 or iy < 0:
            return
        pixel = self._img_pil.getpixel((ix, iy))

        if self._adding_target:
            # Add pixel as new target+source
            self.mappings.append({'target': pixel, 'source': pixel, 'tolerance': 16})
            self._adding_target = False
            self._draw_mapping_list()
            self._status_label.configure(text=f"Added new target color #{len(self.mappings)}")
            return

        if self._selected_idx < 0:
            self._status_label.configure(text="Select a target color first (right panel)")
            return
        self.mappings[self._selected_idx]['source'] = pixel
        self._draw_mapping_list()
        self._status_label.configure(text=f"Source set for target #{self._selected_idx + 1}")

    def _start_add_target(self):
        self._adding_target = True
        self._selected_idx = -1
        self._draw_mapping_list()
        self._status_label.configure(text="Click on the image to add its color as a new target")

    def _export_css(self):
        if not self.mappings:
            self._status_label.configure(text="No targets to export")
            return
        path = filedialog.asksaveasfilename(
            title="Export Palette CSS",
            defaultextension=".css",
            filetypes=[("CSS File", "*.css"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, 'w') as f:
                f.write("/* Generated with Pyaint Palette Export */\n")
                for i, m in enumerate(self.mappings):
                    r, g, b = m['target']
                    f.write(f".{i} {{ color: rgb({r}, {g}, {b}); }}\n")
            self._status_label.configure(text=f"Exported {len(self.mappings)} colors to {os.path.basename(path)}")
        except Exception as e:
            self._status_label.configure(text=f"Export failed: {e}")

    # --- Palette import ---
    def _import_palette(self):
        path = filedialog.askopenfilename(
            title="Import Palette",
            filetypes=[("GIMP CSS", "*.css"), ("GIMP Palette", "*.gpl"), ("All Files", "*.*")]
        )
        if not path:
            return

        colors = []
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # GIMP CSS: /* RGB(r, g, b) */
                    if '/*' in line and 'RGB(' in line:
                        try:
                            rgb_part = line[line.index('RGB('):line.index(')') + 1]
                            parts = rgb_part[4:-1].split(',')
                            r, g, b = int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip())
                            colors.append((r, g, b))
                        except (ValueError, IndexError):
                            pass
                    # CSS rgb() format: rgb(r, g, b) or .N { color: rgb(r, g, b); }
                    elif 'rgb(' in line:
                        try:
                            start = line.index('rgb(') + 4
                            end = line.index(')', start)
                            parts = line[start:end].split(',')
                            if len(parts) == 3:
                                r = int(parts[0].strip())
                                g = int(parts[1].strip())
                                b = int(parts[2].strip())
                                colors.append((r, g, b))
                        except (ValueError, IndexError):
                            pass
                    # GIMP .gpl: R G B Name
                    elif line and line[0].isdigit():
                        try:
                            parts = line.split()
                            if len(parts) >= 3:
                                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                                colors.append((r, g, b))
                        except (ValueError, IndexError):
                            pass
                    # Simple hex
                    elif line.startswith('#') and len(line) >= 7:
                        try:
                            r, g, b = int(line[1:3], 16), int(line[3:5], 16), int(line[5:7], 16)
                            colors.append((r, g, b))
                        except ValueError:
                            pass
        except Exception as e:
            messagebox.showerror("Import Error", str(e))
            return

        if not colors:
            messagebox.showwarning("Import", "No colors found in file.")
            return

        self.mappings = [{'target': c, 'source': None, 'tolerance': 16} for c in colors]
        # Auto-map: find closest image color for each palette target
        self._auto_map_sources()
        self._status_label.configure(text=f"{len(colors)} colors imported and auto-mapped. Adjust tolerances if needed.")
        self._selected_idx = -1
        self._adding_target = False
        self._draw_mapping_list()

    def _auto_map_sources(self):
        """For each palette target, find the closest color in the image as the source."""
        if not self.mappings:
            return
        # Downscale image for fast scanning
        w, h = self._img_pil.size
        scale = max(1, min(w, h) // 64)  # Sample at most 64px per dimension
        small = self._img_pil.resize((w // scale, h // scale), Image.NEAREST)
        pix = small.load()
        sw, sh = small.size

        # Pre-compute RGB values of sampled pixels
        samples = []
        for y in range(sh):
            for x in range(sw):
                samples.append(pix[x, y])

        # For each target, find the closest sample
        for idx, m in enumerate(self.mappings):
            target = m['target']
            best_dist = float('inf')
            best_color = None
            for s in samples:
                dr = target[0] - s[0]
                dg = target[1] - s[1]
                db = target[2] - s[2]
                d = dr * dr + dg * dg + db * db
                if d < best_dist:
                    best_dist = d
                    best_color = s
                if best_dist == 0:
                    break  # Exact match
            m['source'] = best_color
            # Auto-set tolerance based on how far the closest match is
            if best_color is not None:
                m['tolerance'] = max(8, min(48, int(best_dist ** 0.5 * 2)))

    # --- Mapping list UI ---
    def _draw_mapping_list(self):
        self._tol_labels.clear()
        for w in self._list_frame.winfo_children():
            w.destroy()

        if not self.mappings:
            ttk.Label(self._list_frame, text="No targets — import a palette first").pack(pady=20)
            return

        for i, m in enumerate(self.mappings):
            frame = tk.Frame(self._list_frame, bg="#f0f0f0" if i != self._selected_idx else "#c8d8f0",
                             highlightbackground="#aaa" if i != self._selected_idx else "#5588cc",
                             highlightthickness=2 if i == self._selected_idx else 1)
            frame.pack(fill=tk.X, pady=2, padx=2)

            ttk.Label(frame, text=f"#{i + 1}", font=("", 9, "bold"), width=4).pack(side=tk.LEFT, padx=(4, 2))

            # Target swatch
            target_hex = '#%02x%02x%02x' % m['target']
            target_cv = tk.Canvas(frame, width=28, height=28, bg=target_hex, highlightthickness=1)
            target_cv.pack(side=tk.LEFT, padx=(0, 4))

            ttk.Label(frame, text="←").pack(side=tk.LEFT)

            # Source swatch or placeholder
            if m['source']:
                src_hex = '#%02x%02x%02x' % m['source']
                src_label = tk.Label(frame, text="  ■  ", bg=src_hex, fg=src_hex, font=("", 8))
            else:
                src_label = tk.Label(frame, text="  ?  ", bg="#ddd", fg="#999", font=("", 8))
            src_label.pack(side=tk.LEFT, padx=(4, 4))

            # Tolerance slider
            tol_var = tk.IntVar(value=m['tolerance'])
            tol_var.trace_add('write', lambda *a, idx=i, v=tol_var: self._on_tol_change(idx, v.get()))
            ttk.Label(frame, text="Tol:", font=("", 7)).pack(side=tk.LEFT)
            ttk.Scale(frame, from_=0, to=128, variable=tol_var, orient=tk.HORIZONTAL,
                      length=80).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 4))
            tol_label = ttk.Label(frame, text=str(m['tolerance']), font=("", 8), width=4)
            tol_label.pack(side=tk.LEFT)
            self._tol_labels[i] = tol_label

            # Select / Remove buttons
            ttk.Button(frame, text="✕", width=3, command=lambda idx=i: self._remove_target(idx)).pack(side=tk.RIGHT, padx=1)
            ttk.Button(frame, text="Select", command=lambda idx=i: self._select_target(idx)).pack(side=tk.RIGHT, padx=4)

    def _select_target(self, idx):
        if idx == self._selected_idx:
            return  # Already selected, no need to redraw
        self._selected_idx = idx
        self._draw_mapping_list()

    def _remove_target(self, idx):
        if 0 <= idx < len(self.mappings):
            del self.mappings[idx]
            if not self.mappings:
                self._selected_idx = -1
            elif self._selected_idx >= len(self.mappings):
                self._selected_idx = max(0, len(self.mappings) - 1)
            self._draw_mapping_list()
            self._status_label.configure(text=f"Removed target #{idx + 1}")

    def _on_tol_change(self, idx, val):
        try:
            v = int(float(val))
            self.mappings[idx]['tolerance'] = v
            # Update label in-place instead of redrawing the whole list
            if idx in self._tol_labels:
                self._tol_labels[idx].configure(text=str(v))
        except (ValueError, IndexError):
            pass

    # --- Actions ---
    def _clear_all(self):
        for m in self.mappings:
            m['source'] = None
            m['tolerance'] = 16
        self._draw_mapping_list()
        self._status_label.configure(text="All source mappings cleared")

    def _preview(self):
        if not self.mappings or self._canvas_img_w <= 0:
            return
        preview = self._img_pil.copy()
        pix = preview.load()
        w, h = preview.size
        for y in range(h):
            for x in range(w):
                pixel = pix[x, y]
                best_dist = float('inf')
                best_target = None
                for m in self.mappings:
                    if m['source'] is None:
                        continue
                    dr = (pixel[0] - m['source'][0])
                    dg = (pixel[1] - m['source'][1])
                    db = (pixel[2] - m['source'][2])
                    dist_sq = dr * dr + dg * dg + db * db
                    if dist_sq <= m['tolerance'] ** 2 and dist_sq < best_dist:
                        best_dist = dist_sq
                        best_target = m['target']
                if best_target is not None:
                    pix[x, y] = best_target
        preview_tk = ImageTk.PhotoImage(preview.resize((self._canvas_img_w, self._canvas_img_h)))
        if hasattr(self, '_canvas_img_id'):
            self._img_canvas.delete(self._canvas_img_id)
        self._canvas_img_id = self._img_canvas.create_image(0, 0, anchor=tk.NW, image=preview_tk)
        self._preview_tk = preview_tk
        self._status_label.configure(text="Preview shown — adjusted pixels replaced with flat colors")

    def _on_apply(self):
        entries = []
        for m in self.mappings:
            if m['source'] is not None:
                entries.append(((m['source'], m['tolerance']), m['target']))
        self.bot.color_remap_entries = entries
        self.bot.color_remap_enabled = bool(entries)
        count = len(entries)
        self._status_label.configure(text=f"Applied {count} color mappings. Draw will use flat colors.")
        self.window.after(1500, self._on_close)

    def _on_close(self):
        self.window.destroy()
