import os
import time
import tkinter
import traceback
from tkinter import Tk, filedialog, messagebox
from tkinter import ttk

from PIL import Image

from bot import Bot
from utils import resource_path
from ui.action_panel import ActionPanel
from ui.config_manager import ConfigManager
from ui.image_panel import ImagePanel
from ui.palette_window import PaletteWindow
from ui.settings_panel import SettingsPanel
from ui.setup import SetupWindow
from ui.single_color_window import SingleColorWindow
from ui.status_bar import StatusBar
from ui.thread_manager import ThreadJob, ThreadManager



def is_free(func):
    """
    Decorator that only executes a function when the bot is not busy by checking that
    `self.busy` flag. Keeps decorator at module scope to avoid descriptor/type issues.
    """

    def decorator(self):
        if self.busy:
            self._status.set("Cannot perform action. Currently busy...")
        else:
            self.busy = True
            try:
                func(self)
            except Exception:
                # Never leave the UI wedged on a failed action.
                traceback.print_exc()
                self.busy = False
                raise

    return decorator

class Window:

    def __init__(self, title, bot, w, h, x, y):
        self._root = Tk()
        self._config = ConfigManager(resource_path('config.json'))
        # Prevent saving during initial UI setup (slider.set etc. trigger callbacks)
        self._config.begin_batch()

        self._root.title(title)
        # Center the window on screen
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)

        self.bot = bot
        self.title = title
        self.busy = False

        # tools dict is the ConfigManager's live data (compat alias)
        self.tools = self._config.data

        # Status bar at the bottom
        self._status = StatusBar(self._root)
        self._status.grid(row=1, column=0, sticky='ew', padx=5, pady=5)

        # Main notebook: Settings / Preview / Actions
        self._notebook = ttk.Notebook(self._root)
        self._notebook.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self._settings = SettingsPanel(self._notebook, controller=self, config=self._config)
        self._notebook.add(self._settings, text='Settings')

        self._image_panel = ImagePanel(self._notebook, controller=self, config=self._config)
        self._notebook.add(self._image_panel, text='Preview')

        self._actions = ActionPanel(self._notebook, controller=self)
        self._notebook.add(self._actions, text='Actions')

        # Background task lifecycle
        self._threads = ThreadManager(self._root, on_status=lambda msg: self._status.set(msg))

        # State previously initialized inside panel builders
        self._redraw_region = None  # Will store (x1, y1, x2, y2) canvas coordinates
        self._sc_window = None  # Single Color config window reference

        try:
            self._image_panel.load_image(path=resource_path('assets/sample.png'))
        except FileNotFoundError:
            self._status.set('Sample image not found. Load an image via the Preview tab.')
        try:
            self.load_config()  # Load saved config
        finally:
            # UI initialization finished - allow saving (safe even if load_config raised)
            self._config.end_batch()

        self._root.mainloop()

    def __del__(self):
        """Clean up cache directory on application exit"""
        try:
            import shutil
            cache_dir = 'cache'
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                print(f"Cleaned up cache directory: {cache_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up cache directory: {e}")
        

    def _open_single_color_window(self):
        if hasattr(self, '_sc_window') and self._sc_window is not None and self._sc_window.window.winfo_exists():
            self._sc_window.window.lift()
            return
        if not hasattr(self, '_imname') or not os.path.isfile(self._imname):
            messagebox.showerror(self.title, "Please load an image first.")
            self._settings.reset_mode_selection()
            return
        self._sc_window = SingleColorWindow(self._root, self.bot, self._imname)
        # Clean up reference when window closes
        self._sc_window.window.protocol('WM_DELETE_WINDOW', lambda: self._on_sc_window_close())

    def _on_sc_window_close(self):
        if hasattr(self, '_sc_window') and self._sc_window is not None:
            self._sc_window.window.destroy()
            self._sc_window = None


    def load_config(self):
        self._config.load()
        self._settings.load_from_config()
        self._image_panel.load_from_config()

        # Apply saved tool configs to bot state
        for tool_name in ('Palette', 'Canvas', 'Custom Colors', 'New Layer',
                          'Color Button', 'Color Button Okay', 'Color Picker', 'MSPaint Mode'):
            self.bot.apply_tool_config(tool_name, self.tools.get(tool_name, {}))

        self._settings.refresh_from_bot()

        if self._config.data:
            self._status.set('Successfully loaded setup from config file.')
        else:
            self._status.set('Config file missing or invalid. Using default settings.')

    def _set_busy(self, val):
        self.busy = val

    @is_free
    def setup(self):
        self.load_config()
        # Ensure setup tools exist with default structure if missing
        default_tools = {
            'Palette': {
                'status': False,
                'box': None,
                'rows': 6,
                'cols': 8,
                'color_coords': None,
                'preview': None,
            },
            'Canvas': {
                'status': False,
                'box': None,
                'preview': None,
            },
            'Custom Colors': {
                'status': False,
                'box': None,
                'preview': None,
            },
            'Color Picker': {
                'name': 'Color Picker',
                'status': False,
                'coords': None,
                'enabled': False,
            },
            'New Layer': {
                'status': False,
                'coords': None,
                'enabled': False,
                'modifiers': {
                    'ctrl': False,
                    'alt': False,
                    'shift': False
                }
            },
            'Color Button': {
                'status': False,
                'coords': None,
                'enabled': False,
                'delay': 0.1,
                'modifiers': {
                    'ctrl': False,
                    'alt': False,
                    'shift': False
                }
            },
            'Color Button Okay': {
                'status': False,
                'coords': None,
                'enabled': False,
                'modifiers': {
                    'ctrl': False,
                    'alt': False,
                    'shift': False
                }
            },
            'color_preview_spot': {
                'name': 'Color Preview Spot',
                'button': None,
                'enabled': False,
                'coords': None,
                'data': None,
                'modifiers': {
                    'ctrl': False,
                    'alt': False,
                    'shift': False
                },
                'status': False
            }
        }

        # Build a dedicated setup_tools mapping (only tools) so that
        # SetupWindow doesn't iterate non-tool keys (like drawing_settings).
        setup_tools = {}
        for tool_name in ['Palette', 'Canvas', 'Custom Colors', 'Color Picker', 'New Layer', 'Color Button', 'Color Button Okay', 'color_preview_spot']:
            existing = self.tools.get(tool_name, {})
            merged = default_tools[tool_name].copy()
            merged.update(existing if isinstance(existing, dict) else {})
            setup_tools[tool_name] = merged

        # Keep a reference so we can merge results back into self.tools
        self._setup_tools = setup_tools
        self._iwindow = SetupWindow(parent=self._root, bot=self.bot, tools=self._setup_tools, on_complete=self._on_complete_setup, title='Setup')

    def _on_complete_setup(self):
        # If SetupWindow returned modified setup data, merge it back into self.tools
        if hasattr(self, '_setup_tools'):
            for k, v in self._setup_tools.items():
                self.tools[k] = v

        # Apply tool configs to bot state
        for tool_name in ('Palette', 'Canvas', 'Custom Colors', 'New Layer',
                          'Color Button', 'Color Button Okay', 'Color Picker', 'MSPaint Mode'):
            self.bot.apply_tool_config(tool_name, self.tools.get(tool_name, {}))

        # Sync feature-toggle checkboxes with the new bot state
        self._settings.refresh_from_bot()

        self.tools['pause_key'] = self._settings.pause_key or 'p'
        self.bot.pause_key = self.tools['pause_key']

        # Convert tuples to lists for JSON serialization
        for tool_name in ['Canvas', 'Custom Colors']:
            if tool_name in self.tools and 'box' in self.tools[tool_name]:
                box = self.tools[tool_name]['box']
                if isinstance(box, tuple):
                    self.tools[tool_name]['box'] = list(box)

        # Save current drawing settings and options
        self._settings.save_drawing_settings()
        self._config.set_drawing_option('ignore_white_pixels', bool(self.draw_options & Bot.IGNORE_WHITE))
        self._config.set_drawing_option('use_custom_colors', bool(self.draw_options & Bot.USE_CUSTOM_COLORS))

        # Save current URL if any
        if self._image_panel.last_url:
            self._config.set('last_image_url', self._image_panel.last_url)

        self._config.save()
        self._status.set('Setup saved.')
        self._set_busy(False)

    @is_free
    def start_precompute_thread(self):
        self._threads.start(ThreadJob(
            name='precompute',
            target=self.precompute,
            progress_getter=lambda: self.bot.progress,
            progress_msg=lambda p: f"Pre-computing: {p:.2f}%",
        ))

    def precompute(self):
        try:
            cache_file = self.bot.precompute(self._imname, flags=self.draw_options, mode=self._mode)

            # Load cached data to estimate drawing time
            cache_data = self.bot.load_cached(cache_file)
            if cache_data:
                drawing_eta = self.bot.estimate_drawing_time(cache_data['cmap'])
                self._status.set(f'Pre-compute completed! Estimated drawing time: {drawing_eta}')
            else:
                self._status.set(f'Pre-compute completed! Cache saved.')

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(self.title, f'Pre-compute failed: {str(e)}')
        finally:
            self._set_busy(False)

    @is_free
    def start_test_draw_thread(self):
        # Color Picker Mode requires the dropper button to be configured
        if (self.draw_options & Bot.USE_COLOR_PICKER
                and not self.bot.color_picker.get('coords')):
            messagebox.showerror(self.title, "Color Picker tool not configured. Please run Setup first.")
            self._set_busy(False)
            return
        self._threads.start(ThreadJob(
            name='test_draw',
            target=self.test_draw,
            progress_getter=lambda: self.bot.progress,
            progress_msg=lambda p: f"Test drawing: {p:.2f}%",
        ))

    @is_free
    def start_simple_test_draw_thread(self):
        """Start simple test draw in a separate thread"""
        if not hasattr(self.bot, '_canvas') or self.bot._canvas is None:
            messagebox.showerror(self.title, "Canvas not configured. Please run Setup first.")
            self._set_busy(False)
            return

        self._threads.start(ThreadJob(
            name='simple_test_draw',
            target=self.simple_test_draw,
            running_msg='Simple test drawing in progress...',
        ))

    @is_free
    def start_calibration_thread(self):
        """Start color calibration process in a separate thread"""
        # Check if required tools are configured
        custom_colors_data = self.tools.get('Custom Colors', {}).get('box')
        if not custom_colors_data or (isinstance(custom_colors_data, list) and len(custom_colors_data) == 0):
            messagebox.showerror(self.title, "Custom Colors tool not configured. Please run Setup first.")
            self._set_busy(False)
            return
        
        preview_spot_coords = self.tools.get('color_preview_spot', {}).get('coords')
        if not preview_spot_coords:
            messagebox.showerror(self.title, "Color Preview Spot tool not configured. Please run Setup first.")
            self._set_busy(False)
            return
        
        # Get step size from entry field
        try:
            step = int(self._settings.calib_step)
        except ValueError:
            step = 2  # Default to 2 if invalid
        
        # Store step size in tools config
        self._config.set_calibration_setting('step_size', step)
        
        # Create calibration progress overlay window
        self._create_calibration_overlay()
        
        # Minimize window then start calibration
        messagebox.showinfo(self.title, f'Press ESC to stop calibration.')
        self._root.iconify()
        time.sleep(1)  # Small delay before starting to allow window to minimize
        
        # Track calibration start time for ETA calculation
        self._calibration_start_time = time.time()
        self._calibration_cancel_latched = False
        
        # Create and start calibration thread
        self._threads.start(ThreadJob(
            name='calibration',
            target=self._calibration_thread,
            poll_fn=self._calibration_poll,
        ))

    def _create_calibration_overlay(self):
        """
        Create and show an always-on-top progress overlay window for color calibration.
        The window displays current calibration progress and appears above the custom color box location.
        """
        try:
            # Get custom color box location for positioning
            custom_colors_box = self.tools.get('Custom Colors', {}).get('box')
            if not custom_colors_box:
                # Fallback to top center of screen if box location not available
                screen_width = self._root.winfo_screenwidth()
                x_position = (screen_width - 240) // 2
                y_position = 10
            else:
                # Position above the custom color box
                if isinstance(custom_colors_box, list):
                    box_x = custom_colors_box[0]
                    box_y = custom_colors_box[1]
                else:
                    box_x = custom_colors_box.get('x', 0)
                    box_y = custom_colors_box.get('y', 0)
                
            # Position overlay above the box (with some offset)
            window_width = 400
            window_height = 20
            # Align right edge of overlay with right edge of custom colors box
            box_right = custom_colors_box[2] if isinstance(custom_colors_box, list) else box_x + (custom_colors_box.get('width', 0) if isinstance(custom_colors_box, dict) else 0)
            x_position = box_right - window_width
            y_position = box_y - 30  # 30 pixels above the box
            
            # Create the overlay window
            self._calib_overlay_window = tkinter.Toplevel(self._root)
            self._calib_overlay_window.title("Calibration Progress")

            # Set window to always on top and remove decorations
            self._calib_overlay_window.attributes("-topmost", True)
            self._calib_overlay_window.overrideredirect(True)

            # Set window size and position
            window_width = 400
            window_height = 20
            self._calib_overlay_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

            # Create a dark background frame with border
            border_frame = tkinter.Frame(
                self._calib_overlay_window,
                bg="#4a4a4a",
                width=window_width,
                height=window_height
            )
            border_frame.pack(fill=tkinter.BOTH, expand=True)

            # Inner frame for content
            overlay_frame = tkinter.Frame(
                border_frame,
                bg="#2c2c2c",
                width=window_width - 2,
                height=window_height - 2
            )
            overlay_frame.place(x=1, y=1, width=window_width - 2, height=window_height - 2)

            # Create centered label for progress text
            self._calib_overlay_label = tkinter.Label(
                overlay_frame,
                text="Initializing...",
                bg="#2c2c2c",
                fg="#00ff00",  # Green text for progress
                font=("Arial", 9, "bold"),
                relief=tkinter.FLAT
            )
            self._calib_overlay_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

            # Keep window responsive
            self._calib_overlay_window.update()

            print("[CalibrationOverlay] Overlay window created")
            return self._calib_overlay_window

        except Exception as e:
            print(f"[CalibrationOverlay] Error creating overlay: {e}")
            return None

    def _close_calibration_overlay(self):
        """Close the calibration progress overlay window"""
        try:
            if hasattr(self, '_calib_overlay_window') and self._calib_overlay_window is not None:
                self._calib_overlay_window.destroy()
                self._calib_overlay_window = None
                self._calib_overlay_label = None
                print("[CalibrationOverlay] Overlay window closed")
        except Exception as e:
            print(f"[CalibrationOverlay] Error closing overlay: {e}")

    def _calibration_poll(self, job):
        """Custom poll body for the calibration thread: overlay + ETA updates.

        Returns False when the job should stop polling; the calibration
        thread's finally block handles final cleanup (overlay close, window
        restore, busy flag).
        """
        if job.thread.is_alive():
            # Check if calibration was cancelled. Latch the message and keep
            # polling until the thread exits; never reset `terminate` here or
            # the thread may miss the flag and keep driving the mouse.
            if self.bot.terminate:
                if not self._calibration_cancel_latched:
                    self._calibration_cancel_latched = True
                    self._status.set('Calibration cancelled by user (ESC pressed)')
                    self._close_calibration_overlay()
                return True

            # Update progress based on calibration state
            if hasattr(self.bot, '_calibration_progress'):
                total = self.bot._calibration_progress.get('total', 0)
                current = self.bot._calibration_progress.get('current', 0)
                if total > 0:
                    percent = (current / total) * 100
                    # Calculate ETA based on elapsed time
                    elapsed_time = time.time() - self._calibration_start_time
                    if current > 0 and percent < 100:
                        avg_time_per_color = elapsed_time / current
                        colors_remaining = total - current
                        eta_seconds = colors_remaining * avg_time_per_color
                        eta_str = self.bot._format_time(eta_seconds)
                    else:
                        eta_str = "calculating..."
                    # Update overlay label
                    if hasattr(self, '_calib_overlay_label') and self._calib_overlay_label is not None:
                        self._calib_overlay_label['text'] = f"Calibrating: {current}/{total} ({percent:.1f}%) - ETA: {eta_str}"
                        if hasattr(self, '_calib_overlay_window') and self._calib_overlay_window is not None:
                            try:
                                self._calib_overlay_window.update()  # Force UI update
                            except Exception as e:
                                print(f"[CalibrationOverlay] Error updating window: {e}")
                    self._status.set(f"Calibrating: {current}/{total} colors ({percent:.1f}%) - ETA: {eta_str}")
                else:
                    elapsed_time = time.time() - self._calibration_start_time
                    if hasattr(self, '_calib_overlay_label') and self._calib_overlay_label is not None:
                        self._calib_overlay_label['text'] = f"Calibrating: {current} colors... ({elapsed_time:.0f}s)"
                        if hasattr(self, '_calib_overlay_window') and self._calib_overlay_window is not None:
                            try:
                                self._calib_overlay_window.update()  # Force UI update
                            except Exception as e:
                                print(f"[CalibrationOverlay] Error updating window: {e}")
                    self._status.set(f"Calibrating: {current} colors... (Time: {elapsed_time:.0f}s)")
            return True
        # Thread finished; its finally block closed the overlay and restored the window.
        # Reset terminate (no-op on normal completion; clears ESC on cancel).
        self.bot.terminate = False
        return False

    def _calibration_thread(self):
        """Execute color calibration process"""
        try:
            # Get grid_box and preview_point from tools
            grid_box = self.tools.get('Custom Colors', {}).get('box')
            preview_point = self.tools.get('color_preview_spot', {}).get('coords')
            
            if not grid_box or not preview_point:
                self._status.set('Error: Missing calibration configuration data')
                self._set_busy(False)
                return
            
            # Get step size
            step = self.tools.get('calibration_settings', {}).get('step_size', 2)
            
            # Initialize progress tracking
            self.bot._calibration_progress = {'total': 0, 'current': 0}
            
            # Calculate total positions to calibrate
            if isinstance(grid_box, (list, tuple)):
                grid_width = grid_box[2] - grid_box[0]
                grid_height = grid_box[3] - grid_box[1]
            else:
                grid_width = grid_box.get('width', 0)
                grid_height = grid_box.get('height', 0)
            total_positions = ((grid_width // step) + 1) * ((grid_height // step) + 1)
            self.bot._calibration_progress['total'] = total_positions
            
            # Run calibration
            self.bot.calibrate_custom_colors(grid_box, preview_point, step=step)

            # Save calibration data to file (skip if ESC-cancelled so a
            # previously good color_calibration.json is not overwritten)
            if not self.bot.terminate:
                calib_file = 'color_calibration.json'
                if self.bot.save_color_calibration(calib_file):
                    self._status.set(f'Calibration saved to {calib_file} with {len(self.bot.color_calibration_map)} colors')
                else:
                    self._status.set('Failed to save calibration data')
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(self.title, f'Calibration failed: {str(e)}')
        finally:
            # Close calibration overlay window
            self._close_calibration_overlay()
            # Restore window after calibration completes (even if cancelled or failed)
            self._root.deiconify()
            self._root.wm_state('normal')
            self._set_busy(False)

    def simple_test_draw(self):
        """Execute simple test draw"""
        try:
            t = time.time()

            messagebox.showinfo(self.title, 'Simple test draw: Will draw 5 lines (1/4 canvas width each) starting from upper-left corner.\n\nPlease select your desired color in painting app first. No color picking will occur.')
            self._root.iconify()

            # Clear any previous termination/paused state
            self.bot.terminate = False
            self.bot.paused = False
            self.bot.drawing = False

            result = self.bot.simple_test_draw()
            self._root.deiconify()
            self._root.wm_state('normal')

            if result == 'success':
                actual_time = time.time() - t
                self._status.set(f"Simple test draw completed. Time elapsed: {actual_time:.2f}s")
            elif result == 'terminated':
                actual_time = time.time() - t
                self._status.set(f"Simple test draw terminated. Time elapsed: {actual_time:.2f}s")
                self.bot.terminate = False
            else:
                self._status.set(f"Simple test draw result: {result}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(self.title, f'Simple test draw failed: {str(e)}')
        finally:
            self._set_busy(False)

    @is_free
    def start_draw_thread(self):
        # Color Picker Mode requires the dropper button to be configured
        if (self.draw_options & Bot.USE_COLOR_PICKER
                and not self.bot.color_picker.get('coords')):
            messagebox.showerror(self.title, "Color Picker tool not configured. Please run Setup first.")
            self._set_busy(False)
            return

        # Color Picker Mode: offer loading a palette file before the main draw.
        # (Main draw only — Test Draw / Simple Test Draw never prompt.)
        if self.draw_options & Bot.USE_COLOR_PICKER:
            choice = messagebox.askyesnocancel(
                self.title,
                'Color Picker Mode\n\n'
                'Use the eye dropper with EXACT image colors\n'
                '(one dropper cycle per color)?\n\n'
                '  Yes   = eye dropper only\n'
                '  No    = load a palette file and map image colors to it first\n'
                '  Cancel = abort this draw')
            if choice is None:
                self._set_busy(False)
                return
            if not choice:
                path = filedialog.askopenfilename(
                    parent=self._root,
                    title='Load Color Palette',
                    filetypes=[('Palette files', '*.gpl *.css *.txt *.hex'), ('All Files', '*.*')])
                if not path:
                    self._set_busy(False)
                    return
                try:
                    self.bot.set_loaded_palette(path)
                except Exception as e:
                    messagebox.showerror(self.title, f'Failed to load palette: {e}')
                    self._set_busy(False)
                    return

        self._threads.start(ThreadJob(
            name='draw',
            target=self.start,
            progress_getter=lambda: self.bot.progress,
            progress_msg=lambda p: f"Processing image: {p:.2f}%",
        ))
    def _process_image(self):
        """Process the loaded image according to the current draw mode."""
        self.bot._cached_path_optimization = False  # Reset; live processing re-optimizes
        if self._mode == Bot.SINGLE_COLOR:
            if not self.bot.single_color_configured:
                raise ValueError("Single Color mode not configured. Please configure it first.")
            return self.bot.process_single_color(
                self._imname,
                self.bot.single_color_ignore,
                self.bot.single_color_tolerance,
                self.draw_options
            )
        return self.bot.process(self._imname, flags=self.draw_options, mode=self._mode)

    def test_draw(self):
        try:
            t = time.time()

            # Check for cached computation first
            has_cache, cache_file = self.bot.get_cached_status(self._imname, flags=self.draw_options, mode=self._mode)
            if has_cache:
                # Load from cache
                print(f"Loading from cache: {cache_file}")
                cache_data = self.bot.load_cached(cache_file)
                if cache_data:
                    cmap = cache_data['cmap']
                    self.bot._cached_path_optimization = cache_data.get('path_optimization', False)
                    # Log cache details
                    num_colors = len(cmap)
                    total_points = sum(len(lines) for lines in cmap.values())
                    cache_time = time.ctime(cache_data['timestamp'])
                    print(f"Cache loaded - {num_colors} colors, {total_points} coordinate points")
                    print(f"Cached on: {cache_time}")
                    print(f"Settings: Delay={cache_data['settings'][0]}, PixelSize={cache_data['settings'][1]}")
                    self._status.set(f"Using cached computation for test draw")
                else:
                    # Cache invalid, fall back to processing
                    print("Cache file invalid, processing live...")
                    cmap = self._process_image()
            else:
                # No cache, process normally
                print("No cache available, processing live...")
                cmap = self._process_image()

            # Count total lines and limit to first 20 (or fewer if less available)
            total_lines = sum(len(lines) for lines in cmap.values())
            test_lines = min(20, total_lines)
            print(f"Test drawing first {test_lines} lines out of {total_lines} total")

            messagebox.showinfo(self.title, f'Test drawing first {test_lines} lines. Adjust your brush size in the painting app, then use the full "Start" button.')
            self._root.iconify()
            # Clear any previous termination/paused state so test can be retried
            self.bot.terminate = False
            self.bot.paused = False
            self.bot.drawing = False
            self.bot.draw_state = {
                'color_idx': 0,
                'line_idx': 0,
                'segment_idx': 0,
                'current_color': None,
                'was_paused': False
            }

            self.bot.single_color_mode_active = (self._mode == Bot.SINGLE_COLOR)
            result = self.bot.test_draw(cmap, max_lines=test_lines)
            self._root.deiconify()  # type: ignore
            self._root.wm_state('normal')  # type: ignore
            if result == 'success':
                actual_time = time.time() - t
                # Show time comparison if available
                if hasattr(self.bot, 'estimated_time_seconds'):
                    estimated_str = self.bot._format_time(self.bot.estimated_time_seconds)
                    actual_str = self.bot._format_time(actual_time)
                    diff_seconds = self.bot.estimated_time_seconds - actual_time
                    if diff_seconds >= 0:
                        diff_str = f"Saved: {self.bot._format_time(diff_seconds)}"
                    else:
                        diff_str = f"Extra: {self.bot._format_time(abs(diff_seconds))}"
                    self._status.set(f"Test draw completed! Est: {estimated_str}, Act: {actual_str}, {diff_str}")
                else:
                    self._status.set(f"Test draw completed. Time elapsed: {actual_time:.2f}s")
            elif result == 'terminated':
                actual_time = time.time() - t
                if hasattr(self.bot, 'estimated_time_seconds'):
                    estimated_str = self.bot._format_time(self.bot.estimated_time_seconds)
                    actual_str = self.bot._format_time(actual_time)
                    self._status.set(f"Test draw terminated. Est: {estimated_str}, Act: {actual_str}")
                else:
                    self._status.set(f"Test draw terminated by user. Time elapsed: {actual_time:.2f}s")
                # Clear termination so future tests can run
                self.bot.terminate = False
            else:
                self._status.set(f"Test draw result: {result}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(self.title, str(e))

        # Let the thread manager know that the task has ended
        self._set_busy(False)

    def _on_redraw_pick(self):
        """Start region selection mode for redraw functionality (like canvas setup)"""
        if not hasattr(self.bot, '_canvas') or self.bot._canvas is None:
            messagebox.showerror(self.title, "Canvas not configured. Please run Setup first.")
            return

        self._coords = []
        self._clicks = 0
        self._required_clicks = 2

        # Prompt user like the setup process
        if messagebox.askokcancel(self.title, "Click on the UPPER LEFT and LOWER RIGHT corners of the region you want to redraw.") == True:
            from pynput.mouse import Listener
            self._listener = Listener(on_click=self._on_redraw_click)
            self._listener.start()
            self._root.iconify()

    def _on_redraw_click(self, x, y, button, pressed):
        """Handle mouse clicks for redraw region selection (like setup canvas selection)"""
        if pressed:
            self._root.bell()
            print(x, y)
            self._clicks += 1
            self._coords += x, y

            if self._clicks == self._required_clicks:
                # Determining corner coordinates based on the received input. ImageGrab.grab() always expects
                # the first pair of coordinates to be above and on the left of the second pair
                top_left = min(self._coords[0], self._coords[2]), min(self._coords[1], self._coords[3])
                bot_right = max(self._coords[0], self._coords[2]), max(self._coords[1], self._coords[3])
                box = top_left + bot_right
                print(f'Capturing box: {box}')

                # Store selected region coordinates
                self._redraw_region = box
                self._actions.region_label['text'] = f"Region: ({box[0]}, {box[1]}) to ({box[2]}, {box[3]})"
                self._status.set("Redraw region selected. Click 'Draw Region' to start drawing.")

                self._listener.stop()
                self._root.deiconify()

                messagebox.showinfo(self.title, f"Region selected!\n\nTop-left: ({box[0]}, {box[1]})\nBottom-right: ({box[2]}, {box[3]})\n\nYou can now click 'Draw Region' to redraw this area.")

    def _on_delete_calibration(self):
        """Remove the color calibration file"""
        from tkinter import messagebox
        if messagebox.askyesno(self.title, "Are you sure you want to remove the color calibration file?\n\nThis will delete: color_calibration.json"):
            try:
                import os
                calib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'color_calibration.json')
                if os.path.exists(calib_path):
                    os.remove(calib_path)
                    self._status.set("Color calibration file removed successfully.")
                    # Clear calibration data from bot
                    self.bot.color_calibration_map = None
                    print(f"[File Management] Removed calibration file: {calib_path}")
                else:
                    self._status.set("No calibration file found to remove.")
            except Exception as e:
                self._status.set(f"Error removing calibration file: {str(e)}")
                print(f"[File Management] Error: {e}")

    def _on_reset_config(self):
        """Delete config.json file to reset to defaults"""
        from tkinter import messagebox
        if messagebox.askyesno(self.title, "Are you sure you want to reset to default settings?\n\nThis will delete: config.json\n\nAll your tool positions, settings, and preferences will be lost."):
            try:
                import os
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
                if os.path.exists(config_path):
                    os.remove(config_path)
                    self._status.set("Config file removed successfully. Please restart the application to use defaults.")
                    print(f"[File Management] Removed config file: {config_path}")
                else:
                    self._status.set("No config file found to remove.")
            except Exception as e:
                self._status.set(f"Error removing config file: {str(e)}")
                print(f"[File Management] Error: {e}")

    @is_free
    def _redraw_draw_thread(self):
        """Start the redraw region drawing process"""
        if self._redraw_region is None:
            messagebox.showerror(self.title, "No redraw region selected. Please click 'Pick Region' first.")
            self._set_busy(False)
            return

        if not hasattr(self.bot, '_canvas') or self.bot._canvas is None:
            messagebox.showerror(self.title, "Canvas not configured. Please run Setup first.")
            self._set_busy(False)
            return

        self._threads.start(ThreadJob(
            name='redraw',
            target=self.redraw_region,
            progress_getter=lambda: self.bot.progress,
            progress_msg=lambda p: f"Processing redraw region: {p:.2f}%",
        ))

    def redraw_region(self):
        """Process and draw only the selected region"""
        try:
            t = time.time()

            # Convert canvas region to reference image region
            canvas_region = self._redraw_region  # (x1, y1, x2, y2) in canvas coordinates
            image_region = self._canvas_to_image_region(canvas_region)

            print(f"Canvas region: {canvas_region}")
            print(f"Image region: {image_region}")

            # Process only the selected region of the image and draw it at the selected canvas location
            canvas_target = (canvas_region[0], canvas_region[1], canvas_region[2] - canvas_region[0], canvas_region[3] - canvas_region[1])
            cmap = self.bot.process_region(self._imname, image_region, flags=self.draw_options, mode=self._mode, canvas_target=canvas_target)

            if not cmap or len(cmap) == 0:
                self._status.set("No drawable content found in the selected region.")
                return

            # Show drawing time estimate
            drawing_eta = self.bot.estimate_drawing_time(cmap)
            print(f"Estimated redraw time: {drawing_eta}")
            self._status.set(f"Starting redraw - ETA: {drawing_eta}")

            messagebox.showwarning(self.title, f'Redrawing the selected region.\nPress ESC to stop the bot. Press {self.bot.pause_key} to pause/resume.')
            self._root.iconify()

            # Clear any previous termination/paused state
            self.bot.terminate = False
            self.bot.paused = False
            self.bot.drawing = False
            self.bot.draw_state = {
                'color_idx': 0,
                'line_idx': 0,
                'segment_idx': 0,
                'current_color': None,
                'was_paused': False
            }

            self.bot.single_color_mode_active = (self._mode == Bot.SINGLE_COLOR)
            result = self.bot.draw(cmap)
            self._root.deiconify()
            self._root.wm_state('normal')

            if result == 'success':
                actual_time = time.time() - t
                # Show time comparison if available
                if hasattr(self.bot, 'estimated_time_seconds'):
                    estimated_str = self.bot._format_time(self.bot.estimated_time_seconds)
                    actual_str = self.bot._format_time(actual_time)
                    diff_seconds = self.bot.estimated_time_seconds - actual_time
                    if diff_seconds >= 0:
                        diff_str = f"Saved: {self.bot._format_time(diff_seconds)}"
                    else:
                        diff_str = f"Extra: {self.bot._format_time(abs(diff_seconds))}"
                    self._status.set(f"Redraw completed! Est: {estimated_str}, Act: {actual_str}, {diff_str}")
                else:
                    self._status.set(f"Redraw completed. Time elapsed: {actual_time:.2f}s")
            elif result == 'terminated':
                actual_time = time.time() - t
                if hasattr(self.bot, 'estimated_time_seconds'):
                    estimated_str = self.bot._format_time(self.bot.estimated_time_seconds)
                    actual_str = self.bot._format_time(actual_time)
                    self._status.set(f"Redraw terminated. Est: {estimated_str}, Act: {actual_str}")
                else:
                    self._status.set(f"Redraw terminated by user. Time elapsed: {actual_time:.2f}s")
                self.bot.terminate = False
            elif result == 'paused':
                self._status.set(f"Redraw paused. Press {self.bot.pause_key} again to resume.")
            else:
                self._status.set(f"Unknown redraw result: {result}")

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(self.title, f'Redraw failed: {str(e)}')
        finally:
            self._set_busy(False)

    def _canvas_to_image_region(self, canvas_region):
        """Convert canvas coordinates to reference image coordinates"""
        x1, y1, x2, y2 = canvas_region

        # Get canvas dimensions
        canvas_x, canvas_y, canvas_w, canvas_h = self.bot._canvas

        # Load the reference image to get its dimensions
        img = Image.open(self._imname)
        img_w, img_h = img.size

        # Calculate scaling factors
        scale_x = img_w / canvas_w
        scale_y = img_h / canvas_h

        # Convert canvas coordinates to image coordinates
        img_x1 = int((x1 - canvas_x) * scale_x)
        img_y1 = int((y1 - canvas_y) * scale_y)
        img_x2 = int((x2 - canvas_x) * scale_x)
        img_y2 = int((y2 - canvas_y) * scale_y)

        # Ensure coordinates are within image bounds
        img_x1 = max(0, min(img_x1, img_w))
        img_y1 = max(0, min(img_y1, img_h))
        img_x2 = max(0, min(img_x2, img_w))
        img_y2 = max(0, min(img_y2, img_h))

        return (img_x1, img_y1, img_x2, img_y2)

    def start(self):
        try:
            t = time.time()

            # Check for cached computation first
            has_cache, cache_file = self.bot.get_cached_status(self._imname, flags=self.draw_options, mode=self._mode)
            if has_cache:
                # Load from cache
                print(f"Loading from cache: {cache_file}")
                cache_data = self.bot.load_cached(cache_file)
                if cache_data:
                    cmap = cache_data['cmap']
                    self.bot._cached_path_optimization = cache_data.get('path_optimization', False)
                    # Log cache details
                    num_colors = len(cmap)
                    total_points = sum(len(lines) for lines in cmap.values())
                    cache_time = time.ctime(cache_data['timestamp'])
                    print(f"Cache loaded - {num_colors} colors, {total_points} coordinate points")
                    print(f"Cached on: {cache_time}")
                    print(f"Settings: Delay={cache_data['settings'][0]}, PixelSize={cache_data['settings'][1]}")
                    self._status.set(f"Using cached computation")
                else:
                    # Cache invalid, fall back to processing
                    print("Cache file invalid, processing live...")
                    cmap = self._process_image()
            else:
                # No cache, process normally
                print("No cache available, processing live...")
                cmap = self._process_image()

            # Show drawing time estimate
            drawing_eta = self.bot.estimate_drawing_time(cmap)
            print(f"Estimated drawing time: {drawing_eta}")
            self._status.set(f"Starting draw - ETA: {drawing_eta}")

            messagebox.showwarning(self.title, f'Press ESC to stop the bot. Press {self.bot.pause_key} to pause/resume.')
            self._root.iconify()
            # Allow time for user to click inside the app to draw in
            time.sleep(5)
            # Clear any previous termination/paused state before starting
            self.bot.terminate = False
            self.bot.paused = False
            self.bot.drawing = False
            self.bot.draw_state = {
                'color_idx': 0,
                'line_idx': 0,
                'segment_idx': 0,
                'current_color': None,
                'was_paused': False
            }

            self.bot.single_color_mode_active = (self._mode == Bot.SINGLE_COLOR)
            result = self.bot.draw(cmap)
            self._root.deiconify()  # type: ignore
            self._root.wm_state('normal')  # type: ignore
            if result == 'success':
                actual_time = time.time() - t
                # Show time comparison if available
                if hasattr(self.bot, 'estimated_time_seconds'):
                    estimated_str = self.bot._format_time(self.bot.estimated_time_seconds)
                    actual_str = self.bot._format_time(actual_time)
                    diff_seconds = self.bot.estimated_time_seconds - actual_time
                    if diff_seconds >= 0:
                        diff_str = f"Saved: {self.bot._format_time(diff_seconds)}"
                    else:
                        diff_str = f"Extra: {self.bot._format_time(abs(diff_seconds))}"
                    self._status.set(f"Success! Est: {estimated_str}, Act: {actual_str}, {diff_str}")
                else:
                    self._status.set(f"Success. Time elapsed: {actual_time:.2f}s")
            elif result == 'terminated':
                actual_time = time.time() - t
                if hasattr(self.bot, 'estimated_time_seconds'):
                    estimated_str = self.bot._format_time(self.bot.estimated_time_seconds)
                    actual_str = self.bot._format_time(actual_time)
                    self._status.set(f"Terminated. Est: {estimated_str}, Act: {actual_str}")
                else:
                    self._status.set(f"Terminated by user. Time elapsed: {actual_time:.2f}s")
                # Reset bot state for fresh start after termination
                self.bot.draw_state = {
                    'color_idx': 0,
                    'line_idx': 0,
                    'segment_idx': 0,
                    'current_color': None,
                    'was_paused': False
                }
                # Clear termination flag so user can start again
                self.bot.terminate = False
            elif result == 'paused':
                actual_time = time.time() - t
                if hasattr(self.bot, 'estimated_time_seconds'):
                    estimated_str = self.bot._format_time(self.bot.estimated_time_seconds)
                    actual_str = self.bot._format_time(actual_time)
                    self._status.set(f"Paused. Press {self.bot.pause_key} again to resume. Est: {estimated_str}, Act: {actual_str}")
                else:
                    self._status.set(f"Paused. Press {self.bot.pause_key} again to resume. Time elapsed: {actual_time:.2f}s")
            else:
                self._status.set(f"Unknown result: {result}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(self.title, str(e))
        finally:
            # Clear the temp-memory Color Picker palette when the draw ends
            # (success, terminated, paused, or error) — the next Start asks again.
            self.bot.clear_loaded_palette()

        # Let the thread manager know that the task has ended
        self._set_busy(False)

    @is_free
    def start_palette_window(self):
        """Open color palette generation window"""
        try:
            if not hasattr(self, '_imname') or not self._imname:
                messagebox.showerror(self.title, 'No image loaded. Please load an image first.')
                self._set_busy(False)
                return
            
            # Check if image file exists
            if not os.path.exists(self._imname):
                messagebox.showerror(self.title, f'Image file not found: {self._imname}')
                self._set_busy(False)
                return
            
            # Open palette window
            PaletteWindow(self._root, self._imname, self.bot)
            
            self._status.set('Palette window opened.')
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(self.title, f'Failed to open palette window: {str(e)}')
        finally:
            self._set_busy(False)

    @is_free
    def start_interactive_mode(self):
        was_iconified = False
        try:
            self._status.set('Starting Interactive Layer Mode...')
            if not hasattr(self, '_imname') or not os.path.isfile(self._imname):
                messagebox.showerror(self.title, "Please load an image first.")
                self._set_busy(False)
                return
            # Check canvas is initialized
            if not self.bot._canvas:
                messagebox.showerror(self.title, "Please initialize the canvas in Setup first.")
                self._set_busy(False)
                return
            warning = ("Interactive Layer Mode lets you pick colors from your image and draw them one at a time.\n\n"
                       "WARNING: This mode is significantly slower than automatic drawing.\n"
                       "You have full control over flatness and stroke style.\n\n"
                       "Click the image in the controller to select a color to draw.\n"
                       "Keyboard shortcuts: Y = Draw, ESC = Close\n\n"
                       "Continue?")
            if not messagebox.askyesno(self.title, warning):
                self._set_busy(False)
                return
            from ui.interactive_layer_window import InteractiveLayerController
            self._root.iconify()
            was_iconified = True
            InteractiveLayerController(self._root, self.bot, self._imname, self.draw_options, self._mode)
            self._status.set('Interactive Layer Mode completed.')
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(self.title, f'Interactive Mode failed: {str(e)}')
        finally:
            if was_iconified:
                self._root.deiconify()
                self._root.wm_state('normal')
            self._set_busy(False)

    # ------------------------------------------------------------------
    # Compat properties (state lives in the panels)
    # ------------------------------------------------------------------

    @property
    def _mode(self):
        return self._settings.mode

    @_mode.setter
    def _mode(self, value):
        self._settings.mode = value

    @property
    def draw_options(self):
        return self._settings.draw_options

    @draw_options.setter
    def draw_options(self, value):
        self._settings.draw_options = value

    @property
    def _imname(self):
        return self._image_panel.imname

    @_imname.setter
    def _imname(self, value):
        self._image_panel.imname = value

