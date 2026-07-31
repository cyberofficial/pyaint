"""
ConfigManager — single source of truth for config.json read/write.

Replaces the repeated json.load/json.dump blocks that were scattered across
Window and its child windows. Auto-saves on every mutation, unless a batch
is in progress (``begin_batch`` / ``end_batch``), which replaces the old
``_initializing`` flag hack.
"""

import json


class ConfigManager:
    """Centralized config.json persistence with batch mode and typed accessors."""

    def __init__(self, path):
        self._path = path
        self._data = {}
        self._batch_depth = 0
        self._dirty = False

    # ------------------------------------------------------------------
    # Basic I/O
    # ------------------------------------------------------------------

    @property
    def path(self):
        return self._path

    @property
    def data(self):
        """The raw config dict. Existing code may read/mutate it directly."""
        return self._data

    def load(self):
        """Load config from disk. Returns the data dict; missing/invalid
        config falls back to an empty dict (mirrors old behavior).

        Mutates the existing dict in place so external references to
        ``self.data`` (e.g. Window's ``self.tools`` alias) stay valid.
        """
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
        except FileNotFoundError:
            loaded = {}
        except Exception as e:
            print(f"Config file missing or invalid ({e}). Using default settings.")
            loaded = {}
        self._data.clear()
        self._data.update(loaded)
        print(f"Loaded config from {self._path}; keys={list(self._data.keys())}")
        return self._data

    def save(self):
        """Write the config dict to disk. Best-effort, never raises."""
        try:
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=4)
            print(f"Saved config to {self._path}; keys={list(self._data.keys())}")
        except Exception as e:
            print(f"Failed to save config: {e}")

    # ------------------------------------------------------------------
    # Batch mode (replaces the _initializing flag)
    # ------------------------------------------------------------------

    def begin_batch(self):
        """Suppress auto-save until ``end_batch`` is called. Nested calls
        are counted; pending changes are only cleared when opening the
        outermost batch."""
        if self._batch_depth == 0:
            self._dirty = False
        self._batch_depth += 1

    def end_batch(self):
        """Re-enable auto-save and flush any pending changes once."""
        if self._batch_depth > 0:
            self._batch_depth -= 1
        if self._batch_depth == 0 and self._dirty:
            self._dirty = False
            self.save()

    # ------------------------------------------------------------------
    # Generic accessors
    # ------------------------------------------------------------------

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        """Set a top-level config value and save (unless batching)."""
        self._data[key] = value
        self._persist()

    def _persist(self):
        if self._batch_depth > 0:
            self._dirty = True
        else:
            self.save()

    # ------------------------------------------------------------------
    # Typed accessors
    # ------------------------------------------------------------------

    def get_pause_key(self):
        return self._data.get('pause_key', 'p')

    def set_pause_key(self, key):
        self.set('pause_key', key)

    def get_drawing_settings(self):
        return self._data.get('drawing_settings', {})

    def set_drawing_setting(self, key, value):
        settings = self.get_drawing_settings()
        settings[key] = value
        self._data['drawing_settings'] = settings
        self._persist()

    def get_drawing_options(self):
        """Return the raw drawing_options sub-dict (not the bot flag int)."""
        return self._data.get('drawing_options', {})

    def set_drawing_option(self, key, value):
        options = self.get_drawing_options()
        options[key] = value
        self._data['drawing_options'] = options
        self._persist()

    def get_tool(self, name):
        return self._data.get(name, {})

    def set_tool(self, name, data):
        self.set(name, data)

    def get_calibration_settings(self):
        return self._data.get('calibration_settings', {})

    def set_calibration_setting(self, key, value):
        settings = self.get_calibration_settings()
        settings[key] = value
        self._data['calibration_settings'] = settings
        self._persist()
