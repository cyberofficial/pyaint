"""
ImagePanel — image preview, URL/file loading, and remote image fetching.

Extracted from Window._init_ipanel / _set_img / _on_search_img / _open_file
/ _fetch_remote_image. Holds the current image path (``imname``) and the
last entered URL (``last_url``), which Window accesses via properties.
"""

import os
import tempfile
import time
import traceback
import urllib.error as urllib_error
import urllib.request
import utils
from genericpath import isfile
from tkinter import END, filedialog
from tkinter.ttk import Button, Entry, Frame, Label
from PIL import Image, ImageTk
from utils import resource_path


class ImagePanel(Frame):
    """Image preview + URL/file load controls."""

    def __init__(self, parent, controller, config):
        super().__init__(parent)
        self._controller = controller  # duck-typed Window
        self._config = config
        self.imname = 'sample.png'
        self.last_url = None  # Last entered URL
        self._img = None
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=3, uniform='column')
        self.columnconfigure(1, weight=1, uniform='column')
        self.columnconfigure(2, weight=1, uniform='column')
        self.rowconfigure(0, weight=4, uniform='row')
        self.rowconfigure(1, weight=1, uniform='row')

        self._ilabel = Label(self)
        self._ilabel.bind('<Configure>', lambda e: self.load_image(path=self.imname))
        self._ilabel.grid(column=0, row=0, columnspan=3, sticky='ns', padx=5, pady=5)

        self._ientry = Entry(self)
        ImagePanel._set_etext(self._ientry, 'Enter URL or File System Path')
        self._ientry.grid(column=0, row=1, sticky='ew', padx=5, pady=5)

        self._search_btn = Button(self, text='Search', command=self._on_search_img)
        self._search_btn.grid(column=1, row=1, sticky='ew', padx=5, pady=5)
        self._file_btn = Button(self, text='Open File', command=self._open_file)
        self._file_btn.grid(column=2, row=1, sticky='ew', padx=5, pady=5)

    @staticmethod
    def _set_etext(e, txt):
        e.delete(0, END)
        e.insert(0, txt)

    # ------------------------------------------------------------------
    # Image display
    # ------------------------------------------------------------------

    def load_image(self, image=None, path=None):
        """Display the given PIL image or load one from ``path``."""
        if image is not None:
            img = image
        else:
            self.imname = path if path is not None else resource_path('assets/sample.png')
            img = Image.open(self.imname)

        # Resize image. The panel may not be laid out yet (e.g. when the
        # Preview tab is not selected); the <Configure> binding re-renders
        # once it becomes visible, so clamp to a sane minimum here.
        self.update()
        avail_w = max(self.winfo_width() - 10, 50)
        avail_h = max(self.winfo_height() * .8 - 10, 50)
        size = utils.adjusted_img_size(img, (avail_w, avail_h))
        self._img = ImageTk.PhotoImage(img.resize(size))
        self._ilabel['image'] = self._img

        # Check cache status and update status (only if canvas is initialized)
        bot = self._controller.bot
        if hasattr(bot, '_canvas') and bot._canvas is not None:
            has_cache, _ = bot.get_cached_status(
                self.imname, flags=self._controller.draw_options, mode=self._controller._mode)
            if has_cache:
                self._controller._status.set('Cached computation available ✓')
            else:
                self._controller._status.set('No cached computation - will process live')
        else:
            self._controller._status.set('Loading configuration...')

    def load_from_config(self):
        """Restore the last entered URL from config."""
        last_url = self._config.get('last_image_url', '')
        if last_url:
            self._ientry.delete(0, END)
            self._ientry.insert(0, last_url)
            self.last_url = last_url

    # ------------------------------------------------------------------
    # Image source handling
    # ------------------------------------------------------------------

    def _fetch_remote_image(self, url, timeout=10, retries=3):
        """Fetch remote image with proper headers and error handling."""
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )

        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    # Check if response is actually an image
                    content_type = response.headers.get('content-type', '').lower()
                    if not content_type.startswith('image/'):
                        raise ValueError(f"URL does not point to an image (content-type: {content_type})")

                    # Create temporary file
                    fd, temp_path = tempfile.mkstemp(suffix='.png')
                    try:
                        with os.fdopen(fd, 'wb') as tmp_file:
                            tmp_file.write(response.read())
                        return temp_path
                    except Exception:
                        try:
                            os.close(fd)  # fd may already be closed by fdopen's context manager
                        except OSError:
                            pass
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        raise

            except urllib_error.HTTPError as e:
                if e.code == 429:  # Rate limited
                    wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                    print(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{retries}")
                    time.sleep(wait_time)
                    continue
                elif e.code >= 400:
                    raise ValueError(f"HTTP {e.code}: {e.reason}")
                else:
                    raise
            except urllib_error.URLError as e:
                if attempt == retries - 1:
                    raise ValueError(f"Network error: {e.reason}")
                continue

        raise ValueError("Failed to fetch image after all retries")

    def _on_search_img(self):
        try:
            input_text = self._ientry.get().strip()
            if not input_text:
                self._controller._status.set('Please enter a URL or file path')
                return

            # Check if it's a local file first
            if isfile(input_text):
                path = input_text
                # Don't save file paths as URLs
                self.last_url = None
            else:
                # Try to fetch as remote image
                self._controller._status.set('Fetching remote image...')
                path = self._fetch_remote_image(input_text)
                # Save the URL for persistence
                self.last_url = input_text
                self._config.set('last_image_url', input_text)

            self.load_image(path=path)
            self._controller._status.set('Image loaded successfully')

        except ValueError as e:
            self._controller._status.set(f'Error: {str(e)}')
        except Exception as e:
            traceback.print_exc()
            self._controller._status.set(f'Unexpected error: {str(e)}')

    def _open_file(self):
        try:
            path = filedialog.askopenfile(parent=self._controller._root)
            if path is not None:
                self.load_image(path=path.name)
        except Exception as e:
            self._controller._status.set(str(e))
