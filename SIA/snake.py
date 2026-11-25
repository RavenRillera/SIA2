import random

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

CELL, COLS, ROWS = 22, 24, 18
KEYS = {
    Qt.Key.Key_Up: (0, -1), Qt.Key.Key_W: (0, -1),
    Qt.Key.Key_Down: (0, 1), Qt.Key.Key_S: (0, 1),
    Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_A: (-1, 0),
    Qt.Key.Key_Right: (1, 0), Qt.Key.Key_D: (1, 0),
}


class SnakeBoard(QWidget):
    message = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedSize(COLS * CELL, ROWS * CELL)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.reset()

    def reset(self):
        self.timer.stop()
        self.snake = [(12, 9), (11, 9), (10, 9)]
        self.direction = self.pending = (1, 0)
        self.score = 0
        self.alive = True
        self.food = self._new_food()
        self.update()

    def start(self):
        self.reset()
        self.timer.start(110)
        self.setFocus()
        self.message.emit("Score: 0 — arrows/WASD to move, Space to pause")

    def pause(self):
        if self.timer.isActive():
            self.timer.stop()
            self.message.emit(f"Paused — score {self.score}. Press Space to resume")

    def _new_food(self):
        free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in self.snake]
        return random.choice(free)

    def _tick(self):
        self.direction = self.pending
        head = (self.snake[0][0] + self.direction[0], self.snake[0][1] + self.direction[1])
        if not (0 <= head[0] < COLS and 0 <= head[1] < ROWS) or head in self.snake:
            self.timer.stop()
            self.alive = False
            self.message.emit(f"Game over — score {self.score}. Press Start to play again")
            self.update()
            return
        self.snake.insert(0, head)
        if head == self.food:
            self.score += 1
            self.food = self._new_food()
            self.message.emit(f"Score: {self.score}")
        else:
            self.snake.pop()
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space and self.alive:
            if self.timer.isActive():
                self.pause()
            else:
                self.timer.start(110)
            return
        new = KEYS.get(event.key())
        if new and (new[0] != -self.direction[0] or new[1] != -self.direction[1]):
            self.pending = new
        else:
            super().keyPressEvent(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#e04040"))
        painter.drawEllipse(QRectF(self.food[0] * CELL + 3, self.food[1] * CELL + 3, CELL - 6, CELL - 6))
        for i, (x, y) in enumerate(self.snake):
            painter.setBrush(QColor("#7fd35a") if i == 0 else QColor("#3fa34d"))
            painter.drawRoundedRect(QRectF(x * CELL + 1, y * CELL + 1, CELL - 2, CELL - 2), 5, 5)


class SnakeWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.status = QLabel("Press Start")
        start = QPushButton("Start")
        row.addWidget(self.status, stretch=1)
        row.addWidget(start)
        layout.addLayout(row)
        self.board = SnakeBoard()
        self.board.message.connect(self.status.setText)
        start.clicked.connect(self.board.start)
        layout.addWidget(self.board, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

    def pause(self):
        self.board.pause()