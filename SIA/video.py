
import json

import PySide6

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
from SIA.ui import FunctionWorker, SeekSlider, format_clock, make_title
from SIA.video_api import search_videos

PLACEHOLDER_HTML = (
    "<html><body style='background:#202020;color:#ddd;font-family:sans-serif;"
    "display:grid;place-items:center'>Select a video to play it here.</body></html>"
)


YOUTUBE_PAGE = """<!DOCTYPE html><html><head><style>
html,body{margin:0;width:100%;height:100%;background:#000;overflow:hidden}
iframe{width:100%;height:100%;border:none}
</style></head><body>
<iframe id="player"
  src="https://www.youtube-nocookie.com/embed/__VIDEO_ID__?autoplay=1&controls=0&disablekb=1&fs=0&rel=0&playsinline=1&modestbranding=1&iv_load_policy=3&origin=https://www.youtube-nocookie.com"
  allow="autoplay; encrypted-media" allowfullscreen></iframe>
</body></html>"""

# JavaScript that gets the video information from the YouTube player.
YT_STATE_JS = (
    "(function(){var v=document.querySelector('video');"
    "if(!v){return 'null';}"
    "return JSON.stringify([v.currentTime||0,(isFinite(v.duration)?v.duration:0),v.paused?2:1,0]);})()"
)


