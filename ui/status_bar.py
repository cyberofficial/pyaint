"""
StatusBar — single-line status display for the main window.

Replaces the ad-hoc ``tlabel`` label in Window and the ~80 scattered
``self.tlabel['text'] = ...`` assignments with one ``set(msg)`` method.
"""

from tkinter import font
from tkinter.ttk import Frame, Label


class StatusBar(Frame):
    """Single-line status display with word-wrap."""

    def __init__(self, parent):
        super().__init__(parent)
        default_font = font.nametofont('TkDefaultFont').actual()
        self._label = Label(self, text='Hello! Begin by pressing "Setup"',
                            font=(default_font['family'], default_font['size']))
        self._label.bind('<Configure>', lambda e: self._label.config(wraplength=e.width))
        self._label.pack(fill='both', expand=True, padx=5)

    def set(self, text):
        self._label['text'] = text
