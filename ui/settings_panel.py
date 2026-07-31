"""
SettingsPanel — drawing settings, misc options, and feature toggles.

Extracted from Window._init_cpanel (the non-button portion) together with
the callbacks that operate on these widgets: _on_check, _on_slider_move,
the entry-field handlers, and the feature-toggle handlers. The panel owns
the shared UI state that Window exposes via properties:
``draw_options`` (bot flag int) and ``mode`` (draw mode string).
"""

from tkinter import END, StringVar, DoubleVar, IntVar, font
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label, OptionMenu, Scale


class SettingsPanel(Frame):
    """Drawing settings: mode selector, sliders, misc options, toggles."""

    _SLIDER_TOOLTIPS = (
        'Affects the delay (more accurately duration) for each stroke. ' +
        'Increase the delay if your machine is slow and does not respond well to extremely fast input',

        'For more detailed results, reduce the pixel size. Remember that lower pixel sizes imply longer draw times.' +
        'This setting does not affect the botted application\'s brush size. You must do that manually.',

        'Affects custom color accuracy for each pixel. ' +
        'At lower values, the color variety of the result will be greatly reduced. ' +
        'At 1.0 accuracy, every pixel will have perfect colors ' +
        'Recommended setting: 0.9',

        'Adds delay when cursor jumps more than 5 pixels between strokes. ' +
        'Helps prevent unintended strokes from rapid cursor movement. ' +
        'Recommended: 0.5 seconds'
    )

    _MISC_TOOLTIPS = (
        'Ignores and does not draw the white pixels of an image. Useful for when the canvas is white.',
        'Use custom colors. This option considerably lengthens the draw duration.'
    )

    def __init__(self, parent, controller, config):
        super().__init__(parent)
        self._controller = controller  # duck-typed Window
        self._config = config
        self._bot = controller.bot

        std_font = font.nametofont('TkDefaultFont').actual()
        self.TITLE_FONT = (std_font['family'], std_font['size'], 'bold')

        # Shared UI state (exposed to Window via properties)
        self.draw_options = 0
        self.mode = None

        self._build()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _build(self):
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        for i in range(20):
            self.rowconfigure(i, weight=1)

        curr_row = 0

        # Draw mode
        self._teclbl = Label(self, text='Draw Mode', font=self.TITLE_FONT)
        self._teclbl.grid(column=0, row=curr_row, columnspan=2, sticky='w', padx=5, pady=5)
        curr_row += 1
        modes = [self._bot.SLOTTED, self._bot.LAYERED, self._bot.SINGLE_COLOR]
        self._tecvar = StringVar()
        self._tecvar.set(modes[1])
        self.mode = modes[1]
        self._teclst = OptionMenu(self, self._tecvar, self.mode, *modes, command=self._update_mode)
        self._teclst.grid(column=0, row=curr_row, columnspan=2, sticky='ew', padx=5, pady=5)
        curr_row += 1

        self._single_color_btn = Button(self, text='Configure Single Color',
                                        command=self._controller._open_single_color_window)
        self._single_color_btn.grid(column=0, row=curr_row, columnspan=2, sticky='ew', padx=5, pady=5)
        self._single_color_btn.grid_remove()
        curr_row += 1

        # For every slider option, layout is (name, default, from, to)
        defaults = self._bot.settings
        self._options = (
            ('Delay', defaults[0], 0, 1),
            ('Pixel Size', defaults[1], 1, 50),
            ('Precision', defaults[2], 0, 1),
            ('Jump Delay', defaults[3] if len(defaults) > 3 else 0.5, 0, 2),
        )
        size = len(self._options)
        # Use IntVar for Pixel Size (index 1), DoubleVar for others
        self._optvars = []
        for i in range(size):
            if i == 1:  # Pixel Size
                self._optvars.append(IntVar())
            else:
                self._optvars.append(DoubleVar())

        self._optlabl = []
        for i, o in enumerate(self._options):
            if i == 1:  # Pixel Size - show as integer
                self._optlabl.append(Label(self, text=f"{o[0]}: {int(o[1])}", font=self.TITLE_FONT))
            else:
                self._optlabl.append(Label(self, text=f"{o[0]}: {o[1]:.2f}", font=self.TITLE_FONT))

        # Create sliders for all options except Delay (index 0)
        self._optslid = []
        for i in range(size):
            if i == 0:  # Skip Delay - will use Entry field instead
                self._optslid.append(None)
            else:
                self._optslid.append(Scale(
                    self,
                    from_=self._options[i][2],
                    to=self._options[i][3],
                    variable=self._optvars[i],
                    command=lambda val, index=i: self._on_slider_move(index, val)
                ))

        # Delay Entry field (replaces slider for index 0)
        self._delay_var = StringVar()
        self._delay_entry = Entry(self, textvariable=self._delay_var, width=10)
        self._delay_entry.bind('<Return>', self._on_delay_entry_change)
        self._delay_entry.bind('<FocusOut>', self._on_delay_entry_change)

        # Grid all widgets
        for i in range(size):
            self._optlabl[i].grid(column=0, row=(i * 2) + curr_row, columnspan=2, padx=5, pady=5, sticky='w')
            if i == 0:  # Delay - use Entry field
                self._delay_entry.grid(column=0, row=(i * 2) + curr_row + 1, columnspan=2, padx=5, pady=5, sticky='ew')
            else:  # Other options - use sliders
                self._optslid[i].set(self._options[i][1])
                self._optslid[i].set(defaults[i])
                self._optslid[i].grid(column=0, row=(i * 2) + curr_row + 1, columnspan=2, padx=5, sticky='ew')
        curr_row += size * 2

        # Misc settings
        self._misclbl = Label(self, text='Misc Settings', font=self.TITLE_FONT)
        self._misclbl.grid(column=0, row=curr_row, columnspan=2, padx=5, pady=5, sticky='w')
        curr_row += 1

        misc_opt_names = ('Ignore white pixels', 'Use custom colors')
        self._checkbutton_vars = [IntVar() for _ in range(len(misc_opt_names))]
        options = [self._bot.IGNORE_WHITE, self._bot.USE_CUSTOM_COLORS]
        for i in range(len(misc_opt_names)):
            cb = Checkbutton(self, text=misc_opt_names[i], variable=self._checkbutton_vars[i],
                             command=lambda val=options[i], index=i: self._on_check(index, val))
            cb.grid(column=0, row=i + curr_row, columnspan=2, padx=5, sticky='w')
        curr_row += len(misc_opt_names)

        # Feature toggles: (label, checkbox text, variable, command)
        toggles = (
            ('New Layer', 'Enable New Layer', self._on_newlayer_toggle),
            ('Color Button', 'Enable Color Button', self._on_colorbutton_toggle),
            ('Skip First Color', 'Skip first color', self._on_skip_first_color_toggle),
            ('Path Optimization', 'Minimize cursor jumps', self._on_path_opt_toggle),
            ('Wait After Draw', 'Match jump delay to stroke time', self._on_wait_after_draw_toggle),
            ('MSPaint Mode', 'Enable double-click', self._on_mspaint_mode_toggle),
        )
        for label_text, cb_text, command in toggles:
            Label(self, text=label_text, font=self.TITLE_FONT).grid(
                column=0, row=curr_row, padx=5, pady=5, sticky='w')
            var = IntVar()
            cb = Checkbutton(self, text=cb_text, variable=var, command=command)
            cb.grid(column=1, row=curr_row, padx=5, pady=5, sticky='w')
            if label_text == 'New Layer':
                self._newlayer_var = var
            elif label_text == 'Color Button':
                self._colorbutton_var = var
                self._colorbutton_cb = cb
            elif label_text == 'Skip First Color':
                self._skip_first_color_var = var
            elif label_text == 'Path Optimization':
                self._path_opt_var = var
            elif label_text == 'Wait After Draw':
                self._wait_after_draw_var = var
            elif label_text == 'MSPaint Mode':
                self._mspaint_mode_var = var
            curr_row += 1

        # MSPaint Mode delay setting
        Label(self, text='MSPaint Delay (s)', font=self.TITLE_FONT).grid(
            column=0, row=curr_row, padx=5, pady=5, sticky='w')
        self._mspaint_delay_var = StringVar()
        self._mspaint_delay_entry = Entry(self, textvariable=self._mspaint_delay_var, width=5)
        self._mspaint_delay_entry.bind('<FocusOut>', self._on_mspaint_delay_change)
        self._mspaint_delay_entry.bind('<Return>', self._on_mspaint_delay_change)
        self._mspaint_delay_entry.grid(column=1, row=curr_row, padx=5, pady=5, sticky='ew')
        curr_row += 1

        # Pause Key Setting
        Label(self, text='Pause Key', font=self.TITLE_FONT).grid(column=0, row=curr_row, padx=5, pady=5, sticky='w')
        self._pause_key_entry = Entry(self)
        self._pause_key_entry.grid(column=1, row=curr_row, padx=5, pady=5, sticky='ew')
        self._pause_key_entry.bind('<Key>', self._on_pause_key_entry_press)
        curr_row += 1

        # Calibration Step Size Setting
        Label(self, text='Calib. Step', font=self.TITLE_FONT).grid(column=0, row=curr_row, padx=5, pady=5, sticky='w')
        self._calib_step_var = StringVar()
        self._calib_step_var.set('2')
        self._calib_step_entry = Entry(self, textvariable=self._calib_step_var, width=5)
        self._calib_step_entry.grid(column=1, row=curr_row, padx=5, pady=5, sticky='ew')
        self._calib_step_entry.bind('<FocusOut>', self._on_calib_step_change)
        self._calib_step_entry.bind('<Return>', self._on_calib_step_change)
        curr_row += 1

        # Jump Threshold Setting
        Label(self, text='Jump Thresh (px)', font=self.TITLE_FONT).grid(column=0, row=curr_row, padx=5, pady=5, sticky='w')
        self._jump_threshold_var = StringVar()
        self._jump_threshold_var.set('5')
        self._jump_threshold_entry = Entry(self, textvariable=self._jump_threshold_var, width=5)
        self._jump_threshold_entry.grid(column=1, row=curr_row, padx=5, pady=5, sticky='ew')
        self._jump_threshold_entry.bind('<FocusOut>', self._on_jump_threshold_change)
        self._jump_threshold_entry.bind('<Return>', self._on_jump_threshold_change)
        curr_row += 1

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _update_mode(self, selection):
        self.mode = selection
        if selection == self._bot.SINGLE_COLOR:
            self._single_color_btn.grid()
            if not self._bot.single_color_configured:
                self._controller._open_single_color_window()
        else:
            self._single_color_btn.grid_remove()

    def _on_check(self, index, option):
        self._controller._status.set(self._MISC_TOOLTIPS[index])
        # Bot options are updated with the newly toggled option
        if self._checkbutton_vars[index].get() == 1:  # 1 indicates checked
            self.draw_options |= option
        else:
            self.draw_options &= ~option

        # Save drawing options to config
        self._config.set_drawing_option('ignore_white_pixels', bool(self.draw_options & self._bot.IGNORE_WHITE))
        self._config.set_drawing_option('use_custom_colors', bool(self.draw_options & self._bot.USE_CUSTOM_COLORS))

    def _on_newlayer_toggle(self):
        enabled = bool(self._newlayer_var.get())
        self._bot.new_layer['enabled'] = enabled
        tool = self._config.get_tool('New Layer')
        if not tool:
            tool = {'status': False, 'coords': None, 'enabled': False,
                    'modifiers': {'ctrl': False, 'alt': False, 'shift': False}}
        tool['enabled'] = enabled
        self._config.set_tool('New Layer', tool)

    def _on_colorbutton_toggle(self):
        enabled = bool(self._colorbutton_var.get())
        self._bot.color_button['enabled'] = enabled
        tool = self._config.get_tool('Color Button')
        if not tool:
            tool = {'status': False, 'coords': None, 'enabled': False, 'delay': 0.1,
                    'modifiers': {'ctrl': False, 'alt': False, 'shift': False}}
        tool['enabled'] = enabled
        self._config.set_tool('Color Button', tool)

    def _on_skip_first_color_toggle(self):
        enabled = bool(self._skip_first_color_var.get())
        self._bot.skip_first_color = enabled
        self._config.set('skip_first_color', enabled)

    def _on_path_opt_toggle(self):
        enabled = bool(self._path_opt_var.get())
        self._bot.path_optimization = enabled
        self._config.set('path_optimization', enabled)

    def _on_wait_after_draw_toggle(self):
        enabled = bool(self._wait_after_draw_var.get())
        self._bot.wait_after_draw = enabled
        self._config.set('wait_after_draw', enabled)

    def _on_mspaint_mode_toggle(self):
        enabled = bool(self._mspaint_mode_var.get())
        self._bot.mspaint_mode['enabled'] = enabled
        tool = self._config.get_tool('MSPaint Mode')
        if not tool:
            tool = {'enabled': False, 'delay': 0.5}
        tool['enabled'] = enabled
        self._config.set_tool('MSPaint Mode', tool)

    def _on_mspaint_delay_change(self, event=None):
        """Handle changes to MSPaint Mode delay entry field with validation"""
        try:
            val_str = self._mspaint_delay_var.get().strip()
            if not val_str:
                return  # Empty input, don't update

            val = float(val_str)

            # Validate range: 0.01 to 5.0
            if val < 0.01:
                val = 0.01
                self._mspaint_delay_var.set(str(val))
            elif val > 5.0:
                val = 5.0
                self._mspaint_delay_var.set(str(val))

            # Update bot state
            self._bot.mspaint_mode['delay'] = round(val, 3)

            # Save to config
            tool = self._config.get_tool('MSPaint Mode')
            if not tool:
                tool = {'enabled': False, 'delay': 0.5}
            tool['delay'] = self._bot.mspaint_mode['delay']
            self._config.set_tool('MSPaint Mode', tool)

            self._controller._status.set(
                'MSPaint Mode delay updated. This is the wait time between double-clicks on the palette.')

        except ValueError:
            # Invalid input, revert to current bot setting
            self._mspaint_delay_var.set(str(self._bot.mspaint_mode.get('delay', 0.5)))
            self._controller._status.set('Invalid delay value. Please enter a number between 0.01 and 5.0')

    def _on_delay_entry_change(self, event=None):
        """Handle changes to the delay entry field with validation"""
        try:
            val_str = self._delay_var.get().strip()
            if not val_str:
                return  # Empty input, don't update

            val = float(val_str)

            # Validate range: 0.01 to 10.0
            if val < 0.01:
                val = 0.01
                self._delay_var.set(str(val))
            elif val > 10.0:
                val = 10.0
                self._delay_var.set(str(val))

            # Update bot settings
            self._bot.settings[0] = round(val, 3)
            self._optlabl[0]['text'] = f"{self._options[0][0]}: {val:.2f}"

            # Save drawing settings to config
            self.save_drawing_settings()

            self._controller._status.set(self._SLIDER_TOOLTIPS[0])

        except ValueError:
            # Invalid input, revert to current bot setting
            self._delay_var.set(str(self._bot.settings[0]))
            self._controller._status.set('Invalid delay value. Please enter a number between 0.01 and 10.0')

    def _on_slider_move(self, index, val):
        # Skip delay (index 0) since it uses an entry field now
        if index == 0:
            return

        val = float(val)
        if index == 1:  # Pixel Size - force to integer
            val = int(round(val))
            self._bot.settings[index] = val
            self._optlabl[index]['text'] = f"{self._options[index][0]}: {val}"
        else:
            self._bot.settings[index] = round(val, 3)
            self._optlabl[index]['text'] = f"{self._options[index][0]}: {val:.2f}"

        # Save drawing settings to config
        self.save_drawing_settings()

        self._controller._status.set(self._SLIDER_TOOLTIPS[index])

    def save_drawing_settings(self):
        """Persist the four bot settings (delay, pixel size, precision, jump delay)."""
        self._config.set_drawing_setting('delay', self._bot.settings[0])
        self._config.set_drawing_setting('pixel_size', self._bot.settings[1])
        self._config.set_drawing_setting('precision', self._bot.settings[2])
        self._config.set_drawing_setting('jump_delay', self._bot.settings[3])

    def _on_jump_threshold_change(self, event=None):
        """Handle jump threshold change"""
        try:
            val_str = self._jump_threshold_var.get().strip()
            if not val_str:
                return  # Empty input, don't update

            val = int(val_str)

            # Validate range: 1 to 100 pixels
            if val < 1:
                val = 1
                self._jump_threshold_var.set(str(val))
            elif val > 100:
                val = 100
                self._jump_threshold_var.set(str(val))

            # Update bot state
            self._bot.jump_threshold = val

            # Save to config
            self._config.set_drawing_setting('jump_threshold', val)

            self._controller._status.set(
                f'Jump threshold updated to {val} pixels. Cursor jumps larger than this will trigger delay.')

        except ValueError:
            # Invalid input, revert to current bot setting
            self._jump_threshold_var.set(str(self._bot.jump_threshold))
            self._controller._status.set('Invalid jump threshold. Please enter a number between 1 and 100.')

    def _on_calib_step_change(self, event=None):
        """Handle calibration step size change"""
        try:
            val_str = self._calib_step_var.get().strip()
            if not val_str:
                return  # Empty input, don't update

            val = int(val_str)

            # Validate range: 1 to 10
            if val < 1:
                val = 1
                self._calib_step_var.set(str(val))
            elif val > 10:
                val = 10
                self._calib_step_var.set(str(val))

            # Save to config
            self._config.set_calibration_setting('step_size', val)

            self._controller._status.set(
                'Calibration step size updated. Lower values = more accurate but slower.')

        except ValueError:
            # Invalid input, revert to default
            self._calib_step_var.set('2')
            self._controller._status.set('Invalid step size. Please enter a number between 1 and 10.')

    def _on_pause_key_entry_press(self, event):
        # Only allow setting pause key when not drawing
        if not self._controller.busy:
            # When not drawing, allow setting pause key by typing in the entry field
            key_name = event.keysym.lower()
            # Handle special cases
            if key_name.startswith('f') and key_name[1:].isdigit():
                key_name = key_name  # f1, f2, etc.
            elif len(key_name) > 1:
                # For special keys, keep as-is
                pass
            else:
                # For regular keys, use char
                key_name = event.char.lower() if event.char else key_name

            # Update the entry field and bot's pause key
            self._pause_key_entry.delete(0, END)
            self._pause_key_entry.insert(0, key_name)
            self._bot.pause_key = key_name

            # Save pause key to config file
            self._config.set_pause_key(key_name)

            return "break"

        # This should never be reached when not busy, but just in case
        print(f"Unexpected pause key press while busy={self._controller.busy}")
        return "break"

    # ------------------------------------------------------------------
    # Accessors for Window
    # ------------------------------------------------------------------

    @property
    def pause_key(self):
        """Current pause key as shown in the entry field."""
        return self._pause_key_entry.get().strip() or 'p'

    @property
    def calib_step(self):
        """Current calibration step size as entered in the UI."""
        return self._calib_step_var.get()

    def reset_mode_selection(self):
        """Revert the mode dropdown to the current mode (used after errors)."""
        self._tecvar.set(self.mode)

    # ------------------------------------------------------------------
    # Config <-> UI sync
    # ------------------------------------------------------------------

    def load_from_config(self):
        """Restore widget values from config. Call after ConfigManager.load()."""
        config = self._config

        # Pause key
        self._pause_key_entry.delete(0, END)
        self._pause_key_entry.insert(0, config.get_pause_key())

        # Calibration step size
        calib_step = config.get_calibration_settings().get('step_size', 2)
        self._calib_step_var.set(str(calib_step))

        # Jump threshold
        jump_threshold = config.get_drawing_settings().get('jump_threshold', 5)
        self._bot.jump_threshold = jump_threshold
        self._jump_threshold_var.set(str(jump_threshold))

        # Drawing settings
        settings = config.get_drawing_settings()
        if settings:
            self._bot.settings = [
                settings.get('delay', 0.1),
                settings.get('pixel_size', 12),
                settings.get('precision', 0.9),
                settings.get('jump_delay', 0.5)
            ]
            # Update UI - delay uses entry field, others use sliders
            for i, val in enumerate(self._bot.settings):
                if i == 0:  # Delay - use entry field
                    self._delay_var.set(str(val))
                    self._optlabl[0]['text'] = f"{self._options[0][0]}: {val:.2f}"
                elif i == 1:  # Pixel Size - force to integer
                    val = int(val)
                    self._optvars[i].set(val)
                    self._optlabl[i]['text'] = f"{self._options[i][0]}: {val}"
                else:  # Other options - use sliders
                    self._optvars[i].set(val)
                    self._optlabl[i]['text'] = f"{self._options[i][0]}: {val:.2f}"

        # Drawing options checkbuttons
        options = config.get_drawing_options()
        ignore_white = options.get('ignore_white_pixels', True)
        self._checkbutton_vars[0].set(1 if ignore_white else 0)
        if ignore_white:
            self.draw_options |= self._bot.IGNORE_WHITE
        else:
            self.draw_options &= ~self._bot.IGNORE_WHITE

        use_custom = options.get('use_custom_colors', False)
        self._checkbutton_vars[1].set(1 if use_custom else 0)
        if use_custom:
            self.draw_options |= self._bot.USE_CUSTOM_COLORS
        else:
            self.draw_options &= ~self._bot.USE_CUSTOM_COLORS

    def refresh_from_bot(self):
        """Sync feature-toggle checkboxes from bot state (after config apply)."""
        bot = self._bot
        self._newlayer_var.set(1 if bot.new_layer.get('enabled', False) else 0)
        self._colorbutton_var.set(1 if bot.color_button.get('enabled', False) else 0)
        cb_status = self._config.get_tool('Color Button').get('status', False)
        try:
            self._colorbutton_cb.config(state='normal' if cb_status else 'disabled')
        except Exception:
            pass
        self._skip_first_color_var.set(1 if bot.skip_first_color else 0)
        self._path_opt_var.set(1 if bot.path_optimization else 0)
        self._wait_after_draw_var.set(1 if bot.wait_after_draw else 0)
        self._mspaint_mode_var.set(1 if bot.mspaint_mode.get('enabled', False) else 0)
        self._mspaint_delay_var.set(str(bot.mspaint_mode.get('delay', 0.5)))
