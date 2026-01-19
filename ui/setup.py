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
        self._root.rowconfigure(0, weight=1, uniform='row')
        self._root.rowconfigure(1, weight=1, uniform='row')
        
        self._tools_panel = self._init_tools_panel()
        self._tools_panel.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')

        self._preview_panel = self._init_preview_panel()
        self._preview_panel.grid(column=0, row=1, sticky='nsew', padx=5, pady=5)

    def _init_tools_panel(self):
        frame = LabelFrame(self._root, text='Tools')

        for i in range(2):
            frame.columnconfigure(i, weight=1, uniform='column')
        frame.columnconfigure(2, weight=2, uniform='column')
        for i in range(3):
            frame.rowconfigure(i, weight=1, uniform='row')

        self._statuses = {}

        for idt, (k, v) in enumerate(self.tools.items()):
            # Use the 'name' field for display if it exists, otherwise use the key
            display_name = v.get('name', k) if isinstance(v, dict) else k
            Label(frame, text=display_name, font=SetupWindow.TITLE_FONT).grid(column=0, row=idt, sticky='w', padx=5, pady=5)
            status = Label(
                frame, 
                text='INITIALIZED' if v['status'] else 'NOT INITIALIZED', 
                foreground='white', 
                background='green' if v['status'] else 'red',
                justify='center',
                anchor='center'
            )
            status.grid(column=1, row=idt, sticky='ew', padx=10)
            self._statuses[k] = status

            settings_frame = Frame(frame)
            for i in range(4):
                settings_frame.columnconfigure(i, weight=1, uniform='column')
            settings_frame.rowconfigure(0, weight=1, uniform='row')

            # Do not write the callback as "lambda : self._start_listening(tool)" as this will cause only the last tool to be registered in every callback
            # Instead, do "lambda t=tool : self._start_listening(t)" which will pass the tool of the current iteration for every new callback.
            # (Note that t here stores the current tool as a default argument)
            Button(settings_frame, text='Initialize', command=lambda n=k, t=v : self._start_listening(n, t)).grid(column=0, columnspan=2, row=0, sticky='ew', padx=5, pady=5)
            
            if k == 'New Layer' or k == 'Color Button' or k == 'Color Button Okay':
                # Create modifier checkboxes (CTRL, ALT, SHIFT)
                from tkinter import Checkbutton, IntVar
                self._mod_vars = getattr(self, '_mod_vars', {})
                mv = {}
                mods = v.get('modifiers', {}) if isinstance(v, dict) else {}
                for ci, name in enumerate(('ctrl', 'alt', 'shift')):
                    iv = IntVar()
                    iv.set(1 if mods.get(name, False) else 0)
                    # FIXED: Capture k as default argument tk to avoid lambda closure bug
                    cb = Checkbutton(settings_frame, text=name.upper(), variable=iv,
                                     command=lambda tk=k, n=name, iv=iv: self._on_modifier_toggle(tk, n, iv))
                    cb.grid(column=2 + ci, row=0, padx=2, sticky='w')
                    mv[name] = iv
                self._mod_vars[k] = mv
            elif k == 'color_preview_spot':
                # Color preview spot doesn't need any extra buttons (no modifiers, no preview)
                pass
            else:
                Button(settings_frame, text='Preview', command=lambda n=k : self._set_preview(n)).grid(column=2, columnspan=1, row=0, sticky='ew', padx=2, pady=5)
                
                # Add Manual Color Selection button for Palette
                if k == 'Palette':
                    Button(settings_frame, text='Edit Colors', command=lambda n=k, t=v : self._start_manual_color_selection(n, t)).grid(column=3, columnspan=1, row=0, sticky='ew', padx=2, pady=5)

            if k == 'Palette':
                settings_frame.rowconfigure(1, weight=1, uniform='row')

                Label(settings_frame, text='Rows').grid(column=0, row=1, padx=5, pady=5)
                self._erows = Entry(settings_frame, width=5)
                self._erows.grid(column=1, row=1, padx=5, pady=5)
                Label(settings_frame, text='Columns').grid(column=2, row=1, padx=5, pady=5)
                self._ecols = Entry(settings_frame, width=5)
                self._ecols.grid(column=3, row=1, padx=5, pady=5)

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
                settings_frame.rowconfigure(1, weight=1, uniform='row')

                Label(settings_frame, text='Delay (s)').grid(column=0, row=1, padx=5, pady=5)
                self._edelay = Entry(settings_frame, width=8)
                self._edelay.grid(column=1, row=1, padx=5, pady=5)

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

            elif k == 'Color Button Okay':
                settings_frame.rowconfigure(1, weight=1, uniform='row')

                from tkinter import Checkbutton, IntVar
                self._enable_vars = getattr(self, '_enable_vars', {})
                ev = IntVar()
                ev.set(1 if v.get('enabled', False) else 0)
                cb = Checkbutton(settings_frame, text='Enable', variable=ev,
                             command=lambda n=k, ev=ev: self._on_enable_toggle(n, ev))
                cb.grid(column=0, row=1, columnspan=4, padx=5, pady=5, sticky='w')
                self._enable_vars[k] = ev

            settings_frame.grid(column=2, row=idt, sticky='nsew')
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
        self._color_sel_window.rowconfigure(0, weight=0)  # Instructions and mode
        self._color_sel_window.rowconfigure(1, weight=1)  # Grid
        
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
        instructions.grid(column=0, row=0, padx=10, pady=10, sticky='ew')
        
        # Mode buttons
        mode_frame = Frame(self._color_sel_window)
        mode_frame.grid(column=0, row=0, padx=10, pady=5, sticky='e')
        
        self._mode_btn_toggle = Button(mode_frame, text='Toggle Valid/Invalid', command=self._set_toggle_mode)
        self._mode_btn_toggle.pack(side='left', padx=5)
        
        self._mode_btn_pick = Button(mode_frame, text='Pick Centers', command=self._set_pick_centers_mode)
        self._mode_btn_pick.pack(side='left', padx=5)
        
        # Scrollable frame for grid
        canvas = Canvas(self._color_sel_window)
        scrollbar = Scrollbar(self._color_sel_window, orient='vertical', command=canvas.yview)
        scrollable_frame = Frame(canvas)
        
        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(column=0, row=1, sticky='nsew', padx=10, pady=10)
        scrollbar.grid(column=1, row=1, sticky='ns', pady=10)
        
        # Create grid cells
        self._grid_buttons = {}
        # Note: self._valid_positions is already loaded above from config
        
        # Load palette preview image
        try:
            palette_img = Image.open(self._current_tool['preview'])
            self._palette_img_tk = ImageTk.PhotoImage(palette_img)
            
            # Display palette image as reference
            img_label = Label(scrollable_frame, image=self._palette_img_tk)
            img_label.grid(column=0, row=0, columnspan=self.cols, padx=5, pady=5)
            
            current_row = 1
        except:
            current_row = 0
            self._palette_img_tk = None
        
        # Create clickable grid cells
        for i in range(self.rows * self.cols):
            row = i // self.cols
            col = i % self.cols
            
            # Use tkLabel (tkinter.Label) for better color control (can change background)
            lbl = tkLabel(
                scrollable_frame,
                text=f'{i+1}',
                width=8,
                relief='raised',
                borderwidth=2,
                cursor='hand2'
            )
            lbl.bind('<Button-1>', lambda e, idx=i: self._toggle_grid_cell(idx))
            # Set initial color based on valid/invalid state
            if i in self._valid_positions:
                lbl.config(bg='lightgreen')
            else:
                lbl.config(bg='mistyrose')
            lbl.grid(column=col, row=current_row + row, padx=2, pady=2)
            self._grid_buttons[i] = lbl
        
        # Done button
        done_frame = Frame(self._color_sel_window)
        done_frame.grid(column=0, row=2, padx=10, pady=10, sticky='ew')
        
        Button(
            done_frame,
            text='Done',
            command=self._on_color_selection_done
        ).pack(side='left', padx=5)
        
        Button(
            done_frame,
            text='Auto-Estimate Centers',
            command=self._auto_estimate_centers
        ).pack(side='left', padx=5)
        
        Button(
            done_frame,
            text='Precision Estimate',
            command=self._start_precision_estimate
        ).pack(side='left', padx=5)
        
        Button(
            done_frame,
            text='Show Custom Centers',
            command=self._show_custom_centers_overlay
        ).pack(side='left', padx=5)
        
        Button(
            done_frame,
            text='Select All',
            command=self._select_all_colors
        ).pack(side='left', padx=5)
        
        Button(
            done_frame,
            text='Deselect All',
            command=self._deselect_all_colors
        ).pack(side='left', padx=5)
        
        Button(
            done_frame,
            text='Cancel',
            command=lambda: self._color_sel_window.destroy()
        ).pack(side='left', padx=5)
        
        # Bind ESC key to cancel picking on the parent window (works even when color window is minimized)
        self.parent.bind('<Escape>', lambda e: self._on_escape_press(e))
    
    def _toggle_grid_cell(self, index):
        """Toggle a grid cell between valid and invalid"""
        if index in self._valid_positions:
            self._valid_positions.remove(index)
            self._grid_buttons[index].config(bg='mistyrose')
        else:
            self._valid_positions.add(index)
            self._grid_buttons[index].config(bg='lightgreen')
    
    def _select_all_colors(self):
        """Select all grid cells as valid"""
        self._valid_positions = set(range(self.rows * self.cols))
        for i, btn in self._grid_buttons.items():
            btn.config(bg='lightgreen')
    
    def _deselect_all_colors(self):
        """Deselect all grid cells"""
        self._valid_positions = set()
        for i, btn in self._grid_buttons.items():
            btn.config(bg='mistyrose')
    
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
        # Update grid to show valid/invalid toggle AND rebind click handler
        for i, lbl in self._grid_buttons.items():
            if i in self._valid_positions:
                lbl.config(bg='lightgreen', cursor='hand2', text=f'{i+1}')
            else:
                lbl.config(bg='mistyrose', cursor='hand2', text=f'{i+1}')
            # Rebind click handler to toggle mode function
            lbl.unbind('<Button-1>')
            lbl.bind('<Button-1>', lambda e, idx=i: self._toggle_grid_cell(idx))
    
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
        for i, lbl in self._grid_buttons.items():
            if i in self._manual_centers:
                lbl.config(bg='yellow', text='✓')
            else:
                lbl.config(bg='white', text=f'{i+1}')
            lbl.unbind('<Button-1>')
            lbl.bind('<Button-1>', lambda e, idx=i: self._pick_center(idx))
    
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
            
            # Update the grid cell to show it has a center (show both number and checkmark)
            if i in self._grid_buttons:
                self._grid_buttons[i].config(bg='yellow', text=f'{i+1} ✓')
        
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
            # Update grid to show extracted centers
            for i, lbl in self._grid_buttons.items():
                if i in self._manual_centers:
                    lbl.config(bg='yellow', text=f'{i+1} ✓')
                else:
                    lbl.config(bg='mistyrose', text=f'{i+1}')
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
                
                # Update the grid cell to show it has a center
                if self._current_picking_index in self._grid_buttons:
                    self._grid_buttons[self._current_picking_index].config(bg='yellow', text='✓')
                
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
        """Update delay value and validate on focus out or return"""
        try:
            value = event.widget.get()
            if value == '':
                # Default to 0.1 if empty
                event.widget.delete(0, END)
                event.widget.insert(0, '0.1')
                clamped = 0.1
            else:
                num = float(value)
                # Clamp to valid range
                clamped = max(0.01, min(5.0, num))
                if clamped != num:
                    event.widget.delete(0, END)
                    event.widget.insert(0, str(clamped))
            # Update tools dict with delay value
            self.tools['Color Button']['delay'] = clamped
        except ValueError:
            # If invalid, reset to default
            event.widget.delete(0, END)
            event.widget.insert(0, '0.1')
            self.tools['Color Button']['delay'] = 0.1

    def _on_enable_toggle(self, tool_name, intvar):
        # Update stored tools dict enabled state for given tool
        try:
            if tool_name in self.tools:
                self.tools[tool_name]['enabled'] = bool(intvar.get())
        except Exception:
            pass

    def _on_modifier_toggle(self, tool_name, modifier_name, intvar):
        # Update the stored tools dict modifiers for the given tool
        try:
            if tool_name in self.tools:
                if 'modifiers' not in self.tools[tool_name] or not isinstance(self.tools[tool_name]['modifiers'], dict):
                    self.tools[tool_name]['modifiers'] = {}
                self.tools[tool_name]['modifiers'][modifier_name] = bool(intvar.get())
        except Exception:
            pass

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
        
        if self._phase == 1:  # Region selection
            status_label = Label(self._control_frame, 
                text='Phase 1: Click upper-left and bottom-right corners of palette region')
            status_label.grid(column=0, row=0, pady=5)
        
        elif self._phase == 2:  # Grid configuration
            # Grid dimension inputs
            Label(self._control_frame, text='Rows:').grid(column=0, row=0, sticky='w', padx=5)
            self._rows_entry = Entry(self._control_frame, width=5)
            self._rows_entry.grid(column=1, row=0, padx=5)
            if self._rows > 0:
                self._rows_entry.insert(0, str(self._rows))
            
            Label(self._control_frame, text='Cols:').grid(column=2, row=0, sticky='w', padx=5)
            self._cols_entry = Entry(self._control_frame, width=5)
            self._cols_entry.grid(column=3, row=0, padx=5)
            if self._cols > 0:
                self._cols_entry.insert(0, str(self._cols))
            
            Button(self._control_frame, text='Set Grid', 
                command=self._on_set_grid).grid(column=4, row=0, padx=5)
            
            Button(self._control_frame, text='Back to Region', 
                command=self._back_to_phase_1).grid(column=5, row=0, padx=5)
        
        elif self._phase == 3:  # Anchor placement
            # Status and anchor count
            required_anchors = self._get_required_anchors()
            anchor_count = len(self._anchors)
            status_text = f'Anchors: {anchor_count}/{required_anchors} required'
            status_label = Label(self._control_frame, text=status_text)
            status_label.grid(column=0, row=0, pady=5)
            
            Button(self._control_frame, text='Clear Anchors', 
                command=self._clear_anchors).grid(column=1, row=0, padx=5)
            
            Button(self._control_frame, text='Back to Grid', 
                command=self._back_to_phase_2).grid(column=2, row=0, padx=5)
            
            Button(self._control_frame, text='Extract Colors', 
                command=self._on_extract_colors).grid(column=3, row=0, padx=5)
        
        elif self._phase == 4:  # Complete
            Button(self._control_frame, text='Close', 
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
