import json

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSlider, QStackedWidget, QTabWidget, QVBoxLayout, QWidget,
)

from SIA import featured_store
from SIA.catalog import FEATURED_VIDEOS
from SIA.ui import FunctionWorker, format_clock, make_title
from SIA.video_api import search_videos

PLACEHOLDER_HTML = (
    "<html><body style='background:#202020;color:#ddd;font-family:sans-serif;"
    "display:grid;place-items:center'>Select a video to play it here.</body></html>"
)


class VideoWindow(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.search_worker = None
        self.youtube_active = False   # True while a YouTube video is loaded
        self.youtube_playing = False  # our best guess of its play/pause state
        self.volume = 80              # 0-100, shared by both players
        self.setWindowTitle("Movies and TV Shows")
        self.resize(900, 780)

        # --- players: native for the featured MP4s, embedded web view for YouTube ---
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)
        self.web_view = QWebEngineView()
        # let the YouTube embed start playing without an extra click
        self.web_view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False
        )
        self.web_view.setHtml(PLACEHOLDER_HTML)
        self.stage = QStackedWidget()
        self.stage.addWidget(self.web_view)
        self.stage.addWidget(self.video_widget)
        self.stage.setMinimumHeight(320)

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        back = QPushButton("Back")
        back.clicked.connect(self.back_requested.emit)
        header.addWidget(make_title("Movies and TV Shows"))
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
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.volume)
        self.volume_slider.setFixedWidth(90)
        self.volume_slider.valueChanged.connect(self._on_volume)
        self.audio.setVolume(self.volume / 100)
        for widget in (self.play_button, stop_button):
            row.addWidget(widget)
        row.addWidget(self.position_slider, stretch=1)
        row.addWidget(self.time_label)
        row.addWidget(QLabel("Vol"))
        row.addWidget(self.volume_slider)
        return row

    def _build_featured_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        self.featured_list = QListWidget()
        self.featured_list.itemClicked.connect(self._play_item)
        box.addWidget(self.featured_list)
        remove_button = QPushButton("Remove selected from Featured")
        remove_button.clicked.connect(self._remove_featured)
        box.addWidget(remove_button)
        self._refresh_featured()
        return page

    def _refresh_featured(self):
        """Built-in videos first, then the ones you added (marked with a star)."""
        entries = [(x, False) for x in FEATURED_VIDEOS] + [(x, True) for x in featured_store.load("videos")]
        self.featured_list.clear()
        for video, custom in entries:
            star = "★ " if custom else ""
            item = QListWidgetItem(f"{star}{video['title']} — {video['subtitle']}")
            # a "kind" key (e.g. "youtube") overrides the default "file"
            item.setData(Qt.ItemDataRole.UserRole, {"kind": "file", **video, "custom": custom})
            self.featured_list.addItem(item)

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
        add_button = QPushButton("★ Add selected video to Featured")
        add_button.clicked.connect(self._add_to_featured)
        box.addWidget(add_button)
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

    # ---------- featured management ----------
    def _add_to_featured(self):
        item = self.results.currentItem()
        if item is None:
            self.status_label.setText("Search and select a video first.")
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        entry = {"kind": "youtube", "title": data["title"], "subtitle": data["channel"], "video_id": data["video_id"]}
        if any(x.get("video_id") == entry["video_id"] for x in FEATURED_VIDEOS) or not featured_store.add("videos", entry):
            self.status_label.setText(f"\"{entry['title']}\" is already in Featured.")
            return
        self._refresh_featured()
        self.status_label.setText(f"Added \"{entry['title']}\" to Featured.")

    def _remove_featured(self):
        item = self.featured_list.currentItem()
        if item is None:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data.get("custom"):
            self.status_label.setText("Built-in videos can't be removed here (edit catalog.py).")
            return
        featured_store.remove("videos", data)
        self._refresh_featured()
        self.status_label.setText("Removed from Featured.")

    # ---------- playback ----------
    def _play_item(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data["kind"] == "file":
            self.youtube_active = False
            self.youtube_playing = False
            self.web_view.setHtml(PLACEHOLDER_HTML)  # unload any YouTube iframe
            self.stage.setCurrentWidget(self.video_widget)
            self.player.setSource(QUrl(data["url"]))
            self.player.play()
            self.status_label.setText(f"Playing: {data['title']}")
        else:
            self.player.stop()
            self.position_slider.setValue(0)
            self.time_label.setText("0:00 / 0:00")
            self.stage.setCurrentWidget(self.web_view)
            self._play_youtube(data["video_id"])
            self.status_label.setText(f"Playing: {data['title']}")

    def _play_youtube(self, video_id):
        # enablejsapi=1 lets us send play/pause/volume commands to the player
        embed_url = (
            f"https://www.youtube-nocookie.com/embed/{video_id}"
            "?autoplay=1&rel=0&enablejsapi=1"
            "&origin=https://www.youtube-nocookie.com"
        )
        html = (
            "<!DOCTYPE html><html><head><style>"
            "html,body{margin:0;width:100%;height:100%;background:#000;overflow:hidden}"
            "iframe{width:100%;height:100%;border:none}</style></head><body>"
            f'<iframe id="player" src="{embed_url}" '
            'allow="autoplay; encrypted-media; fullscreen" allowfullscreen></iframe>'
            "</body></html>"
        )
        # A real https base URL gives YouTube a valid referrer (avoids the embed error
        # you can get with a "localhost" origin).
        self.web_view.setHtml(html, QUrl("https://www.youtube-nocookie.com"))
        self.youtube_active = True
        self.youtube_playing = True
        self.play_button.setText("Pause")
        # the player needs a moment to start; then apply the slider's volume
        QTimer.singleShot(2000, self._apply_youtube_volume)

    def _youtube_command(self, command, args=""):
        """Send a command (playVideo, pauseVideo, setVolume...) to the YouTube iframe."""
        message = json.dumps({"event": "command", "func": command, "args": args})
        js = (
            "var p = document.getElementById('player');"
            f"if (p) p.contentWindow.postMessage({json.dumps(message)}, '*');"
        )
        self.web_view.page().runJavaScript(js)

    def _apply_youtube_volume(self):
        if self.youtube_active:
            self._youtube_command("setVolume", [self.volume])

    def _on_volume(self, value):
        self.volume = value
        self.audio.setVolume(value / 100)   # MP4 player
        self._apply_youtube_volume()        # YouTube player

    def _toggle_play(self):
        # YouTube video: send a command to the web page
        if self.stage.currentWidget() is self.web_view:
            if not self.youtube_active:
                return
            self.youtube_playing = not self.youtube_playing
            self._youtube_command("playVideo" if self.youtube_playing else "pauseVideo")
            self.play_button.setText("Pause" if self.youtube_playing else "Play")
            return

        # Featured MP4: use the native player
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.player.source().isValid():
            self.player.play()
        else:
            item = self.featured_list.currentItem() or self.featured_list.item(0)
            if item is None:
                self.status_label.setText("Featured is empty. Search and add a video first.")
                return
            self._play_item(item)

    def stop_playback(self):
        self.youtube_active = False
        self.youtube_playing = False
        self.player.stop()
        self.player.setSource(QUrl())
        self.web_view.setHtml(PLACEHOLDER_HTML)
        self.stage.setCurrentWidget(self.web_view)
        self.position_slider.setValue(0)
        self.time_label.setText("0:00 / 0:00")
        self.play_button.setText("Play")

    on_leave = stop_playback

    def _on_state(self, state):
        if self.youtube_active:
            return  # the button label belongs to the YouTube player right now
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