"""
ActionPanel — action buttons, redraw region controls, and file management.

Extracted from Window._init_cpanel (the button section). Commands are wired
to controller (Window) methods; the redraw region status label is exposed
as ``region_label`` so Window can update it after region selection.
"""

from tkinter import font
from tkinter.ttk import Button, Frame, Label


class ActionPanel(Frame):
    """Action buttons that trigger drawing/calibration/setup operations."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self._controller = controller  # duck-typed Window
        self.region_label = None
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        default_font = font.nametofont('TkDefaultFont').actual()
        title_font = (default_font['family'], default_font['size'], 'bold')

        actions = [
            ('Setup', self._controller.setup),
            ('Pre-compute', self._controller.start_precompute_thread),
            ('Test Draw', self._controller.start_test_draw_thread),
            ('Simple Test Draw', self._controller.start_simple_test_draw_thread),
            ('Run Calibration', self._controller.start_calibration_thread),
            ('Generate Palette', self._controller.start_palette_window),
            ('Interactive Mode', self._controller.start_interactive_mode),
            ('Start', self._controller.start_draw_thread),
        ]
        for i, (label, command) in enumerate(actions):
            btn = Button(self, text=label, command=command)
            btn.grid(column=0, row=i, columnspan=2, padx=5, pady=5, sticky='ew')

        curr_row = len(actions)

        # Redraw Region section
        Label(self, text='Redraw Region', font=title_font).grid(
            column=0, row=curr_row, columnspan=2, padx=5, pady=5, sticky='w')
        curr_row += 1

        Button(self, text='Pick Region', command=self._controller._on_redraw_pick).grid(
            column=0, row=curr_row, padx=5, pady=5, sticky='ew')
        Button(self, text='Draw Region', command=self._controller._redraw_draw_thread).grid(
            column=1, row=curr_row, padx=5, pady=5, sticky='ew')
        curr_row += 1

        self.region_label = Label(self, text='No region selected', font=('TkDefaultFont', 8))
        self.region_label.grid(column=0, row=curr_row, columnspan=2, padx=5, pady=5, sticky='w')
        curr_row += 1

        # File Management section
        Label(self, text='File Management', font=title_font).grid(
            column=0, row=curr_row, columnspan=2, padx=5, pady=5, sticky='w')
        curr_row += 1

        Button(self, text='Remove Calibration', command=self._controller._on_delete_calibration).grid(
            column=0, row=curr_row, padx=5, pady=5, sticky='ew')
        Button(self, text='Reset Config', command=self._controller._on_reset_config).grid(
            column=1, row=curr_row, padx=5, pady=5, sticky='ew')