class VideoWindow(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.search_worker = None
        self.youtube_active = False   # True when a YouTube video is loaded
        self.youtube_playing = False  # Tracks the YouTube play/pause state
        self.youtube_error_shown = False
        self.youtube_misses = 0       # Counts failed responses from YouTube
        self.youtube_debug = ""       # Stores the reason for missing responses
        self.youtube_timer = QTimer(self)  # Checks the YouTube player regularly
        self.youtube_timer.setInterval(500)
        self.youtube_timer.timeout.connect(self._poll_youtube)
        self.volume = 80              # Shared volume for both players
        self.setWindowTitle("VIDEOS")
        self.resize(900, 780)

        # Set up the players: native player for MP4 files and web view for YouTube
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)
        self.web_view = QWebEngineView()
        # Allow YouTube videos to play automatically
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
        header.addWidget(make_title("VIDEOS"))
        header.addStretch(1)
        header.addWidget(back)
        layout.addLayout(header)

        layout.addWidget(self.stage, stretch=3)
        layout.addLayout(self._build_controls())

        self.status_label = QLabel("Pick a favorite video or search YouTube.")
        layout.addWidget(self.status_label)

        tabs = QTabWidget()
        tabs.addTab(self._build_featured_tab(), "Favorites")
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
        self.position_slider = SeekSlider()
        self.position_slider.setRange(0, 0)
        self.position_slider.seek_requested.connect(self._seek)
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
        remove_button = QPushButton("Remove selected from Favorites")
        remove_button.clicked.connect(self._remove_featured)
        box.addWidget(remove_button)
        self._refresh_featured()
        return page

    def _refresh_featured(self):
        """Show built-in videos first, followed by added videos marked with a star."""
        entries = [(x, False) for x in FEATURED_VIDEOS] + [(x, True) for x in featured_store.load("videos")]
        self.featured_list.clear()
        for video, custom in entries:
            star = "★ " if custom else ""
            item = QListWidgetItem(f"{star}{video['title']} — {video['subtitle']}")
            # The "kind" key identifies the video type. The default type is "file".
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
        add_button = QPushButton("★ Add selected video to Favorites")
        add_button.clicked.connect(self._add_to_featured)
        box.addWidget(add_button)
        return page

    # ---------- Search ----------
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

    # ---------- Featured video management ----------
    def _add_to_featured(self):
        item = self.results.currentItem()
        if item is None:
            self.status_label.setText("Search and select a video first.")
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        entry = {"kind": "youtube", "title": data["title"], "subtitle": data["channel"], "video_id": data["video_id"]}
        if any(x.get("video_id") == entry["video_id"] for x in FEATURED_VIDEOS) or not featured_store.add("videos", entry):
            self.status_label.setText(f"\"{entry['title']}\" is already in Favorites.")
            return
        self._refresh_featured()
        self.status_label.setText(f"Added \"{entry['title']}\" to Favorites.")

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
        self.status_label.setText("Removed from Favorites.")

    # ---------- Video playback ----------
    def _play_item(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data["kind"] == "file":
            self.youtube_active = False
            self.youtube_playing = False
            self.youtube_timer.stop()
            self.web_view.setHtml(PLACEHOLDER_HTML)  # Close the YouTube video
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
        html = YOUTUBE_PAGE.replace("__VIDEO_ID__", video_id)
        # Use an HTTPS base URL so YouTube can recognize the page correctly.
        self.web_view.setHtml(html, QUrl("https://www.youtube-nocookie.com"))
        self.youtube_active = True
        self.youtube_playing = True
        self.youtube_error_shown = False
        self.youtube_misses = 0
        self.position_slider.setRange(0, 0)
        self.play_button.setText("Pause")
        self.youtube_timer.start()
        QTimer.singleShot(2500, self._apply_youtube_volume)

    def _youtube_frame(self):
        """Find the YouTube iframe inside the web view."""
        try:
            for frame in self.web_view.page().mainFrame().children():
                if frame.isValid() and "youtube" in frame.url().toString():
                    return frame
        except AttributeError:  # Handle older PySide6 versions without QWebEngineFrame
            self.youtube_debug = f"PySide6 {PySide6.__version__} is too old; run: python -m pip install -U PySide6"
            return None
        self.youtube_debug = "YouTube frame not found in the page"
        return None

    def _youtube_js(self, code, callback=None):
        """Run JavaScript inside the YouTube frame."""
        frame = self._youtube_frame()
        if frame is None:
            return False
        if callback is None:
            frame.runJavaScript(code, 0, lambda _result: None)
        else:
            frame.runJavaScript(code, 0, callback)
        return True

    def _poll_youtube(self):
        if not self.youtube_active:
            return
        if not self._youtube_js(YT_STATE_JS, self._on_youtube_result):
            self._on_youtube_state(None)

    def _on_youtube_result(self, result):
        try:
            state = json.loads(result) if result else None
        except (TypeError, ValueError):
            state = None
        if state is None:
            self.youtube_debug = "frame found but it has no video element yet" if result == "null" else "frame gave no answer"
        self._on_youtube_state(state)

    def _on_youtube_state(self, state):
        """Update the video controls using the YouTube player's information."""
        if not self.youtube_active:
            return
        if not state:
            self.youtube_misses += 1
            if self.youtube_misses == 16 and not self.youtube_error_shown:  # About 8 seconds
                self.status_label.setText(
                    f"The app can't reach the YouTube player, so the progress bar can't update. ({self.youtube_debug or 'no reason recorded'})"
                )
            return
        self.youtube_misses = 0
        current, duration, player_state, error = state
        self.youtube_playing = player_state == 1
        self.play_button.setText("Pause" if self.youtube_playing else "Play")
        current_ms, duration_ms = int(current * 1000), int(duration * 1000)
        self.position_slider.setRange(0, max(duration_ms, 0))
        if not self.position_slider.dragging:
            self.position_slider.setValue(current_ms)
        self.time_label.setText(f"{format_clock(current_ms)} / {format_clock(duration_ms)}")

    def _seek(self, value):
        if self.youtube_active:
            self._youtube_js(f"(function(){{var v=document.querySelector('video'); if(v){{v.currentTime={value / 1000};}}}})()")
        else:
            self.player.setPosition(value)

    def _apply_youtube_volume(self):
        if self.youtube_active:
            self._youtube_js(f"(function(){{var v=document.querySelector('video'); if(v){{v.volume={self.volume / 100};}}}})()")

    def _on_volume(self, value):
        self.volume = value
        self.audio.setVolume(value / 100)   # Set MP4 player volume
        self._apply_youtube_volume()        # Set YouTube player volume

    def _toggle_play(self):
        # Control playback for YouTube videos
        if self.stage.currentWidget() is self.web_view:
            if not self.youtube_active:
                return
            self.youtube_playing = not self.youtube_playing
            action = "play()" if self.youtube_playing else "pause()"
            self._youtube_js(f"(function(){{var v=document.querySelector('video'); if(v){{v.{action};}}}})()")
            self.play_button.setText("Pause" if self.youtube_playing else "Play")
            return

        # Control playback for featured MP4 videos
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
        self.youtube_timer.stop()
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
            return  # The play button is controlled by the YouTube player
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_button.setText("Pause" if playing else "Play")

    def _on_position(self, position):
        if not self.position_slider.dragging:
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
