from PySide6.QtCore import Signal, Qt, QThread, QUrl
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from raven.video_api import search_videos


class SearchWorker(QThread):
    succeed = Signal(list)
    failed = Signal(str)

    def __init__(self, term):
        super().__init__()
        self.term = term

    def run(self):
        try:
            videos = search_videos(self.term)
            self.succeed.emit(videos)
        except Exception as error:
            self.failed.emit(str(error))

class VideoWindow(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.search_worker = None
        self.setWindowTitle("Raven — Video")
        self.resize(900, 760)

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Video")
        title_font = title.font()
        title_font.setPointSize(16)
        title.setFont(title_font)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.back_requested.emit)

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(back_button)
        layout.addLayout(header)

        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search Videos")
        self.search_box.returnPressed.connect(self._start_search)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._start_search)

        search_row.addWidget(self.search_box, stretch=1)
        search_row.addWidget(self.search_button)
        layout.addLayout(search_row)

        self.status_label = QLabel("Search Videos.")
        layout.addWidget(self.status_label)

        self.results = QListWidget()
        self.results.itemClicked.connect(lambda _item: self._play_selected())
        layout.addWidget(self.results, stretch=1)

        self.player_view = QWebEngineView()
        self.player_view.setMinimumHeight(280)
        self.player_view.setHtml(
            "<html><body style='background:#202020;color:#ddd;"
            "font-family:sans-serif;display:grid;place-items:center'>"
            "Select a video to play it here.</body></html>"
        )
        layout.addWidget(self.player_view, stretch=2)

        play_button = QPushButton("Play selected video")
        play_button.clicked.connect(self._play_selected)
        layout.addWidget(play_button)

    def _start_search(self):
        term = self.search_box.text().strip()

        if not term:
            self.status_label.setText("Type a search term first.")
            return

        if self.search_worker and self.search_worker.isRunning():
            return

        self.search_button.setEnabled(False)
        self.status_label.setText("Searching YouTube...")

        self.search_worker = SearchWorker(term)
        self.search_worker.succeed.connect(self._show_results)
        self.search_worker.failed.connect(self._search_failed)
        self.search_worker.finished.connect(
            lambda: self.search_button.setEnabled(True)
        )
        self.search_worker.start()

    def _show_results(self, videos):
        self.results.clear()

        for video in videos:
            item = QListWidgetItem(
                f"{video['title']} — {video['channel']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, video["video_id"])
            self.results.addItem(item)

        if videos:
            self.results.setCurrentRow(0)
            self.status_label.setText(
                f"{len(videos)} videos found. Click one to play it here."
            )
        else:
            self.status_label.setText("No videos found for that search.")

    def _search_failed(self, message):
        self.status_label.setText(f"Video search failed: {message}")

    def _play_selected(self):
        item = self.results.currentItem()

        if item is None:
            self.status_label.setText("Search first, then select a video.")
            return

        video_id = item.data(Qt.ItemDataRole.UserRole)
        embed_url = (
            f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1&rel=0"
        )
        html_player = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                html, body {{
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                    background: #000;
                    overflow: hidden;
                }}
                iframe {{
                    width: 100%;
                    height: 100%;
                    border: none;
                }}
            </style>
        </head>
        <body>
            <iframe
                src="{embed_url}"
                allow="autoplay; encrypted-media; fullscreen"
                allowfullscreen>
            </iframe>
        </body>
        </html>
        """
        self.player_view.setHtml(html_player, QUrl("https://localhost"))