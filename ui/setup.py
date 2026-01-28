import re
import utils
import json
import os

from PIL import (
    Image,
    ImageTk,
    ImageGrab
)
from pynput.mouse import Listener
from pynput import keyboard
from tkinter import (
    Button, 
    Toplevel, 
    messagebox, 
    simpledialog,
    font, 
    END,
    Canvas,
    Scrollbar,
    Label as tkLabel  # Import tkinter.Label for color control
)
from tkinter.ttk import (
    LabelFrame, 
    Frame, 
    Label, 
    Button, 
    Entry
)

class SetupWindow:
    def __init__(self, parent, bot, tools, on_complete, title='Child Window', w=1600, h=900, x=5, y=5):
        self._root = Toplevel(parent)

        self.title = title
        self.bot = bot
        self.on_complete = on_complete
        self.tools = tools
        self.parent = parent

        self._root.title(self.title)
        # Center the window on screen
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        self._root.geometry(f'{w}x{h}+{x}+{y}')
        self._root.protocol('WM_DELETE_WINDOW', self.close)

        default_font = font.nametofont('TkDefaultFont').actual()
        SetupWindow.TITLE_FONT = (default_font['family'], default_font['size'], 'bold')

        # LAYOUT
        self._root.columnconfigure(0, weight=1, uniform='column')
        self._root.columnconfigure(1, weight=1, uniform='column')
        self._root.rowconfigure(0, weight=1, uniform='row')
        
        self._tools_panel = self._init_tools_panel()
        self._tools_panel.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')

        self._preview_panel = self._init_preview_panel()
        self._preview_panel.grid(column=1, row=0, sticky='nsew', padx=5, pady=5)

    def _init_tools_panel(self):
        frame = LabelFrame(self._root, text='Tools', padding=10)

        # Configure column weights for better layout distribution
        frame.columnconfigure(0, weight=0, minsize=150)  # Tool name
        frame.columnconfigure(1, weight=0, minsize=120)  # Status
        frame.columnconfigure(2, weight=1)               # Settings

        # Configure row weights with consistent spacing
        for i in range(len(self.tools)):
            frame.rowconfigure(i, weight=1, minsize=80)

        self._statuses = {}

        # Define consistent button styling
        button_width = 12
        button_height = 1
        button_padx = 4
        button_pady = 4

        for idt, (k, v) in enumerate(self.tools.items()):
            # Use the 'name' field for display if it exists, otherwise use the key
            display_name = v.get('name', k) if isinstance(v, dict) else k
            
            # Tool name label with consistent padding
            Label(frame, text=display_name, font=SetupWindow.TITLE_FONT).grid(
                column=0, row=idt, sticky='w', padx=10, pady=8
            )
            
            # Status label with consistent styling
            status = Label(
                frame,
                text='INITIALIZED' if v['status'] else 'NOT INITIALIZED',
                foreground='white',
                background='green' if v['status'] else 'red',
                justify='center',
                anchor='center',
                width=14
            )
            status.grid(column=1, row=idt, padx=10, pady=8)
            self._statuses[k] = status

            # Settings frame with proper configuration
            settings_frame = Frame(frame)
            settings_frame.columnconfigure(0, weight=0, minsize=button_width * 8)  # Initialize button
            settings_frame.columnconfigure(1, weight=0, minsize=button_width * 8)  # Preview/Edit button
            settings_frame.columnconfigure(2, weight=0)  # Modifier checkboxes or extra controls
            settings_frame.columnconfigure(3, weight=0)  # Additional controls
            settings_frame.rowconfigure(0, weight=1)
            settings_frame.rowconfigure(1, weight=1)

            # Initialize button with consistent sizing
            Button(settings_frame, text='Initialize',
                   width=button_width,
                   command=lambda n=k, t=v : self._start_listening(n, t)).grid(
                column=0, row=0, padx=button_padx, pady=button_pady, sticky='ew'
            )
            
            if k == 'New Layer' or k == 'Color Button' or k == 'Color Button Okay':
                # Create modifier checkboxes (CTRL, ALT, SHIFT) with consistent styling
                from tkinter import Checkbutton, IntVar
                self._mod_vars = getattr(self, '_mod_vars', {})
                mv = {}
                mods = v.get('modifiers', {}) if isinstance(v, dict) else {}
                
                # Modifier frame for better organization
                mod_frame = Frame(settings_frame)
                mod_frame.grid(column=1, row=0, columnspan=3, sticky='w', padx=button_padx, pady=button_pady)
                
                for ci, name in enumerate(('ctrl', 'alt', 'shift')):
                    iv = IntVar()
                    iv.set(1 if mods.get(name, False) else 0)
                    cb = Checkbutton(mod_frame, text=name.upper(), variable=iv,
                                     command=lambda tk=k, n=name, iv=iv: self._on_modifier_toggle(tk, n, iv))
                    cb.pack(side='left', padx=4)
                    mv[name] = iv
                self._mod_vars[k] = mv
                
            elif k == 'color_preview_spot':
                # Color preview spot doesn't need any extra buttons
                pass
                
            else:
                # Preview button with consistent sizing
                Button(settings_frame, text='Preview',
                       width=button_width,
                       command=lambda n=k : self._set_preview(n)).grid(
                    column=1, row=0, padx=button_padx, pady=button_pady, sticky='ew'
                )
                
                # Add Manual Color Selection button for Palette
                if k == 'Palette':
                    Button(settings_frame, text='Edit Colors',
                           width=button_width,
                           command=lambda n=k, t=v : self._start_manual_color_selection(n, t)).grid(
                        column=2, row=0, padx=button_padx, pady=button_pady, sticky='ew'
                    )

            # Tool-specific settings in second row
            if k == 'Palette':
                # Palette dimension inputs with better organization
                dim_frame = Frame(settings_frame)
                dim_frame.grid(column=0, row=1, columnspan=4, sticky='w', padx=button_padx, pady=button_pady)
                
                Label(dim_frame, text='Rows:').pack(side='left', padx=(0, 4))
                self._erows = Entry(dim_frame, width=6)
                self._erows.pack(side='left', padx=(0, 12))
                
                Label(dim_frame, text='Columns:').pack(side='left', padx=(0, 4))
                self._ecols = Entry(dim_frame, width=6)
                self._ecols.pack(side='left', padx=(0, 4))

                self._erows.insert(0, v['rows'])
                self._ecols.insert(0, v['cols'])
                vcmd = (self._root.register(self._validate_dimensions), '%P')
                ivcmd = (self._root.register(self._on_invalid_dimensions),)
                self._erows.config(
                    validate='all',
                    validatecommand=vcmd,
                    invalidcommand=ivcmd
                )
                self._erows.bind('<FocusOut>', self._on_update_dimensions)
                self._erows.bind('<Return>', self._on_update_dimensions)
                self._ecols.config(
                    validate='all',
                    validatecommand=vcmd,
                    invalidcommand=ivcmd
                )
                self._ecols.bind('<FocusOut>', self._on_update_dimensions)
                self._ecols.bind('<Return>', self._on_update_dimensions)

            elif k == 'Color Button':
                # Color Button delay setting with better organization
                delay_frame = Frame(settings_frame)
                delay_frame.grid(column=0, row=1, columnspan=4, sticky='w', padx=button_padx, pady=button_pady)
                
                Label(delay_frame, text='Delay (s):').pack(side='left', padx=(0, 4))
                self._edelay = Entry(delay_frame, width=8)
                self._edelay.pack(side='left', padx=(0, 4))

                delay_value = v.get('delay', 0.1)
                self._edelay.insert(0, str(delay_value))
                delay_vcmd = (self._root.register(self._validate_delay), '%P')
                delay_ivcmd = (self._root.register(self._on_invalid_delay),)
                self._edelay.config(
                    validate='all',
                    validatecommand=delay_vcmd,
                    invalidcommand=delay_ivcmd
                )
                self._edelay.bind('<FocusOut>', self._on_update_delay)
                self._edelay.bind('<Return>', self._on_update_delay)

            elif k == 'Canvas':
                # Canvas calibration button with better organization
                Button(settings_frame, text='Calibrate Canvas',
                       width=button_width,
                       command=lambda n=k, t=v : self._start_canvas_calibration(n, t)).grid(
                    column=1, row=0, padx=button_padx, pady=button_pady, sticky='ew'
                )

                # Show calibration status
                calib_data = v.get('calibration')
                if calib_data:
                    calib_status = f"Scale: {calib_data.get('scale_factor', 1.0):.2f} ({calib_data.get('scale_factor', 1.0)*100:.0f}%)"
                    calib_date = calib_data.get('calibration_date', 'Never')
                    self._calib_status_label = Label(settings_frame,
                        text=f"{calib_status}\nCalibrated: {calib_date}",
                        font=('TkDefaultFont', 8),
                        justify='left'
                    )
                else:
                    self._calib_status_label = Label(settings_frame,
                        text="No calibration",
                        font=('TkDefaultFont', 8),
                        justify='left'
                    )
                self._calib_status_label.grid(column=0, row=1, columnspan=4, padx=button_padx, pady=button_pady, sticky='w')

            elif k == 'Color Button Okay':
                # Color Button Okay delay setting with better organization
                delay_frame = Frame(settings_frame)
                delay_frame.grid(column=0, row=1, columnspan=4, sticky='w', padx=button_padx, pady=button_pady)
                
                Label(delay_frame, text='Delay (s):').pack(side='left', padx=(0, 4))
                self._edelay_okay = Entry(delay_frame, width=8)
                self._edelay_okay.pack(side='left', padx=(0, 4))

                delay_value = v.get('delay', 0.1)
                self._edelay_okay.insert(0, str(delay_value))
                delay_vcmd = (self._root.register(self._validate_delay), '%P')
                delay_ivcmd = (self._root.register(self._on_invalid_delay),)
                self._edelay_okay.config(
                    validate='all',
                    validatecommand=delay_vcmd,
                    invalidcommand=delay_ivcmd
                )
                self._edelay_okay.bind('<FocusOut>', lambda e, k=k: self._on_update_delay_okay(e, k))
                self._edelay_okay.bind('<Return>', lambda e, k=k: self._on_update_delay_okay(e, k))

            settings_frame.grid(column=2, row=idt, sticky='nsew', padx=5, pady=2)
        return frame

    def _init_preview_panel(self):
        frame = LabelFrame(self._root, text='Preview')
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self._img_label = Label(frame, text='No image to preview')
        self._img_label.grid(column=0, row=0, sticky='ns', padx=5, pady=5)

        return frame

    def _set_preview(self, name):
        self._current_tool = self.tools[name]
        try:
            self._img = Image.open(self.tools[name]['preview'])
            self._img = ImageTk.PhotoImage(self._img.resize(
                utils.adjusted_img_size(self._img, (self._preview_panel.winfo_width() - 10, self._preview_panel.winfo_height() - 10))
            ))
            self._img_label['image'] = self._img
        except:
            self._img_label['image'] = ''
            self._img_label['text'] = 'No image to preview'

    def _start_listening(self, name, tool):
        self._current_tool = tool
        self._tool_name = name

        if self._tool_name == 'Palette':
            try:
                self.rows = int(self._erows.get())
                self.cols = int(self._ecols.get())
            except:
                messagebox.showerror(self.title, 'Please enter valid values for rows and columns before initializing your palette!')
                return

        self._coords = []
        self._clicks = 0
        
        # FIXED: Added 'color_preview_spot' to the tuple checking for single-click tools
        # Using the correct configuration key name
        self._required_clicks = 1 if self._tool_name in ('New Layer', 'Color Button', 'Color Button Okay', 'color_preview_spot') else 2
        
        prompt = 'Click the location of the button.' if self._required_clicks == 1 else 'Click on the UPPER LEFT and LOWER RIGHT corners of the tool.'
        if messagebox.askokcancel(self.title, prompt) == True:
            self._listener = Listener(on_click=self._on_click)
            self._listener.start()
            self._root.iconify()
            self.parent.iconify()
    
    def _start_manual_color_selection(self, name, tool):
        """Start manual color selection for palette grid"""
        self._current_tool = tool
        self._tool_name = name
        
        if self._tool_name != 'Palette':
            messagebox.showerror(self.title, 'Manual color selection is only available for Palette!')
            return
        
        # Check if palette has been captured
        if not tool.get('box'):
            messagebox.showerror(self.title, 'Please initialize the palette first (click Initialize)!')
            return
        
        self.rows = tool['rows']
        self.cols = tool['cols']
        box = tool['box']
        
        # Ensure palette_box coordinates are in correct order (left, top, right, bottom)
        if len(box) == 4:
            left = min(box[0], box[2])
            top = min(box[1], box[3])
            right = max(box[0], box[2])
            bottom = max(box[1], box[3])
            self.palette_box = (left, top, right, bottom)
        else:
            self.palette_box = box
        
        # Open color selection window
        self._open_color_selection_window()
    
    def _open_color_selection_window(self):
        """Open window for manually selecting valid palette colors"""
        # Create a new Toplevel window for color selection
        self._color_sel_window = Toplevel(self._root)
        self._color_sel_window.title('Select Valid Palette Colors')
        self._color_sel_window.geometry('900x700+100+100')
        
        # Center the window
        self._color_sel_window.update_idletasks()
        sw = self._color_sel_window.winfo_screenwidth()
        sh = self._color_sel_window.winfo_screenheight()
        w, h = 900, 700
        x = (sw - w) // 2
        y = (sh - h) // 2
        self._color_sel_window.geometry(f'{w}x{h}+{x}+{y}')
        
        # Configure grid layout
        self._color_sel_window.columnconfigure(0, weight=1)
        self._color_sel_window.columnconfigure(1, weight=0)
        self._color_sel_window.rowconfigure(0, weight=0)  # Instructions
        self._color_sel_window.rowconfigure(1, weight=0)  # Mode buttons
        self._color_sel_window.rowconfigure(2, weight=1)  # Grid
        self._color_sel_window.rowconfigure(3, weight=0)  # Action buttons
        
        # Mode selection
        self._pick_centers_mode = False  # False = Toggle mode, True = Pick centers mode
        self._manual_centers = {}  # Store manually picked centers {index: (x, y)}
        
        # Load existing manual centers if available
        if self._current_tool.get('manual_centers'):
            self._manual_centers = {int(k): tuple(v) for k, v in self._current_tool['manual_centers'].items()}
        
        # Create grid buttons
        self._grid_buttons = {}
        
        # Load existing valid_positions if available, otherwise assume all are valid
        if self._current_tool.get('valid_positions'):
            # Filter to only include positions within current grid bounds
            max_position = self.rows * self.cols - 1
            self._valid_positions = {pos for pos in self._current_tool['valid_positions'] if pos <= max_position}
        else:
            self._valid_positions = set(range(self.rows * self.cols))
        
        # Instructions
        instructions = Label(
            self._color_sel_window,
            text='Click on grid cells to toggle them. Green = Valid, Red = Invalid. Use "Pick Centers" mode to set exact center points.',
            wraplength=870,
            justify='left'
        )
        instructions.grid(column=0, row=0, padx=10, pady=(10, 5), sticky='ew')
        
        # Mode buttons frame with consistent sizing
        mode_frame = Frame(self._color_sel_window)
        mode_frame.grid(column=0, row=1, padx=10, pady=5, sticky='ew')
        
        self._mode_btn_toggle = Button(mode_frame, text='Toggle Valid/Invalid', width=18, command=self._set_toggle_mode)
        self._mode_btn_toggle.pack(side='left', padx=5)
        
        self._mode_btn_pick = Button(mode_frame, text='Pick Centers', width=12, command=self._set_pick_centers_mode)
        self._mode_btn_pick.pack(side='left', padx=5)
        
        # Scrollable frame for grid - using Canvas-based approach like precision estimate
        canvas = Canvas(self._color_sel_window)
        scrollbar = Scrollbar(self._color_sel_window, orient='vertical', command=canvas.yview)
        scrollable_frame = Frame(canvas)
        
        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(column=0, row=2, sticky='nsew', padx=10, pady=5)
        scrollbar.grid(column=1, row=2, sticky='ns', pady=5)
        
        # Create grid cells using Canvas-based approach
        self._grid_buttons = {}
        # Note: self._valid_positions is already loaded above from config
        
        # Load palette preview image
        try:
            palette_img = Image.open(self._current_tool['preview'])
            self._palette_img_pil = palette_img  # Store PIL image for resizing
            
            # Extract colors from palette image for each grid cell
            self.palette_colors = []
            cell_width = palette_img.width // self.cols
            cell_height = palette_img.height // self.rows
            
            for row in range(self.rows):
                for col in range(self.cols):
                    # Calculate center pixel of each cell
                    x = col * cell_width + cell_width // 2
                    y = row * cell_height + cell_height // 2
                    # Get pixel color (RGB tuple)
                    color = palette_img.getpixel((x, y))
                    self.palette_colors.append(color)
            
            current_row = 0  # No separate image label, so grid starts at row 0
        except:
            current_row = 0
            self._palette_img_pil = None
        
        # Create Canvas-based grid with enable/disable indicators ON TOP of cells
        # Calculate cell size based on palette dimensions (similar to precision estimate)
        cell_size = 50  # Base cell size in pixels
        
        # Create a canvas for the grid (no background color - will show palette image)
        grid_canvas = Canvas(scrollable_frame, highlightthickness=0)
        grid_canvas.grid(column=0, row=current_row, columnspan=self.cols, padx=5, pady=5)
        
        # Store canvas reference for later updates
        self._grid_canvas = grid_canvas
        self._cell_size = cell_size
        self._grid_start_row = current_row
        
        # Draw the grid with enable/disable indicators
        self._draw_grid_with_indicators()
        
        # Action buttons frame with better organization and consistent sizing
        action_frame = Frame(self._color_sel_window)
        action_frame.grid(column=0, row=3, columnspan=2, padx=10, pady=10, sticky='ew')
        
        # Group buttons logically
        # Primary actions
        Button(action_frame, text='Done', width=10, command=self._on_color_selection_done).pack(side='left', padx=3)
        Button(action_frame, text='Cancel', width=10, command=lambda: self._color_sel_window.destroy()).pack(side='left', padx=3)
        
        # Separator
        from tkinter import ttk
        ttk.Separator(action_frame, orient='vertical').pack(side='left', fill='y', padx=10)
        
        # Center estimation actions
        Button(action_frame, text='Auto-Estimate', width=14, command=self._auto_estimate_centers).pack(side='left', padx=3)
        Button(action_frame, text='Precision Estimate', width=16, command=self._start_precision_estimate).pack(side='left', padx=3)
        Button(action_frame, text='Show Centers', width=12, command=self._show_custom_centers_overlay).pack(side='left', padx=3)
        
        # Separator
        ttk.Separator(action_frame, orient='vertical').pack(side='left', fill='y', padx=10)
        
        # Selection actions
        Button(action_frame, text='Select All', width=12, command=self._select_all_colors).pack(side='left', padx=3)
        Button(action_frame, text='Deselect All', width=14, command=self._deselect_all_colors).pack(side='left', padx=3)
        
        # Bind ESC key to cancel picking on the parent window (works even when color window is minimized)
        self.parent.bind('<Escape>', lambda e: self._on_escape_press(e))
    
    def _draw_grid_with_indicators(self):
        """Draw the grid with enable/disable indicators ON TOP of each cell (similar to precision estimate)"""
        if not hasattr(self, '_grid_canvas'):
            return
        
        # DEBUG: Log palette_colors existence and content
        print(f"[DEBUG] hasattr(self, 'palette_colors'): {hasattr(self, 'palette_colors')}")
        if hasattr(self, 'palette_colors'):
            print(f"[DEBUG] len(self.palette_colors): {len(self.palette_colors)}")
            print(f"[DEBUG] First 3 colors: {self.palette_colors[:3] if len(self.palette_colors) >= 3 else self.palette_colors}")
        
        # Clear the canvas
        self._grid_canvas.delete('all')
        
        # Calculate canvas dimensions based on grid size
        canvas_width = self.cols * self._cell_size
        canvas_height = self.rows * self._cell_size
        self._grid_canvas.config(width=canvas_width, height=canvas_height)
        
        # Draw palette image as background
        if hasattr(self, '_palette_img_pil') and self._palette_img_pil is not None:
            # Resize palette image to match canvas dimensions
            resized_img = self._palette_img_pil.resize((canvas_width, canvas_height), 1)
            # Create PhotoImage and store as instance variable to prevent garbage collection
            self._palette_canvas_bg = ImageTk.PhotoImage(resized_img)
            # Draw image at top-left corner of canvas
            self._grid_canvas.create_image(0, 0, anchor='nw', image=self._palette_canvas_bg)
        
        # Draw grid cells with enable/disable indicators
        for i in range(self.rows * self.cols):
            row = i // self.cols
            col = i % self.cols
            
            x1 = col * self._cell_size
            y1 = row * self._cell_size
            x2 = x1 + self._cell_size
            y2 = y1 + self._cell_size
            
            # Calculate cell center for indicator dot
            cell_center_x = x1 + self._cell_size / 2
            cell_center_y = y1 + self._cell_size / 2
            
            # Draw enable/disable indicator (transparent grid - no background)
            if i in self._valid_positions:
                # Green indicator for enabled cells (similar to anchor points in precision estimate)
                indicator_size = 8
                self._grid_canvas.create_oval(
                    cell_center_x - indicator_size, cell_center_y - indicator_size,
                    cell_center_x + indicator_size, cell_center_y + indicator_size,
                    fill='green', outline='darkgreen', width=2
                )
            else:
                # Red indicator for disabled cells
                indicator_size = 8
                self._grid_canvas.create_oval(
                    cell_center_x - indicator_size, cell_center_y - indicator_size,
                    cell_center_x + indicator_size, cell_center_y + indicator_size,
                    fill='red', outline='darkred', width=2
                )
        
        # Bind click event to canvas
        self._grid_canvas.bind('<Button-1>', self._on_grid_canvas_click)
    
    def _draw_grid_for_pick_centers(self):
        """Draw the grid for pick centers mode (shows valid cells with center status)"""
        if not hasattr(self, '_grid_canvas'):
            return
        
        # Clear the canvas
        self._grid_canvas.delete('all')
        
        # Calculate canvas dimensions based on grid size
        canvas_width = self.cols * self._cell_size
        canvas_height = self.rows * self._cell_size
        self._grid_canvas.config(width=canvas_width, height=canvas_height)
        
        # Draw grid cells with center picking indicators
        for i in range(self.rows * self.cols):
            row = i // self.cols
            col = i % self.cols
            
            x1 = col * self._cell_size
            y1 = row * self._cell_size
            x2 = x1 + self._cell_size
            y2 = y1 + self._cell_size
            
            # Draw cell background
            if i in self._manual_centers:
                # Yellow for cells that have a center
                self._grid_canvas.create_rectangle(x1, y1, x2, y2, fill='yellow', outline='lightgray')
            elif i in self._valid_positions:
                # White for valid cells without center yet
                self._grid_canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='lightgray')
            else:
                # Gray for invalid cells
                self._grid_canvas.create_rectangle(x1, y1, x2, y2, fill='lightgray', outline='gray')
            
            # Draw cell number centered
            cell_center_x = x1 + self._cell_size / 2
            cell_center_y = y1 + self._cell_size / 2
            
            if i in self._manual_centers:
                # Show checkmark for cells with center
                self._grid_canvas.create_text(cell_center_x, cell_center_y,
                    text='✓', font=('Arial', 14, 'bold'), fill='black')
            else:
                # Show cell number
                self._grid_canvas.create_text(cell_center_x, cell_center_y,
                    text=str(i + 1), font=('Arial', 10), fill='gray')
        
        # Bind click event to canvas for center picking
        self._grid_canvas.bind('<Button-1>', self._on_grid_canvas_click_pick_centers)
    
    def _on_grid_canvas_click_pick_centers(self, event):
        """Handle click on grid canvas for picking centers"""
        # Calculate which cell was clicked
        col = event.x // self._cell_size
        row = event.y // self._cell_size
        
        if col < 0 or col >= self.cols or row < 0 or row >= self.rows:
            return  # Clicked outside grid
        
        index = row * self.cols + col
        self._pick_center(index)
    
    def _on_grid_canvas_click(self, event):
        """Handle click on grid canvas to toggle enable/disable"""
        # Calculate which cell was clicked
        col = event.x // self._cell_size
        row = event.y // self._cell_size
        
        if col < 0 or col >= self.cols or row < 0 or row >= self.rows:
            return  # Clicked outside grid
        
        index = row * self.cols + col
        self._toggle_grid_cell(index)
    
    def _toggle_grid_cell(self, index):
        """Toggle a grid cell between valid and invalid"""
        if index in self._valid_positions:
            self._valid_positions.remove(index)
        else:
            self._valid_positions.add(index)
        # Redraw the grid with updated indicators
        self._draw_grid_with_indicators()
    
    def _select_all_colors(self):
        """Select all grid cells as valid"""
        self._valid_positions = set(range(self.rows * self.cols))
        self._draw_grid_with_indicators()
    
    def _deselect_all_colors(self):
        """Deselect all grid cells"""
        self._valid_positions = set()
        self._draw_grid_with_indicators()
    
    def _set_toggle_mode(self):
        """Set mode to toggle valid/invalid cells"""
        self._pick_centers_mode = False
        self._manual_centers = {}  # Clear manual centers when switching modes
        # Update instructions
        for widget in self._color_sel_window.winfo_children():
            try:
                if isinstance(widget, Label) and 'text' in str(widget.cget('text')):
                    widget.config(text='Click on grid cells to toggle them. Green = Valid, Red = Invalid. Click "Done" when finished.')
            except:
                pass
        # Redraw grid with enable/disable indicators
        self._draw_grid_with_indicators()
    
    def _set_pick_centers_mode(self):
        """Set mode to pick exact center points for each color"""
        if not self._valid_positions:
            messagebox.showwarning(self.title, 'Please mark at least one color as valid first!')
            return
        
        self._pick_centers_mode = True
        self._manual_centers = {}  # Reset manual centers
        # Clear existing manual centers when entering pick mode
        for i in list(self._manual_centers.keys()):
            del self._manual_centers[i]
        
        # Update instructions
        for widget in self._color_sel_window.winfo_children():
            try:
                if isinstance(widget, Label) and 'text' in str(widget.cget('text')):
                    widget.config(text='Click on a color cell, then click the center point on your palette. System will automatically move to the next color. Press ESC to stop at any time. Yellow = Has center, White = No center yet.')
            except:
                pass
        
        # Update grid to show center picking status
        self._draw_grid_for_pick_centers()
    
    def _pick_center(self, index):
        """Pick a center point for a specific color cell"""
        if index not in self._valid_positions:
            messagebox.showwarning(self.title, 'Cannot pick center for invalid cell!')
            return
        
        # Wait for mouse click to get center coordinates
        self._coords = []
        self._clicks = 0
        self._required_clicks = 1
        self._current_picking_index = index
        
        # Start listening for mouse click (no confirmation dialog for continuous picking)
        print(f'Picking center for color {index + 1}... Press ESC to stop.')
        self._listener = Listener(on_click=self._on_center_pick_click)
        self._listener.start()
        
        # Start global keyboard listener for ESC key
        self._key_listener = keyboard.Listener(on_press=self._on_key_press)
        self._key_listener.start()
        
        self._color_sel_window.iconify()
    
    def _on_key_press(self, key):
        """Handle keyboard press events"""
        try:
            # Check if ESC key is pressed
            if key == keyboard.Key.esc:
                if self._pick_centers_mode and hasattr(self, '_listener'):
                    # Stop the mouse listener and keyboard listener
                    try:
                        self._listener.stop()
                    except:
                        pass
                    try:
                        self._key_listener.stop()
                    except:
                        pass
                    self._color_sel_window.deiconify()
                    print('Center picking cancelled by ESC key')
        except AttributeError:
            pass  # Ignore special keys that don't have char attribute
    
    def _auto_estimate_centers(self):
        """Automatically estimate centers for all valid colors"""
        if not self._valid_positions:
            messagebox.showwarning(self.title, 'Please mark at least one color as valid first!')
            return
        
        # Calculate cell dimensions
        palette_w = self.palette_box[2] - self.palette_box[0]
        palette_h = self.palette_box[3] - self.palette_box[1]
        cell_w = palette_w // self.cols
        cell_h = palette_h // self.rows
        
        # Estimate centers for all valid positions
        for i in self._valid_positions:
            row = i // self.cols
            col = i % self.cols
            
            # Calculate center relative to palette box
            center_x = col * cell_w + cell_w // 2
            center_y = row * cell_h + cell_h // 2
            
            self._manual_centers[i] = (center_x, center_y)
        
        # Redraw grid with estimated centers
        self._draw_grid_for_pick_centers()
        
        # Show visual overlay of estimated centers on screen
        self._show_centers_overlay()
        
        # Update instructions to show estimated centers
        for widget in self._color_sel_window.winfo_children():
            try:
                if isinstance(widget, Label) and 'text' in str(widget.cget('text')):
                    widget.config(text='Centers auto-estimated (yellow = estimated). Click "Done" to accept or manually adjust by switching to Pick Centers mode.')
            except:
                pass
        
        print(f'Auto-estimated centers for {len(self._manual_centers)} colors')
    
    def _start_precision_estimate(self):
        """Start interactive palette extraction mode"""
        # Launch the new interactive palette extractor
        from ui.setup import InteractivePaletteExtractor
        self._extractor = InteractivePaletteExtractor(
            parent=self._root,
            bot=self.bot,
            current_tool=self._current_tool,
            tool_name=self._tool_name,
            valid_positions=self._valid_positions,
            palette_box=self.palette_box,
            on_complete=self._on_extraction_complete
        )
    
    def _on_extraction_complete(self, manual_centers):
        """Handle completion of interactive palette extraction"""
        if manual_centers:
            self._manual_centers = manual_centers
            # Redraw grid with extracted centers
            self._draw_grid_for_pick_centers()
            # Show overlay of extracted centers
            self._show_centers_overlay()
            # Update instructions
            for widget in self._color_sel_window.winfo_children():
                try:
                    if isinstance(widget, Label) and 'text' in str(widget.cget('text')):
                        widget.config(text='Extraction complete (yellow = extracted). Click "Done" to accept or manually adjust by switching to Pick Centers mode.')
                except:
                    pass
        else:
            # User cancelled extraction
            print('Interactive palette extraction cancelled')
    
    def _show_centers_overlay(self):
        """Show overlay circles on screen at estimated center positions"""
        from tkinter import Toplevel, Canvas
        
        # Create overlay window positioned exactly over palette
        palette_x = self.palette_box[0]
        palette_y = self.palette_box[1]
        palette_w = self.palette_box[2] - self.palette_box[0]
        palette_h = self.palette_box[3] - self.palette_box[1]
        
        # Create overlay window
        overlay = Toplevel()
        overlay.overrideredirect(True)  # Remove window decorations
        overlay.attributes('-topmost', True)  # Keep on top
        overlay.attributes('-alpha', 0.9)  # Slightly transparent
        overlay.config(bg='white')  # White background to make red circles visible
        overlay.geometry(f'{palette_w}x{palette_h}+{palette_x}+{palette_y}')
        
        # Create canvas
        canvas = Canvas(overlay, bg='white', highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        
        # Draw black dots at each estimated center position
        for i in sorted(self._manual_centers.keys()):
            center_x, center_y = self._manual_centers[i]
            
            # DEBUG: Log drawing coordinates
            if i == min(self._manual_centers.keys()):
                print(f'[DEBUG] Drawing first dot at canvas pos: ({center_x}, {center_y})')
                print(f'[DEBUG] Overlay window position: ({palette_x}, {palette_y})')
                print(f'[DEBUG] Expected screen position: ({palette_x + center_x}, {palette_y + center_y})')
            
            # Draw black dot (filled circle)
            canvas.create_oval(
                center_x - 6, center_y - 6,
                center_x + 6, center_y + 6,
                fill='black', outline='black'
            )
            
            # Add label showing color number
            canvas.create_text(
                center_x, center_y - 15,
                text=str(i + 1),
                fill='red',
                font=('Arial', 12, 'bold')
            )
        
        # Update window
        overlay.update()
        
        # Show for 5 seconds then close
        self._root.after(5000, lambda: overlay.destroy())
        print('Showing estimated centers overlay for 5 seconds...')
        
        # Show info dialog after overlay closes
        self._root.after(5100, lambda: messagebox.showinfo(
            self.title, 
            f'Auto-estimated centers for {len(self._manual_centers)} valid colors!\n\n'
            f'Red circles showed estimated positions on your palette.\n'
            f'Yellow cells in the grid show estimated centers.\n\n'
            f'You can still manually adjust by clicking "Pick Centers" to pick specific centers.'
        ))
    
    def _show_custom_centers_overlay(self):
        """Show overlay circles on screen at manually picked center positions"""
        from tkinter import Toplevel, Canvas
        
        if not self._manual_centers:
            messagebox.showwarning(self.title, 'No custom centers to show! Please pick centers first using "Pick Centers" mode.')
            return
        
        # Create overlay window positioned exactly over palette
        palette_x = self.palette_box[0]
        palette_y = self.palette_box[1]
        palette_w = self.palette_box[2] - self.palette_box[0]
        palette_h = self.palette_box[3] - self.palette_box[1]
        
        overlay = Toplevel()
        overlay.overrideredirect(True)  # Remove window decorations
        overlay.attributes('-topmost', True)  # Keep on top
        overlay.attributes('-alpha', 0.9)  # Slightly transparent
        overlay.config(bg='white')  # White background to make blue circles visible
        overlay.geometry(f'{palette_w}x{palette_h}+{palette_x}+{palette_y}')
        
        # Create canvas
        canvas = Canvas(overlay, bg='white', highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        
        # Draw black dots at each custom center position
        for i in sorted(self._manual_centers.keys()):
            center_x, center_y = self._manual_centers[i]
            
            # Draw black dot (filled circle)
            canvas.create_oval(
                center_x - 6, center_y - 6,
                center_x + 6, center_y + 6,
                fill='black', outline='black'
            )
            
            # Add label showing color number
            canvas.create_text(
                center_x, center_y - 15,
                text=str(i + 1),
                fill='blue',
                font=('Arial', 12, 'bold')
            )
        
        # Update window
        overlay.update()
        
        # Show for 5 seconds then close
        self._root.after(5000, lambda: overlay.destroy())
        print('Showing custom centers overlay for 5 seconds...')
        
        # Show info dialog after overlay closes
        self._root.after(5100, lambda: messagebox.showinfo(
            self.title, 
            f'Displaying {len(self._manual_centers)} custom centers!\n\n'
            f'Blue circles showed your manually picked positions on your palette.\n'
            f'Yellow cells in the grid show custom centers.\n\n'
            f'You can adjust centers by clicking "Pick Centers" to pick specific centers.'
        ))
    
    def _on_escape_press(self, event):
        """Handle ESC key press to cancel picking"""
        if self._pick_centers_mode and hasattr(self, '_listener'):
            # Stop the listener and cancel picking
            try:
                self._listener.stop()
            except:
                pass  # Ignore errors when stopping
            self._color_sel_window.deiconify()
            print('Center picking cancelled by ESC key')
    
    def _on_center_pick_click(self, x, y, _, pressed):
        """Handle click for picking center point"""
        if pressed:
            self._root.bell()
            print(x, y)
            self._clicks += 1
            self._coords += x, y
            
            if self._clicks == self._required_clicks:
                # Store the picked center coordinates (relative to palette box)
                center_x = self._coords[0] - self.palette_box[0]
                center_y = self._coords[1] - self.palette_box[1]
                self._manual_centers[self._current_picking_index] = (center_x, center_y)
                
                # Redraw the grid to show it has a center
                self._draw_grid_for_pick_centers()
                
                print(f'Picked center for color {self._current_picking_index + 1}: ({center_x}, {center_y})')
                
                # Find next valid color that doesn't have a center yet
                next_index = None
                for i in sorted(self._valid_positions):
                    if i > self._current_picking_index and i not in self._manual_centers:
                        next_index = i
                        break
                
                if next_index is not None:
                    # Continue to next color automatically
                    self._current_picking_index = next_index
                    self._clicks = 0
                    self._coords = []
                    # Don't show messagebox, just continue picking
                    print(f'Continuing to color {next_index + 1}...')
                else:
                    # All valid colors have centers
                    self._listener.stop()
                    # Also stop the keyboard listener
                    try:
                        self._key_listener.stop()
                    except:
                        pass
                    self._color_sel_window.deiconify()
                    messagebox.showinfo(self.title, 'All valid colors have been assigned centers!\n\nClick "Done" to save or adjust centers.')
    
    def _on_color_selection_done(self):
        """Handle completion of manual color selection"""
        if not self._valid_positions:
            messagebox.showwarning(
                self.title,
                'You must select at least one valid color!'
            )
            return
        
        # Store valid positions in tool config
        self._current_tool['valid_positions'] = list(self._valid_positions)
        
        # Reinitialize palette with valid positions and manual centers
        try:
            pbox_adj = (self.palette_box[0], self.palette_box[1], 
                        self.palette_box[2] - self.palette_box[0], 
                        self.palette_box[3] - self.palette_box[1])
            
            # Pass manual_centers if in pick centers mode and centers were picked
            manual_centers = self._manual_centers if self._pick_centers_mode and self._manual_centers else None
            
            p = self.bot.init_palette(
                pbox=pbox_adj,
                prows=self.rows,
                pcols=self.cols,
                valid_positions=self._valid_positions,
                manual_centers=manual_centers
            )
            
            # Update tool data
            self._current_tool['color_coords'] = {str(k): v for k, v in p.colors_pos.items()}
            self._current_tool['manual_centers'] = {str(k): v for k, v in self._manual_centers.items()} if self._manual_centers else {}
            self._current_tool['status'] = True
            self._statuses[self._tool_name].configure(text='INITIALIZED', background='green')
            
            messagebox.showinfo(
                self.title,
                f'Palette updated with {len(self._valid_positions)} valid colors out of {self.rows * self.cols} total positions.'
            )
            
        except Exception as e:
            messagebox.showerror(self.title, f'Error updating palette: {str(e)}')
        
        # Close the selection window
        self._color_sel_window.destroy()
    
    def _on_click(self, x, y, _, pressed):
        if pressed:
            self._root.bell()
            print(x, y)
            self._clicks += 1
            self._coords += x, y

            if self._clicks == self._required_clicks:
                init_functions = {
                    'Palette': self.bot.init_palette,
                    'Canvas': self.bot.init_canvas,
                    'Custom Colors': self.bot.init_custom_colors,
                    'color_preview_spot': lambda box: None  # Single-click tool, no init needed
                }

                if self._required_clicks == 2:
                    # Determining corner coordinates based on received input. ImageGrab.grab() always expects
                    # the first pair of coordinates to be above and on the left of the second pair
                    top_left = (min(self._coords[0], self._coords[2]), min(self._coords[1], self._coords[3]))
                    bot_right = (max(self._coords[0], self._coords[2]), max(self._coords[1], self._coords[3]))
                    box = (top_left[0], top_left[1], bot_right[0], bot_right[1])
                    print(f'Capturing box: {box}')

                    if self._tool_name == 'Palette':
                        p = init_functions['Palette'](prows=self.rows, pcols=self.cols, pbox=box)
                        # JSON does not support saving tuples hence the key has been converted into a string instead
                        self._current_tool['color_coords'] = {str(k): v for k, v in p.colors_pos.items()}
                        self._current_tool['rows'] = self.rows
                        self._current_tool['cols'] = self.cols
                    else:
                        init_functions[self._tool_name](box)

                    self._current_tool['status'] = True
                    self._current_tool['box'] = box
                    self._statuses[self._tool_name].configure(text='INITIALIZED', background='green')

                    self._preview_panel.update()
                    self._current_tool['preview'] = f'assets/{self._tool_name}_preview.png'
                    ImageGrab.grab(box).save(self._current_tool['preview'], format='png')

                else:
                    # Single-click tools like New Layer
                    # Save the clicked point as coords
                    coords = (int(self._coords[0]), int(self._coords[1]))
                    print(f'Captured point: {coords}')
                    # Store as simple coords and mark status
                    self._current_tool['coords'] = list(coords)
                    self._current_tool['status'] = True
                    self._statuses[self._tool_name].configure(text='INITIALIZED', background='green')

                self._listener.stop()
                self.parent.deiconify()
                self.parent.wm_state('normal')
                self._root.deiconify()
                self._root.wm_state('normal')
    
    def _validate_dimensions(self, value):
        return re.fullmatch(r'\d*', value) is not None

    def _on_invalid_dimensions(self):
        self._root.bell()

    def _on_update_dimensions(self, event):
        if event.widget.get() == '':
            event.widget.delete(0, END)
            event.widget.insert(0, '1')

    def _validate_delay(self, value):
        """Validate delay input: must be a number between 0.01 and 5.0"""
        if value == '':
            return True  # Allow empty during editing
        try:
            num = float(value)
            return 0.01 <= num <= 5.0
        except ValueError:
            return False

    def _on_invalid_delay(self):
        """Handle invalid delay input"""
        self._root.bell()

    def _on_update_delay(self, event):
        """Update delay value for Color Button and validate on focus out or return"""
        try:
            value = event.widget.get()
            tool_name = 'Color Button'
            if value == '':
                # Default to 0.1 if empty
                event.widget.delete(0, END)
                event.widget.insert(0, '0.1')
                clamped = 0.1
                print(f'{tool_name} delay updated to default: {clamped}s')
            else:
                num = float(value)
                # Clamp to valid range
                clamped = max(0.01, min(5.0, num))
                if clamped != num:
                    event.widget.delete(0, END)
                    event.widget.insert(0, str(clamped))
                    print(f'{tool_name} delay clamped from {num}s to {clamped}s')
                else:
                    print(f'{tool_name} delay updated to {clamped}s')
            # Update tools dict with delay value
            self.tools[tool_name]['delay'] = clamped
        except ValueError:
            # If invalid, reset to default
            tool_name = 'Color Button'
            event.widget.delete(0, END)
            event.widget.insert(0, '0.1')
            self.tools[tool_name]['delay'] = 0.1
            print(f'Invalid {tool_name} delay input, reset to default: 0.1s')

    def _on_enable_toggle(self, tool_name, intvar):
        # Update stored tools dict enabled state for given tool
        try:
            if tool_name in self.tools:
                self.tools[tool_name]['enabled'] = bool(intvar.get())
        except Exception:
            pass

    def _on_update_delay_okay(self, event, tool_name):
        """Update delay value for Color Button Okay and validate on focus out or return"""
        try:
            value = event.widget.get()
            if value == '':
                # Default to 0.1 if empty
                event.widget.delete(0, END)
                event.widget.insert(0, '0.1')
                clamped = 0.1
                print(f'{tool_name} delay updated to default: {clamped}s')
            else:
                num = float(value)
                # Clamp to valid range
                clamped = max(0.01, min(5.0, num))
                if clamped != num:
                    event.widget.delete(0, END)
                    event.widget.insert(0, str(clamped))
                    print(f'{tool_name} delay clamped from {num}s to {clamped}s')
                else:
                    print(f'{tool_name} delay updated to {clamped}s')
            # Update tools dict with delay value
            self.tools[tool_name]['delay'] = clamped
        except ValueError:
            # If invalid, reset to default
            event.widget.delete(0, END)
            event.widget.insert(0, '0.1')
            self.tools[tool_name]['delay'] = 0.1
            print(f'Invalid {tool_name} delay input, reset to default: 0.1s')

    def _on_modifier_toggle(self, tool_name, modifier_name, intvar):
        # Update the stored tools dict modifiers for given tool
        try:
            if tool_name in self.tools:
                if 'modifiers' not in self.tools[tool_name] or not isinstance(self.tools[tool_name]['modifiers'], dict):
                    self.tools[tool_name]['modifiers'] = {}
                self.tools[tool_name]['modifiers'][modifier_name] = bool(intvar.get())
        except Exception:
            pass

    def _start_canvas_calibration(self, name, tool):
        """Start canvas calibration process"""
        if not tool.get('box'):
            messagebox.showerror(self.title, 'Please initialize Canvas first (click Initialize button)!')
            return
        
        # Check if canvas is initialized
        try:
            canvas_x, canvas_y, canvas_w, canvas_h = self.bot._canvas
        except:
            messagebox.showerror(self.title, 'Please initialize Canvas first (click Initialize button)!')
            return
        
        # Show preparation dialog
        result = messagebox.askokcancel(
            'Canvas Calibration',
            'A checkerboard pattern will be drawn on your canvas to detect zoom level.\n\n'
            'The pattern will be drawn using your currently selected color.\n\n'
            'Please prepare:\n'
            '1. Open your drawing application\n'
            '2. Select a color/brush tool\n'
            '3. Have the canvas visible\n\n'
            '4. Click OK when ready\n\n'
            'The bot will wait 5 seconds after you click OK, giving you time to prepare.\n\n'
            'Press ESC to cancel calibration at any time.'
        )
        
        if not result:
            return  # User cancelled
        
        # Wait 5 seconds for user to prepare
        print("[CanvasCalibration] Waiting 5 seconds for user to prepare...")
        self._root.update()
        self._root.after(5000, lambda: self._run_canvas_calibration(name, tool, canvas_x, canvas_y, canvas_w, canvas_h))
    
    def _run_canvas_calibration(self, name, tool, canvas_x, canvas_y, canvas_w, canvas_h):
        """Execute canvas calibration after preparation delay"""
        # Restore windows
        self._root.deiconify()
        self.parent.wm_state('normal')
        self._root.deiconify()
        self._root.wm_state('normal')
        
        # Run calibration
        calibration_results = self.bot.calibrate_canvas()
        
        # Restore windows after calibration
        self._root.deiconify()
        self.parent.wm_state('normal')
        self._root.wm_state('normal')
        self._root.deiconify()
        self._root.wm_state('normal')
        
        if calibration_results is None:
            messagebox.showerror(self.title, 'Canvas calibration failed!')
            return
        
        # Show results dialog
        scale_factor = calibration_results['scale_factor']
        measured_w, measured_h = calibration_results['measured_size']
        intended_w, intended_h = calibration_results['intended_size']
        calib_date = calibration_results['calibration_date']
        
        result = messagebox.askokcancel(
            'Canvas Calibration Results',
            f'Intended size: {intended_w}x{intended_h} pixels\n'
            f'Measured size: {measured_w}x{measured_h} pixels\n'
            f'Scale factor: {scale_factor:.3f} ({scale_factor*100:.1f}%)\n'
            f'Calibration date: {calib_date}\n\n'
            f'This means your canvas is zoomed to {scale_factor*100:.1f}%.\n\n'
            f'Future drawings will use this scale factor to adjust pixel size.\n\n'
            f'For example, if pixel size = 2 and scale = 0.76:\n'
            f'  Effective pixel size = 1.52\n'
            f'  Would you like to save this calibration?\n'
        )
        
        if result:  # User clicked OK
            # Save calibration to config
            self.tools['Canvas']['calibration'] = calibration_results
            
            # Update calibration status label
            calib_status = f"Scale: {scale_factor:.2f}% (Calibrated: {calib_date})"
            self._calib_status_label.config(text=calib_status)
            
            print(f"[CanvasCalibration] Calibration saved: scale_factor={scale_factor:.3f}")
        else:  # User clicked Cancel
            print("[CanvasCalibration] Calibration cancelled by user")
    
    def close(self):
        self._root.destroy()
        self.on_complete()


class InteractivePaletteExtractor:
    """Interactive palette extraction tool with anchor point placement and interpolation"""
    
    TEMP_FILE = 'palette_extraction_temp.json'
    
    def __init__(self, parent, bot, current_tool, tool_name, valid_positions, palette_box, on_complete):
        self._root = Toplevel(parent)
        self._parent = parent
        self.bot = bot
        self._current_tool = current_tool
        self._tool_name = tool_name
        self._valid_positions = valid_positions
        self._palette_box = palette_box
        self._on_complete = on_complete
        
        self._root.title('Interactive Palette Extraction')
        self._root.geometry('1000x700+100+100')
        
        # State management
        self._phase = 0  # 0: region, 1: grid, 2: anchors, 3: extract
        self._region = None
        self._rows = 0
        self._cols = 0
        self._anchors = {}  # {index: (x, y)} - anchor points (green)
        self._interpolated = {}  # {index: (x, y)} - interpolated points (yellow)
        self._palette_img = None
        self._preview_tk = None
        
        # Mouse listener
        self._listener = None
        
        # UI Layout
        self._setup_ui()
        
        # Try to restore from temp file
        self._try_restore()
        
        # Start with phase 1
        self._start_phase_1()
        
        # Window close handler
        self._root.protocol('WM_DELETE_WINDOW', self._on_close)
    
    def _setup_ui(self):
        """Setup main UI layout"""
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)  # Main content
        self._root.rowconfigure(1, weight=0)  # Controls
        
        # Main content frame
        self._content_frame = Frame(self._root)
        self._content_frame.grid(column=0, row=0, sticky='nsew', padx=10, pady=10)
        self._content_frame.columnconfigure(0, weight=1)
        self._content_frame.rowconfigure(0, weight=1)
        
        # Control frame
        self._control_frame = Frame(self._root)
        self._control_frame.grid(column=0, row=1, sticky='ew', padx=10, pady=5)
        self._control_frame.columnconfigure(0, weight=1)
        
        # Content canvas
        self._canvas = Canvas(self._content_frame, bg='white')
        self._canvas.grid(column=0, row=0, sticky='nsew')
    
    def _update_controls(self):
        """Update control buttons based on current phase"""
        # Clear existing controls
        for widget in self._control_frame.winfo_children():
            widget.destroy()
        
        # Define consistent button width
        button_width = 12
        
        if self._phase == 1:  # Region selection
            status_label = Label(self._control_frame,
                text='Phase 1: Click upper-left and bottom-right corners of palette region')
            status_label.grid(column=0, row=0, pady=5)
        
        elif self._phase == 2:  # Grid configuration
            # Grid dimension inputs frame for better organization
            dim_frame = Frame(self._control_frame)
            dim_frame.grid(column=0, row=0, sticky='w')
            
            Label(dim_frame, text='Rows:').pack(side='left', padx=(0, 4))
            self._rows_entry = Entry(dim_frame, width=6)
            self._rows_entry.pack(side='left', padx=(0, 12))
            if self._rows > 0:
                self._rows_entry.insert(0, str(self._rows))
            
            Label(dim_frame, text='Cols:').pack(side='left', padx=(0, 4))
            self._cols_entry = Entry(dim_frame, width=6)
            self._cols_entry.pack(side='left', padx=(0, 12))
            if self._cols > 0:
                self._cols_entry.insert(0, str(self._cols))
            
            # Action buttons
            Button(self._control_frame, text='Set Grid', width=button_width,
                command=self._on_set_grid).grid(column=0, row=1, padx=5, pady=5, sticky='w')
            
            Button(self._control_frame, text='Back', width=button_width,
                command=self._back_to_phase_1).grid(column=1, row=1, padx=5, pady=5)
        
        elif self._phase == 3:  # Anchor placement
            # Status and anchor count frame
            status_frame = Frame(self._control_frame)
            status_frame.grid(column=0, row=0, sticky='w')
            
            required_anchors = self._get_required_anchors()
            anchor_count = len(self._anchors)
            status_text = f'Anchors: {anchor_count}/{required_anchors} required'
            status_label = Label(status_frame, text=status_text)
            status_label.pack(side='left', padx=(0, 10))
            
            # Action buttons
            Button(status_frame, text='Clear Anchors', width=button_width,
                command=self._clear_anchors).pack(side='left', padx=5)
            
            Button(status_frame, text='Back', width=button_width,
                command=self._back_to_phase_2).pack(side='left', padx=5)
            
            # Extract button in separate row
            Button(self._control_frame, text='Extract Colors', width=button_width,
                command=self._on_extract_colors).grid(column=0, row=1, padx=5, pady=5, sticky='w')
        
        elif self._phase == 4:  # Complete
            Button(self._control_frame, text='Close', width=button_width,
                command=self._on_close).grid(column=0, row=0, pady=5)
    
    def _start_phase_1(self):
        """Start phase 1: Region selection"""
        self._phase = 1
        self._update_controls()
        
        # Show instructions first
        result = messagebox.askokcancel(
            'Phase 1: Region Selection',
            'Click on your palette to define the extraction region:\n\n'
            '1. Click the UPPER-LEFT corner of your palette\n'
            '2. Click the BOTTOM-RIGHT corner of your palette\n\n'
            'The selected area will be captured and displayed.\n\n'
            'Click OK to begin, then click the corners on your palette.'
        )
        
        if not result:
            return  # User cancelled
        
        # Clear canvas
        self._canvas.delete('all')
        
        # Instructions on canvas
        self._canvas.create_text(
            400, 300,
            text='Click UPPER-LEFT corner of palette,\nthen click BOTTOM-RIGHT corner.',
            font=('Arial', 14, 'bold'),
            fill='#333333'
        )
        
        # Start mouse listener
        self._coords = []
        self._clicks = 0
        self._required_clicks = 2
        
        self._listener = Listener(on_click=self._on_region_click)
        self._listener.start()
        
        # Minimize windows for clicking
        self._root.iconify()
        self._parent.iconify()
    
    def _on_region_click(self, x, y, button, pressed):
        """Handle click for region selection"""
        if pressed:
            self._root.bell()
            print(x, y)
            self._clicks += 1
            self._coords += x, y
            
            if self._clicks == self._required_clicks:
                # Determine corner coordinates
                top_left = (min(self._coords[0], self._coords[2]), 
                            min(self._coords[1], self._coords[3]))
                bot_right = (max(self._coords[0], self._coords[2]), 
                            max(self._coords[1], self._coords[3]))
                self._region = (top_left[0], top_left[1], bot_right[0], bot_right[1])
                
                print(f'Captured region: {self._region}')
                
                # Capture palette image
                self._capture_palette()
                
                # Stop listener and restore windows
                self._listener.stop()
                self._parent.deiconify()
                self._parent.wm_state('normal')
                self._root.deiconify()
                self._root.wm_state('normal')
                
                # Save and move to phase 2
                self._save_temp()
                self._start_phase_2()
    
    def _capture_palette(self):
        """Capture palette image from selected region"""
        try:
            palette_img = ImageGrab.grab(self._region)
            self._palette_img = palette_img
            
            # Display on canvas
            self._canvas.delete('all')
            
            # Calculate display size
            canvas_w = self._canvas.winfo_width()
            canvas_h = self._canvas.winfo_height()
            
            # Resize to fit canvas
            img_w, img_h = palette_img.size
            scale = min(canvas_w / img_w, canvas_h / img_h) * 0.9
            display_w = int(img_w * scale)
            display_h = int(img_h * scale)
            
            self._palette_display_img = ImageTk.PhotoImage(
                palette_img.resize((display_w, display_h))
            )
            
            # Center image on canvas
            x_offset = (canvas_w - display_w) // 2
            y_offset = (canvas_h - display_h) // 2
            
            self._canvas.create_image(x_offset, y_offset, 
                image=self._palette_display_img, anchor='nw')
            
            # Store display parameters for later
            self._display_scale = scale
            self._display_offset = (x_offset, y_offset)
            
        except Exception as e:
            messagebox.showerror('Capture Error', f'Failed to capture palette: {str(e)}')
    
    def _start_phase_2(self):
        """Start phase 2: Grid configuration"""
        self._phase = 2
        self._update_controls()
    
    def _on_set_grid(self):
        """Handle grid dimension input"""
        try:
            rows = int(self._rows_entry.get())
            cols = int(self._cols_entry.get())
            
            if rows < 1 or cols < 1:
                messagebox.showerror('Invalid Grid', 'Rows and columns must be at least 1')
                return
            
            self._rows = rows
            self._cols = cols
            
            # Save and move to phase 3
            self._save_temp()
            self._start_phase_3()
            
        except ValueError:
            messagebox.showerror('Invalid Input', 'Please enter valid numbers for rows and columns')
    
    def _start_phase_3(self):
        """Start phase 3: Anchor placement"""
        self._phase = 3
        self._anchors = {}
        self._interpolated = {}
        self._update_controls()
        
        # Redraw palette with grid overlay
        self._draw_palette_with_grid()
    
    def _draw_palette_with_grid(self):
        """Draw palette image with grid overlay"""
        self._canvas.delete('all')
        
        # Redraw palette image
        x_offset, y_offset = self._display_offset
        self._canvas.create_image(x_offset, y_offset, 
            image=self._palette_display_img, anchor='nw')
        
        # Draw grid lines
        palette_w, palette_h = self._palette_img.size
        display_w = int(palette_w * self._display_scale)
        display_h = int(palette_h * self._display_scale)
        
        cell_w = display_w / self._cols
        cell_h = display_h / self._rows
        
        # Vertical lines
        for i in range(self._cols + 1):
            x = x_offset + i * cell_w
            self._canvas.create_line(x, y_offset, x, y_offset + display_h, 
                fill='lightgray', dash=(2, 2))
        
        # Horizontal lines
        for i in range(self._rows + 1):
            y = y_offset + i * cell_h
            self._canvas.create_line(x_offset, y, x_offset + display_w, y, 
                fill='lightgray', dash=(2, 2))
        
        # Draw cell numbers
        for i in range(self._rows * self._cols):
            row = i // self._cols
            col = i % self._cols
            
            cell_x = x_offset + col * cell_w + cell_w / 2
            cell_y = y_offset + row * cell_h + cell_h / 2
            
            self._canvas.create_text(cell_x, cell_y, 
                text=str(i + 1), font=('Arial', 10), fill='gray')
        
        # Draw anchor points
        for idx, (rel_x, rel_y) in self._anchors.items():
            display_x = x_offset + rel_x * self._display_scale
            display_y = y_offset + rel_y * self._display_scale
            self._canvas.create_oval(display_x - 6, display_y - 6, 
                display_x + 6, display_y + 6, 
                fill='green', outline='darkgreen', width=2)
            self._canvas.create_text(display_x, display_y - 15, 
                text=str(idx + 1), font=('Arial', 10, 'bold'), fill='green')
        
        # Draw interpolated points
        for idx, (rel_x, rel_y) in self._interpolated.items():
            if idx not in self._anchors:  # Don't draw anchors twice
                display_x = x_offset + rel_x * self._display_scale
                display_y = y_offset + rel_y * self._display_scale
                self._canvas.create_oval(display_x - 4, display_y - 4, 
                    display_x + 4, display_y + 4, 
                    fill='yellow', outline='orange', width=1)
        
        # Bind click for anchor placement
        self._canvas.bind('<Button-1>', self._on_canvas_click)
    
    def _on_canvas_click(self, event):
        """Handle click on canvas for anchor placement"""
        # Convert screen coordinates to palette-relative coordinates
        x_offset, y_offset = self._display_offset
        rel_x = (event.x - x_offset) / self._display_scale
        rel_y = (event.y - y_offset) / self._display_scale
        
        # Determine which cell was clicked
        palette_w, palette_h = self._palette_img.size
        cell_w = palette_w / self._cols
        cell_h = palette_h / self._rows
        
        col = int(rel_x / cell_w)
        row = int(rel_y / cell_h)
        
        if col < 0 or col >= self._cols or row < 0 or row >= self._rows:
            return  # Clicked outside grid
        
        clicked_idx = row * self._cols + col
        
        # Check if clicking on existing anchor to remove it
        if clicked_idx in self._anchors:
            del self._anchors[clicked_idx]
            print(f'Removed anchor at position {clicked_idx + 1}')
        else:
            # Ask user which grid cell this anchor should represent
            result = simpledialog.askstring(
                'Specify Grid Cell',
                f'You clicked at grid position {clicked_idx + 1}.\n\n'
                f'Enter the grid cell number (1-{self._rows * self._cols})\n'
                f'to place this anchor point at.\n\n'
                f'Leave empty to cancel.'
            )
            
            if not result:
                return  # User cancelled
            
            try:
                target_idx = int(result) - 1  # Convert to 0-based index
                
                if target_idx < 0 or target_idx >= self._rows * self._cols:
                    messagebox.showerror(
                        'Invalid Grid Cell',
                        f'Grid cell must be between 1 and {self._rows * self._cols}'
                    )
                    return
                
                # Add anchor at the clicked position, linked to the target grid cell
                self._anchors[target_idx] = (rel_x, rel_y)
                print(f'Added anchor for position {target_idx + 1}: ({rel_x:.1f}, {rel_y:.1f})')
                
            except ValueError:
                messagebox.showerror(
                    'Invalid Input',
                    'Please enter a valid number for the grid cell.'
                )
                return
        
        # Recalculate interpolation
        self._recalculate_interpolation()
        
        # Redraw
        self._draw_palette_with_grid()
        
        # Update status
        self._update_controls()
        
        # Save
        self._save_temp()
    
    def _get_required_anchors(self):
        """Get minimum number of required anchors based on grid"""
        if self._rows == 1 or self._cols == 1:
            return 2  # 1D grid: first and last
        else:
            return 4  # 2D grid: 4 corners
    
    def _get_corner_indices(self):
        """Get indices of corner positions based on grid"""
        if self._rows == 1:
            # Single row: first and last
            return [0, self._cols - 1]
        elif self._cols == 1:
            # Single column: first and last
            return [0, (self._rows - 1) * self._cols]
        else:
            # 2D grid: 4 corners
            top_left = 0
            top_right = self._cols - 1
            bottom_left = (self._rows - 1) * self._cols
            bottom_right = self._rows * self._cols - 1
            return [top_left, top_right, bottom_left, bottom_right]
    
    def _recalculate_interpolation(self):
        """Recalculate interpolated positions from anchors"""
        self._interpolated = {}
        
        required_anchors = self._get_required_anchors()
        if len(self._anchors) < required_anchors:
            return  # Not enough anchors
        
        palette_w, palette_h = self._palette_img.size
        cell_w = palette_w / self._cols
        cell_h = palette_h / self._rows
        
        if self._rows == 1 or self._cols == 1:
            # 1D interpolation
            corners = self._get_corner_indices()
            if corners[0] in self._anchors and corners[1] in self._anchors:
                first_anchor = self._anchors[corners[0]]
                last_anchor = self._anchors[corners[1]]
                
                if self._rows == 1:
                    # Single row: interpolate horizontally
                    for col in range(1, self._cols - 1):
                        idx = col
                        if idx not in self._anchors:
                            t = col / (self._cols - 1)
                            x = first_anchor[0] + t * (last_anchor[0] - first_anchor[0])
                            y = first_anchor[1] + t * (last_anchor[1] - first_anchor[1])
                            self._interpolated[idx] = (x, y)
                else:
                    # Single column: interpolate vertically
                    for row in range(1, self._rows - 1):
                        idx = row * self._cols
                        if idx not in self._anchors:
                            t = row / (self._rows - 1)
                            x = first_anchor[0] + t * (last_anchor[0] - first_anchor[0])
                            y = first_anchor[1] + t * (last_anchor[1] - first_anchor[1])
                            self._interpolated[idx] = (x, y)
        else:
            # 2D bilinear interpolation
            corners = self._get_corner_indices()
            if all(c in self._anchors for c in corners):
                tl = self._anchors[corners[0]]  # top-left
                tr = self._anchors[corners[1]]  # top-right
                bl = self._anchors[corners[2]]  # bottom-left
                br = self._anchors[corners[3]]  # bottom-right
                
                for row in range(self._rows):
                    for col in range(self._cols):
                        idx = row * self._cols + col
                        if idx not in self._anchors:
                            # Bilinear interpolation
                            t_row = row / (self._rows - 1) if self._rows > 1 else 0
                            t_col = col / (self._cols - 1) if self._cols > 1 else 0
                            
                            # Interpolate top edge
                            top_x = tl[0] + t_col * (tr[0] - tl[0])
                            top_y = tl[1] + t_col * (tr[1] - tl[1])
                            
                            # Interpolate bottom edge
                            bottom_x = bl[0] + t_col * (br[0] - bl[0])
                            bottom_y = bl[1] + t_col * (br[1] - bl[1])
                            
                            # Interpolate between top and bottom
                            x = top_x + t_row * (bottom_x - top_x)
                            y = top_y + t_row * (bottom_y - top_y)
                            
                            self._interpolated[idx] = (x, y)
    
    def _clear_anchors(self):
        """Clear all anchor points"""
        if messagebox.askyesno('Clear Anchors', 
                'Clear all anchor points? This cannot be undone.'):
            self._anchors = {}
            self._interpolated = {}
            self._draw_palette_with_grid()
            self._update_controls()
            self._save_temp()
    
    def _back_to_phase_2(self):
        """Go back to grid configuration"""
        self._phase = 2
        self._update_controls()
        self._save_temp()
    
    def _back_to_phase_1(self):
        """Go back to region selection"""
        self._phase = 1
        self._update_controls()
        self._save_temp()
        self._start_phase_1()
    
    def _on_extract_colors(self):
        """Extract colors and complete"""
        required_anchors = self._get_required_anchors()
        if len(self._anchors) < required_anchors:
            messagebox.showerror('Insufficient Anchors', 
                f'Need at least {required_anchors} anchor points. '
                f'Currently have {len(self._anchors)}.')
            return
        
        # Combine anchors and interpolated points
        self._manual_centers = {}
        self._manual_centers.update(self._anchors)
        self._manual_centers.update(self._interpolated)
        
        # Filter to valid positions only
        filtered_centers = {}
        for idx in self._valid_positions:
            if idx in self._manual_centers:
                filtered_centers[idx] = self._manual_centers[idx]
        
        print(f'Extracted {len(filtered_centers)} color centers')
        
        # Clean up temp file
        try:
            import os
            if os.path.exists(self.TEMP_FILE):
                os.remove(self.TEMP_FILE)
                print(f'Cleaned up temp file: {self.TEMP_FILE}')
        except Exception as e:
            print(f'Failed to remove temp file: {e}')
        
        # Close window and return results
        self._root.destroy()
        self._on_complete(filtered_centers)
    
    def _save_temp(self):
        """Save current state to temp file"""
        try:
            state = {
                'phase': self._phase,
                'region': self._region,
                'rows': self._rows,
                'cols': self._cols,
                'anchors': self._anchors,
                'interpolated': self._interpolated
            }
            
            with open(self.TEMP_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f'Saved state to {self.TEMP_FILE}')
        except Exception as e:
            print(f'Failed to save temp file: {e}')
    
    def _try_restore(self):
        """Try to restore state from temp file"""
        try:
            if os.path.exists(self.TEMP_FILE):
                if messagebox.askyesno('Restore Session', 
                        'Found saved extraction session. Restore it?'):
                    with open(self.TEMP_FILE, 'r') as f:
                        state = json.load(f)
                    
                    self._phase = state.get('phase', 0)
                    self._region = state.get('region')
                    self._rows = state.get('rows', 0)
                    self._cols = state.get('cols', 0)
                    self._anchors = {int(k): tuple(v) for k, v in state.get('anchors', {}).items()}
                    self._interpolated = {int(k): tuple(v) for k, v in state.get('interpolated', {}).items()}
                    
                    print(f'Restored state from phase {self._phase}')
                    
                    # Restore to appropriate phase
                    if self._phase >= 2 and self._region:
                        self._capture_palette()
                    if self._phase >= 3:
                        self._draw_palette_with_grid()
                    self._update_controls()
        except Exception as e:
            print(f'Failed to restore: {e}')
    
    def _on_close(self):
        """Handle window close"""
        # Save state even when closing
        self._save_temp()
        self._root.destroy()
        # Call on_complete with None to indicate cancellation
        self._on_complete(None)
