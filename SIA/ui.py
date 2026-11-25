"""Small helpers shared by every window (removes the copy-pasted boilerplate)."""
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QLabel, QSlider, QStyle


def make_title(text, point_size=16):
    label = QLabel(text)
    label.setObjectName("title")  
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


class SeekSlider(QSlider):
    """Seek bar na tumatalon kung saan mo i-click, at nagse-seek kapag binitawan."""

    seek_requested = Signal(int)

    def __init__(self, orientation=Qt.Orientation.Horizontal):
        super().__init__(orientation)
        self.dragging = False

    def _value_at(self, x):
        return QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), int(x), max(self.width(), 1))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.maximum() > self.minimum():
            self.dragging = True
            self.setValue(self._value_at(event.position().x()))
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.setValue(self._value_at(event.position().x()))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.seek_requested.emit(self.value())
            event.accept()
        else:
            super().mouseReleaseEvent(event)