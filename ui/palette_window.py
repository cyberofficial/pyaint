"""
Color Palette Generation Window

UI for generating and exporting color palettes from images.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Scrollbar, Canvas
from typing import List, Tuple, Optional
from palette_generator import ColorPaletteGenerator


class PaletteWindow:
    """Window for generating and exporting color palettes."""
    
    def __init__(self, parent: tk.Tk, image_path: str, bot):
        """
        Initialize palette window.
        
        Args:
            parent: Parent Tk window
            image_path: Path to image to analyze
            bot: Bot instance (for accessing ignore_white setting)
        """
        self.parent = parent
        self.image_path = image_path
        self.bot = bot
        
        # Initialize generator
        ignore_white = bool(bot.options & bot.IGNORE_WHITE)
        self.generator = ColorPaletteGenerator(image_path, ignore_white=ignore_white)
        
        # State
        self.current_palette_size = 16
        self.current_algorithm = "frequency"
        self.colors = []
        self.counts = []
        self.tie_resolved = {}
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Color Palette Generator")
        self.window.geometry("900x750")
        self.window.resizable(True, True)
        
        # Center window on screen
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 900) // 2
        y = (screen_height - 750) // 2
        self.window.geometry(f"900x750+{x}+{y}")
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Initialize UI
        self._init_ui()
        
        # Generate initial palette
        self._update_palette_preview()
    
    def _init_ui(self):
        """Initialize UI components."""
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title section
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            title_frame,
            text="Color Palette Generator",
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            title_frame,
            text=f"Image: {self.image_path}",
            font=("Arial", 10)
        ).pack(side=tk.RIGHT)
        
        # Controls section
        controls_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Palette size control
        size_frame = ttk.Frame(controls_frame)
        size_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(size_frame, text="Palette Size:").pack(side=tk.LEFT)
        
        self.size_var = tk.IntVar(value=self.current_palette_size)
        self.size_entry = ttk.Entry(size_frame, textvariable=self.size_var, width=10)
        self.size_entry.pack(side=tk.LEFT, padx=5)
        self.size_entry.bind('<Return>', self._on_size_change)
        self.size_entry.bind('<FocusOut>', self._on_size_change)
        
        ttk.Label(size_frame, text="(1-256 colors)").pack(side=tk.LEFT, padx=5)
        
        # Algorithm selection
        ttk.Label(size_frame, text="Algorithm:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.algorithm_var = tk.StringVar(value=self.current_algorithm)
        algorithm_combo = ttk.Combobox(
            size_frame,
            textvariable=self.algorithm_var,
            values=("frequency", "dominant_shades", "rare_shades"),
            state="readonly",
            width=15
        )
        algorithm_combo.pack(side=tk.LEFT)
        algorithm_combo.bind('<<ComboboxSelected>>', self._on_algorithm_change)
        
        # Buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.resolve_btn = ttk.Button(
            button_frame,
            text="Resolve Ties",
            command=self._resolve_ties_dialog,
            state=tk.DISABLED
        )
        self.resolve_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ttk.Button(
            button_frame,
            text="Export GIMP CSS",
            command=self._export_palette
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy
        ).pack(side=tk.RIGHT)
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Color Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Container for canvas and scrollbar
        canvas_container = ttk.Frame(preview_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for color swatches
        self.preview_canvas = Canvas(
            canvas_container,
            bg="#f0f0f0"
        )
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for preview (placed correctly before canvas)
        scrollbar = Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_canvas.config(yscrollcommand=scrollbar.set)
        
        # Info section
        info_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        info_frame.pack(fill=tk.X)
        
        self.info_label = ttk.Label(info_frame, text="Loading...")
        self.info_label.pack(fill=tk.X)
        
        # Focus on size entry
        self.size_entry.focus_set()
    
    def _update_palette_preview(self):
        """Update palette preview based on current size and algorithm."""
        try:
            # Get palette size from entry
            size = self.size_var.get()
            
            # Validate range
            if size < 1:
                size = 1
                self.size_var.set(1)
            elif size > 256:
                size = 256
                self.size_var.set(256)
            
            self.current_palette_size = size
            
            # Get current algorithm
            self.current_algorithm = self.algorithm_var.get()
            
            # Get palette from generator with selected algorithm
            self.colors, self.counts, _ = self.generator.get_palette(size, self.current_algorithm)
            
            # Find ties
            ties = self.generator.find_ties(size)
            self.current_ties = ties
            
            # Update UI
            self._draw_color_swatches()
            self._update_info()
            
            # Update resolve button state
            self.resolve_btn.config(state=tk.NORMAL if ties else tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update palette: {e}")
    
    def _draw_color_swatches(self):
        """Draw color swatches on preview canvas."""
        # Clear canvas
        self.preview_canvas.delete("all")
        
        # Calculate layout
        # Use a fixed width if canvas hasn't been rendered yet
        canvas_width = self.preview_canvas.winfo_width()
        if canvas_width < 100:  # Not rendered yet, use default
            canvas_width = 850
        
        swatch_size = 40
        padding = 5
        cols = max(1, canvas_width // (swatch_size + padding))
        
        x, y = padding, padding
        
        # Track the maximum y position for scroll region
        max_y = y
        
        for i, (color, count) in enumerate(zip(self.colors, self.counts)):
            # Check if this color is part of a tie
            is_tied = any(color in tie_colors for tie_colors in self.current_ties.values())
            
            # Draw swatch
            color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            self.preview_canvas.create_rectangle(
                x, y, x + swatch_size, y + swatch_size,
                fill=color_hex,
                outline="white" if is_tied else "black",
                width=3 if is_tied else 1
            )
            
            # Draw index
            self.preview_canvas.create_text(
                x + swatch_size // 2, y + swatch_size // 2,
                text=str(i),
                fill="black" if sum(color) > 382 else "white",
                font=("Arial", 10, "bold")
            )
            
            # Move to next position
            x += swatch_size + padding
            if x + swatch_size > canvas_width:
                x = padding
                y += swatch_size + padding
                max_y = y  # Track the bottom position
        
        # Update scroll region to include all colors
        self.preview_canvas.config(scrollregion=(0, 0, canvas_width, max_y + swatch_size + padding))
    
    def _update_info(self):
        """Update statistics label."""
        if not self.colors:
            self.info_label.config(text="No colors found")
            return
        
        total_pixels = sum(self.counts)
        avg_count = total_pixels / len(self.counts)
        
        # Find most and least frequent
        max_count = max(self.counts)
        min_count = min(self.counts)
        max_color = self.colors[self.counts.index(max_count)]
        min_color = self.colors[self.counts.index(min_count)]
        
        # Build info text
        info = f"Selected: {len(self.colors)} colors | Total pixels: {total_pixels}"
        info += f"\nAverage: {avg_count:.0f} pixels/color"
        info += f"\nMost frequent: {max_color} ({max_count} pixels)"
        info += f"\nLeast frequent: {min_color} ({min_count} pixels)"
        
        if self.current_ties:
            info += f"\n\n⚠ Ties found at {len(self.current_ties)} position(s)"
            info += "\nClick 'Resolve Ties' to choose which colors to include"
        
        self.info_label.config(text=info)
    
    def _on_size_change(self, event=None):
        """Handle palette size change."""
        self._update_palette_preview()
    
    def _on_algorithm_change(self, event=None):
        """Handle algorithm selection change."""
        self._update_palette_preview()
    
    def _resolve_ties_dialog(self):
        """Open dialog to resolve color ties."""
        if not self.current_ties:
            return
        
        # Create tie resolution window
        tie_window = tk.Toplevel(self.window)
        tie_window.title("Resolve Color Ties")
        tie_window.geometry("600x400")
        tie_window.transient(self.window)
        tie_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(tie_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            main_frame,
            text="The following colors have identical pixel counts.",
            font=("Arial", 11, "bold")
        ).pack(pady=(0, 10))
        
        ttk.Label(
            main_frame,
            text="Select which colors to include in the palette:"
        ).pack(pady=(0, 10))
        
        # Scrollable frame for tie options
        canvas = Canvas(main_frame, height=250)
        canvas.pack(fill=tk.BOTH, expand=True)
        scrollbar = Scrollbar(main_frame, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(yscrollcommand=scrollbar.set)
        
        content_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window(0, 0, window=content_frame, anchor=tk.NW)
        
        # Create options for each tie
        tie_vars = {}
        
        for tie_index, tied_colors in self.current_ties.items():
            # Get count for these colors
            count = self.generator.sorted_colors[tie_index][1]
            
            # Frame for this tie
            tie_group = ttk.LabelFrame(
                content_frame,
                text=f"Tie at index {tie_index} ({count} pixels)",
                padding="10"
            )
            tie_group.pack(fill=tk.X, pady=5)
            
            # Radio buttons for each color in tie
            var = tk.IntVar(value=0)
            tie_vars[tie_index] = var
            
            for i, color in enumerate(tied_colors):
                color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                
                color_frame = ttk.Frame(tie_group)
                color_frame.pack(fill=tk.X, pady=2)
                
                # Color swatch
                swatch = tk.Frame(color_frame, width=30, height=30, bg=color_hex)
                swatch.pack(side=tk.LEFT, padx=5)
                
                # Radio button
                rb = ttk.Radiobutton(
                    color_frame,
                    text=f"RGB{color}",
                    variable=var,
                    value=i
                )
                rb.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def apply_resolution():
            # Apply user's choices
            for tie_index, tied_colors in self.current_ties.items():
                var = tie_vars[tie_index]
                selected_idx = var.get()
                if selected_idx >= len(tied_colors):
                    continue
                
                selected_color = tied_colors[selected_idx]
                
                # Replace colors at and beyond tie index with selected color
                for i in range(tie_index, min(self.current_palette_size, len(self.generator.sorted_colors))):
                    if i < len(self.colors):
                        # Check if this color should be replaced
                        original_color = self.generator.sorted_colors[i][0]
                        if original_color in tied_colors:
                            # Replace with selected color
                            if i < len(self.colors):
                                self.colors[i] = selected_color
                            else:
                                # Add new color
                                self.colors.append(selected_color)
            
            # Update preview
            self._draw_color_swatches()
            self._update_info()
            tie_window.destroy()
            
            messagebox.showinfo("Success", "Ties resolved! Palette updated.")
        
        ttk.Button(button_frame, text="Apply", command=apply_resolution).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=tie_window.destroy).pack(side=tk.RIGHT)
        
        # Update scroll region
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
    
    def _export_palette(self):
        """Export palette to GIMP CSS file."""
        if not self.colors:
            messagebox.showwarning("Warning", "No colors to export")
            return
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            title="Save Palette",
            defaultextension=".css",
            filetypes=[("CSS Files", "*.css"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Export
        success = self.generator.export_gimp_css(self.colors, file_path)
        
        if success:
            messagebox.showinfo("Success", f"Palette exported to:\n{file_path}")
        else:
            messagebox.showerror("Error", "Failed to export palette") 
