from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def result(board):
    """Return 'X' / 'O' if someone won, 'draw' if the board is full, else None."""
    for a, b, c in LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return "draw" if all(board) else None


def _minimax(board, player):
    outcome = result(board)
    if outcome == "O":
        return 1
    if outcome == "X":
        return -1
    if outcome == "draw":
        return 0
    scores = []
    for i in range(9):
        if not board[i]:
            board[i] = player
            scores.append(_minimax(board, "X" if player == "O" else "O"))
            board[i] = ""
    return max(scores) if player == "O" else min(scores)


def best_move(board):
    """Unbeatable move for 'O'."""
    best, best_score = None, -2
    for i in range(9):
        if not board[i]:
            board[i] = "O"
            score = _minimax(board, "X")
            board[i] = ""
            if score > best_score:
                best, best_score = i, score
    return best


class TicTacToeWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(["You (X) vs Computer (O)", "Two players"])
        self.mode.currentIndexChanged.connect(self.new_game)
        new_button = QPushButton("New game")
        new_button.clicked.connect(self.new_game)
        top.addWidget(self.mode, stretch=1)
        top.addWidget(new_button)
        layout.addLayout(top)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = self.status.font()
        status_font.setPointSize(14)
        self.status.setFont(status_font)
        layout.addWidget(self.status)
        layout.addStretch(1)

        grid = QGridLayout()
        self.cells = []
        for i in range(9):
            button = QPushButton("")
            button.setFixedSize(130, 130)
            font = button.font()
            font.setPointSize(44)
            button.setFont(font)
            button.clicked.connect(lambda _checked=False, index=i: self.play(index))
            grid.addWidget(button, i // 3, i % 3)
            self.cells.append(button)
        grid.setSpacing(10)
        board_row = QHBoxLayout()   # nasa gitna ang board, parisukat ang bawat kahon
        board_row.addStretch(1)
        board_row.addLayout(grid)
        board_row.addStretch(1)
        layout.addLayout(board_row)
        layout.addStretch(2)
        self.new_game()

    def new_game(self):
        self.board = [""] * 9
        self.turn = "X"
        self.over = False
        for button in self.cells:
            button.setText("")
            button.setEnabled(True)
        self.status.setText("X to move")

    def play(self, index):
        if self.over or self.board[index]:
            return
        self._place(index)
        vs_computer = self.mode.currentIndex() == 0
        if vs_computer and not self.over and self.turn == "O":
            self._place(best_move(self.board))

    def _place(self, index):
        self.board[index] = self.turn
        self.cells[index].setText(self.turn)
        self.cells[index].setEnabled(False)
        outcome = result(self.board)
        if outcome:
            self.over = True
            self.status.setText("It's a draw!" if outcome == "draw" else f"{outcome} wins!")
            return
        self.turn = "O" if self.turn == "X" else "X"
        self.status.setText(f"{self.turn} to move")