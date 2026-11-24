"""Small helpers shared by every window (removes the copy-pasted boilerplate)."""
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QLabel


def make_title(text, point_size=16):
    label = QLabel(text)
    font = label.font()
    font.setPointSize(point_size)
    label.setFont(font)
    return label


def format_clock(milliseconds):
    total_seconds = max(int(milliseconds or 0) // 1000, 0)
    return f"{total_seconds // 60}:{total_seconds % 60:02d}"


class FunctionWorker(QThread):
    """Runs any function off the UI thread. Replaces the two duplicated SearchWorkers."""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, function, *args):
        super().__init__()
        self._function = function
        self._args = args

    def run(self):
        try:
            self.succeeded.emit(self._function(*self._args))
        except Exception as error:
            self.failed.emit(str(error))