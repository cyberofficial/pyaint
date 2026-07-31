"""
ThreadManager — generic lifecycle for background drawing/calibration threads.

Replaces the duplicated start_*_thread / _manage_*_thread pairs in Window
with a single polling mechanism driven by ``root.after``. Each background
operation is described by a :class:`ThreadJob`; the manager launches the
thread and polls it until it finishes, updating the status bar via a
callback. Jobs with bespoke progress UIs (e.g. the calibration overlay)
can supply a custom ``poll_fn`` that takes over the polling body.
"""

from threading import Thread


class ThreadJob:
    """Descriptor for one managed background operation."""

    def __init__(self, name, target, *, poll_ms=500, progress_getter=None,
                 progress_msg=None, running_msg=None, done_msg=None,
                 on_done=None, poll_fn=None):
        self.name = name
        self.target = target
        self.poll_ms = poll_ms
        # progress_getter: callable() -> float (e.g. bot.progress)
        self.progress_getter = progress_getter
        # progress_msg: callable(progress: float) -> str, shown each poll
        self.progress_msg = progress_msg
        # running_msg: static status shown while running (no progress)
        self.running_msg = running_msg
        # done_msg: status shown once when the thread finishes
        self.done_msg = done_msg
        # on_done: callable() invoked once when the thread finishes
        self.on_done = on_done
        # poll_fn: optional callable(job) -> bool replacing the default poll
        # body. Return True to keep polling, False to stop. When provided,
        # it owns the whole lifecycle (status, busy flag, cleanup).
        self.poll_fn = poll_fn
        self.thread = None

    def format_running(self):
        if self.progress_getter is not None and self.progress_msg is not None:
            return self.progress_msg(self.progress_getter())
        if self.running_msg is not None:
            return self.running_msg
        return None


class ThreadManager:
    """Owns ``root.after`` scheduling for background threads."""

    def __init__(self, root, on_status):
        self._root = root
        self._on_status = on_status

    def start(self, job):
        """Launch the job on a daemon thread and begin polling."""
        job.thread = Thread(target=job.target, daemon=True)
        job.thread.start()
        self._root.after(job.poll_ms, lambda: self._poll(job))

    def _poll(self, job):
        """Called repeatedly by root.after while the job runs."""
        if job.poll_fn is not None:
            # Custom poll body owns the lifecycle; reschedule while it
            # returns True (meaning "keep polling").
            if not job.poll_fn(job):
                return
            self._root.after(job.poll_ms, lambda: self._poll(job))
            return

        if job.thread.is_alive():
            msg = job.format_running()
            if msg is not None:
                self._on_status(msg)
            self._root.after(job.poll_ms, lambda: self._poll(job))
        else:
            if job.done_msg is not None:
                self._on_status(job.done_msg)
            if job.on_done is not None:
                job.on_done()
