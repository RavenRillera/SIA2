from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSlider, QTabWidget, QVBoxLayout, QWidget,
)

from SIA import featured_store
from SIA.catalog import FEATURED_TRACKS
from SIA.music_api import search_songs
from SIA.ui import FunctionWorker, format_clock, make_title


class MusicWindow(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.search_worker = None
        self.active_list = None
        self.setWindowTitle("Music and Audio")
        self.resize(720, 660)

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.8)

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        back = QPushButton("Back")
        back.clicked.connect(self.back_requested.emit)
        header.addWidget(make_title("Music and Audio"))
        header.addStretch(1)
        header.addWidget(back)
        layout.addLayout(header)

        self.music_status = QLabel("Pick a favorite track or search Music (30-second previews).")
        layout.addWidget(self.music_status)

        tabs = QTabWidget()
        tabs.addTab(self._build_featured_tab(), "Favorites")
        tabs.addTab(self._build_search_tab(), "Search Music")
        layout.addWidget(tabs, stretch=1)

        self.now_playing = QLabel("Now playing: —")
        layout.addWidget(self.now_playing)
        layout.addLayout(self._build_controls())

        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.player.errorOccurred.connect(lambda _e, m: self.music_status.setText(f"Playback failed: {m}"))

    # ---------- UI builders ----------
    def _build_featured_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        self.featured_list = QListWidget()
        self.featured_list.itemDoubleClicked.connect(lambda item: self._play_item(self.featured_list, item))
        box.addWidget(self.featured_list)
        remove_button = QPushButton("Remove selected from Favorites")
        remove_button.clicked.connect(self._remove_featured)
        box.addWidget(remove_button)
        self._refresh_featured()
        return page

    def _refresh_featured(self):
        """Built-in tracks first, then the ones you added (marked with a star)."""
        entries = [(t, False) for t in FEATURED_TRACKS] + [(t, True) for t in featured_store.load("tracks")]
        self.featured_list.clear()
        for track, custom in entries:
            star = "★ " if custom else ""
            item = QListWidgetItem(f"{star}{track['title']} — {track['subtitle']}")
            item.setData(Qt.ItemDataRole.UserRole, track["url"])
            item.setData(Qt.ItemDataRole.UserRole + 1, track["title"])
            item.setData(Qt.ItemDataRole.UserRole + 2, custom)
            self.featured_list.addItem(item)
        if self.featured_list.count():
            self.featured_list.setCurrentRow(0)

    def _build_search_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Song, artist, or album")
        self.search_box.returnPressed.connect(self._start_search)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._start_search)
        row.addWidget(self.search_box, stretch=1)
        row.addWidget(self.search_button)
        box.addLayout(row)
        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(lambda item: self._play_item(self.results, item))
        box.addWidget(self.results)
        add_button = QPushButton("★ Add selected song to Favorites")
        add_button.clicked.connect(self._add_to_featured)
        box.addWidget(add_button)
        return page

    def _build_controls(self):
        box = QVBoxLayout()
        row = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self._toggle_play)
        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_playback)
        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 100)
        volume.setValue(80)
        volume.setFixedWidth(110)
        volume.valueChanged.connect(lambda v: self.audio.setVolume(v / 100))
        row.addWidget(self.play_button)
        row.addWidget(stop_button)
        row.addStretch(1)
        row.addWidget(QLabel("Volume"))
        row.addWidget(volume)
        box.addLayout(row)

        time_row = QHBoxLayout()
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderReleased.connect(
            lambda: self.player.setPosition(self.position_slider.value())
        )
        self.time_label = QLabel("0:00 / 0:00")
        time_row.addWidget(self.position_slider, stretch=1)
        time_row.addWidget(self.time_label)
        box.addLayout(time_row)
        return box

    # ---------- search ----------
    def _start_search(self):
        term = self.search_box.text().strip()
        if not term:
            self.music_status.setText("Type a song, artist, or album first.")
            return
        if self.search_worker and self.search_worker.isRunning():
            return
        self.search_button.setEnabled(False)
        self.music_status.setText("Calling the iTunes API...")
        self.search_worker = FunctionWorker(search_songs, term)
        self.search_worker.succeeded.connect(self._show_results)
        self.search_worker.failed.connect(lambda m: self.music_status.setText(f"The music API did not answer: {m}"))
        self.search_worker.finished.connect(lambda: self.search_button.setEnabled(True))
        self.search_worker.start()

    def _show_results(self, songs):
        self.results.clear()
        for song in songs:
            album = f" — {song['album']}" if song["album"] else ""
            item = QListWidgetItem(f"{song['title']} — {song['artist']}{album}")
            item.setData(Qt.ItemDataRole.UserRole, song["preview_url"])
            item.setData(Qt.ItemDataRole.UserRole + 1, f"{song['title']} — {song['artist']}")
            item.setData(Qt.ItemDataRole.UserRole + 3, song)
            self.results.addItem(item)
        if songs:
            self.results.setCurrentRow(0)
        self.music_status.setText(
            f"{len(songs)} songs found. Double-click one to play." if songs else "No playable songs for that search."
        )

    # ---------- featured management ----------
    def _add_to_featured(self):
        item = self.results.currentItem()
        if item is None:
            self.music_status.setText("Search and select a song first.")
            return
        song = item.data(Qt.ItemDataRole.UserRole + 3)
        entry = {"title": song["title"], "subtitle": song["artist"], "url": song["preview_url"]}
        if any(t["url"] == entry["url"] for t in FEATURED_TRACKS) or not featured_store.add("tracks", entry):
            self.music_status.setText(f"\"{entry['title']}\" is already in Featured.")
            return
        self._refresh_featured()
        self.music_status.setText(f"Added \"{entry['title']}\" to Featured.")

    def _remove_featured(self):
        item = self.featured_list.currentItem()
        if item is None:
            return
        if not item.data(Qt.ItemDataRole.UserRole + 2):
            self.music_status.setText("Built-in tracks can't be removed here (edit catalog.py).")
            return
        featured_store.remove("tracks", {"url": item.data(Qt.ItemDataRole.UserRole)})
        self._refresh_featured()
        self.music_status.setText("Removed from Featured.")

    # ---------- playback ----------
    def _play_item(self, source_list, item):
        self.active_list = source_list
        self.now_playing.setText(f"Now playing: {item.data(Qt.ItemDataRole.UserRole + 1)}")
        self.music_status.setText("Playing in this window.")
        self.player.setSource(QUrl(item.data(Qt.ItemDataRole.UserRole)))
        self.player.play()

    def _toggle_play(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()
        else:
            source_list = self.active_list or self.featured_list
            item = source_list.currentItem()
            if item is None:
                if source_list is self.featured_list and source_list.count() == 0:
                    self.music_status.setText("Featured is empty. Search and add a song first.")
                else:
                    self.music_status.setText("Pick a song first.")
                return
            self._play_item(source_list, item)

    def stop_playback(self):
        self.player.stop()
        self.now_playing.setText("Now playing: —")
        self.position_slider.setValue(0)

    on_leave = stop_playback

    def _on_media_status(self, status):
        # auto-advance to the next song in the list that is playing
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.active_list is not None:
            row = self.active_list.currentRow() + 1
            if row < self.active_list.count():
                self.active_list.setCurrentRow(row)
                self._play_item(self.active_list, self.active_list.item(row))

    def _on_state(self, state):
        self.play_button.setText("Pause" if state == QMediaPlayer.PlaybackState.PlayingState else "Play")

    def _on_position(self, position):
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        self._update_time()

    def _on_duration(self, duration):
        self.position_slider.setRange(0, max(duration, 0))
        self._update_time()

    def _update_time(self):
        self.time_label.setText(f"{format_clock(self.player.position())} / {format_clock(self.player.duration())}")

    def closeEvent(self, event):
        self.stop_playback()
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.wait(2000)
        super().closeEvent(event)