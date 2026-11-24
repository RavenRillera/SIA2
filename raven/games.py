from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTabWidget, QVBoxLayout, QWidget

from raven.chess_game import ChessWidget
from raven.snake import SnakeWidget
from raven.tictactoe import TicTacToeWidget
from raven.ui import make_title


class GamesWindow(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Games")
        self.resize(640, 640)

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        back = QPushButton("Back")
        back.clicked.connect(self.back_requested.emit)
        header.addWidget(make_title("Games"))
        header.addStretch(1)
        header.addWidget(back)
        layout.addLayout(header)

        self.snake = SnakeWidget()
        self.tabs = QTabWidget()
        self.tabs.addTab(TicTacToeWidget(), "Tic-Tac-Toe")
        self.tabs.addTab(ChessWidget(), "Chess")
        self.tabs.addTab(self.snake, "Snake")
        self.tabs.currentChanged.connect(lambda _index: self.snake.pause())
        layout.addWidget(self.tabs, stretch=1)

    def on_leave(self):
        self.snake.pause()