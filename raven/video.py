from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSlider, QStackedWidget, QTabWidget, QVBoxLayout, QWidget,
)

from raven.catalog import FEATURED_VIDEOS
from raven.ui import FunctionWorker, format_clock, make_title
from raven.video_api import search_videos

PLACEHOLDER_HTML = (
    "<html><body style='background:#202020;color:#ddd;font-family:sans-serif;"
    "display:grid;place-items:center'>Select a video to play it here.</body></html>"
)


class VideoWindow(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.search_worker = None
        self.setWindowTitle("Raven — Video")
        self.resize(900, 780)

        # --- players: native for the featured MP4s, embedded web view for YouTube search ---
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)
        self.web_view = QWebEngineView()
        self.web_view.setHtml(PLACEHOLDER_HTML)
        self.stage = QStackedWidget()
        self.stage.addWidget(self.web_view)
        self.stage.addWidget(self.video_widget)
        self.stage.setMinimumHeight(320)

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        back = QPushButton("Back")
        back.clicked.connect(self.back_requested.emit)
        header.addWidget(make_title("Video"))
        header.addStretch(1)
        header.addWidget(back)
        layout.addLayout(header)

        layout.addWidget(self.stage, stretch=3)
        layout.addLayout(self._build_controls())

        self.status_label = QLabel("Pick a featured video or search YouTube.")
        layout.addWidget(self.status_label)

        tabs = QTabWidget()
        tabs.addTab(self._build_featured_tab(), "Featured")
        tabs.addTab(self._build_search_tab(), "Search YouTube")
        layout.addWidget(tabs, stretch=2)

        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.errorOccurred.connect(self._on_player_error)

    # ---------- UI builders ----------
    def _build_controls(self):
        row = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self._toggle_play)
        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_playback)
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderReleased.connect(
            lambda: self.player.setPosition(self.position_slider.value())
        )
        self.time_label = QLabel("0:00 / 0:00")
        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 100)
        volume.setValue(80)
        volume.setFixedWidth(90)
        volume.valueChanged.connect(lambda v: self.audio.setVolume(v / 100))
        self.audio.setVolume(0.8)
        for widget in (self.play_button, stop_button):
            row.addWidget(widget)
        row.addWidget(self.position_slider, stretch=1)
        row.addWidget(self.time_label)
        row.addWidget(QLabel("Vol"))
        row.addWidget(volume)
        return row

    def _build_featured_tab(self):
        self.featured_list = QListWidget()
        for video in FEATURED_VIDEOS:
            item = QListWidgetItem(f"{video['title']} — {video['subtitle']}")
            item.setData(Qt.ItemDataRole.UserRole, {"kind": "file", **video})
            self.featured_list.addItem(item)
        self.featured_list.itemClicked.connect(self._play_item)
        return self.featured_list

    def _build_search_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search YouTube")
        self.search_box.returnPressed.connect(self._start_search)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._start_search)
        row.addWidget(self.search_box, stretch=1)
        row.addWidget(self.search_button)
        box.addLayout(row)
        self.results = QListWidget()
        self.results.itemClicked.connect(self._play_item)
        box.addWidget(self.results)
        return page

    # ---------- search ----------
    def _start_search(self):
        term = self.search_box.text().strip()
        if not term:
            self.status_label.setText("Type a search term first.")
            return
        if self.search_worker and self.search_worker.isRunning():
            return
        self.search_button.setEnabled(False)
        self.status_label.setText("Searching YouTube...")
        self.search_worker = FunctionWorker(search_videos, term)
        self.search_worker.succeeded.connect(self._show_results)
        self.search_worker.failed.connect(lambda m: self.status_label.setText(f"Video search failed: {m}"))
        self.search_worker.finished.connect(lambda: self.search_button.setEnabled(True))
        self.search_worker.start()

    def _show_results(self, videos):
        self.results.clear()
        for video in videos:
            item = QListWidgetItem(f"{video['title']} — {video['channel']}")
            item.setData(Qt.ItemDataRole.UserRole, {"kind": "youtube", **video})
            self.results.addItem(item)
        self.status_label.setText(
            f"{len(videos)} videos found. Click one to play it here." if videos else "No videos found."
        )

    # ---------- playback ----------
    def _play_item(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data["kind"] == "file":
            self.web_view.setHtml(PLACEHOLDER_HTML)  # unload any YouTube iframe
            self.stage.setCurrentWidget(self.video_widget)
            self.player.setSource(QUrl(data["url"]))
            self.player.play()
            self.status_label.setText(f"Playing: {data['title']}")
        else:
            self.player.stop()
            self.stage.setCurrentWidget(self.web_view)
            self._play_youtube(data["video_id"])
            self.status_label.setText(f"Playing: {data['title']}")

    def _play_youtube(self, video_id):
        embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1&rel=0"
        html = (
            "<!DOCTYPE html><html><head><style>"
            "html,body{margin:0;width:100%;height:100%;background:#000;overflow:hidden}"
            "iframe{width:100%;height:100%;border:none}</style></head><body>"
            f'<iframe src="{embed_url}" allow="autoplay; encrypted-media; fullscreen" '
            "allowfullscreen></iframe></body></html>"
        )
        # A real https base URL gives YouTube a valid referrer (avoids the embed error
        # you can get with a "localhost" origin).
        self.web_view.setHtml(html, QUrl("https://www.youtube-nocookie.com"))

    def _toggle_play(self):
        if self.stage.currentWidget() is not self.video_widget:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.player.source().isValid():
            self.player.play()
        else:
            item = self.featured_list.currentItem() or self.featured_list.item(0)
            self._play_item(item)

    def stop_playback(self):
        self.player.stop()
        self.player.setSource(QUrl())
        self.web_view.setHtml(PLACEHOLDER_HTML)
        self.stage.setCurrentWidget(self.web_view)
        self.position_slider.setValue(0)

    on_leave = stop_playback

    def _on_state(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_button.setText("Pause" if playing else "Play")

    def _on_position(self, position):
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        self._update_time()

    def _on_duration(self, duration):
        self.position_slider.setRange(0, max(duration, 0))
        self._update_time()

    def _update_time(self):
        self.time_label.setText(f"{format_clock(self.player.position())} / {format_clock(self.player.duration())}")

    def _on_player_error(self, _error, message):
        self.status_label.setText(f"Playback failed: {message}")

    def closeEvent(self, event):
        self.stop_playback()
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.wait(2000)
        super().closeEvent(event)