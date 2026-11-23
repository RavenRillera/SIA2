from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from raven.music_api import search_songs


class SearchWorker(QThread):
    succeeded = Signal(list)
    failed = Signal(str)

    def __init__(self, term):
        super().__init__()
        self.term = term

    def run(self):
        try:
            self.succeeded.emit(search_songs(self.term))
        except Exception as error:
            self.failed.emit(str(error))


class MusicWindow(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.search_worker = None
        self.setWindowTitle("Raven — Music")
        self.resize(720, 640)

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(1.0)

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Music")
        title_font = title.font()
        title_font.setPointSize(16)
        title.setFont(title_font)
        back = QPushButton("Back")
        back.clicked.connect(self.back_requested.emit)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(back)
        layout.addLayout(header)
        layout.addWidget(QLabel("Search calls the iTunes API. Play stays in this window."))

        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Song, artist, or album")
        self.search_box.returnPressed.connect(self._start_search)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._start_search)
        search_row.addWidget(self.search_box, stretch=1)
        search_row.addWidget(self.search_button)
        layout.addLayout(search_row)

        self.music_status = QLabel("No search yet.")
        layout.addWidget(self.music_status)

        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(lambda _item: self._play_selected())
        layout.addWidget(self.results, stretch=1)

        self.now_playing = QLabel("Now playing: —")
        layout.addWidget(self.now_playing)

        controls = QHBoxLayout()
        play_button = QPushButton("Play")
        pause_button = QPushButton("Pause")
        stop_button = QPushButton("Stop")
        play_button.clicked.connect(self._play_selected)
        pause_button.clicked.connect(self.player.pause)
        stop_button.clicked.connect(self._stop)
        controls.addWidget(play_button)
        controls.addWidget(pause_button)
        controls.addWidget(stop_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        time_row = QHBoxLayout()
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderReleased.connect(self._seek)
        self.time_label = QLabel("0:00 / 0:00")
        time_row.addWidget(self.position_slider, stretch=1)
        time_row.addWidget(self.time_label)
        layout.addLayout(time_row)

        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(lambda _state: self._update_time_label())
        self.player.errorOccurred.connect(self._on_player_error)

    def _start_search(self):
        term = self.search_box.text().strip()
        if not term:
            self.music_status.setText("Type a song, artist, or album first.")
            return
        if self.search_worker and self.search_worker.isRunning():
            return
        self.search_button.setEnabled(False)
        self.music_status.setText("Calling the iTunes API...")
        self.search_worker = SearchWorker(term)
        self.search_worker.succeeded.connect(self._show_results)
        self.search_worker.failed.connect(self._search_failed)
        self.search_worker.finished.connect(lambda: self.search_button.setEnabled(True))
        self.search_worker.start()

    def _show_results(self, songs):
        self.results.clear()
        for song in songs:
            album = f" — {song['album']}" if song["album"] else ""
            item = QListWidgetItem(f"{song['title']} — {song['artist']}{album}")
            item.setData(Qt.ItemDataRole.UserRole, song["preview_url"])
            item.setData(Qt.ItemDataRole.UserRole + 1, f"{song['title']} — {song['artist']}")
            self.results.addItem(item)
        if songs:
            self.results.setCurrentRow(0)
            self.music_status.setText(f"{len(songs)} songs from the API. Double-click one, or press Play.")
        else:
            self.music_status.setText("The API returned no playable songs for that search.")

    def _search_failed(self, message):
        self.music_status.setText(f"The music API did not answer: {message}")

    def _play_selected(self):
        item = self.results.currentItem()
        if item is None:
            self.music_status.setText("Search first, then choose a song.")
            return
        self.now_playing.setText(f"Now playing: {item.data(Qt.ItemDataRole.UserRole + 1)}")
        self.music_status.setText("Playing the API audio in this window.")
        self.player.setSource(QUrl(item.data(Qt.ItemDataRole.UserRole)))
        self.player.play()

    def _stop(self):
        self.player.stop()
        self.now_playing.setText("Now playing: —")
        self.position_slider.setValue(0)

    def _seek(self):
        self.player.setPosition(self.position_slider.value())

    def _on_position(self, position):
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        self._update_time_label()

    def _on_duration(self, duration):
        self.position_slider.setRange(0, max(duration, 0))
        self._update_time_label()

    def _update_time_label(self):
        self.time_label.setText(f"{_clock(self.player.position())} / {_clock(self.player.duration())}")

    def _on_player_error(self, _error, message):
        self.music_status.setText(f"Playback failed: {message}")

    def closeEvent(self, event):
        self._stop()
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.wait(2000)
        super().closeEvent(event)


def _clock(milliseconds):
    total_seconds = max(int(milliseconds or 0) // 1000, 0)
    return f"{total_seconds // 60}:{total_seconds % 60:02d}"
