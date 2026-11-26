import sys
from functools import lru_cache

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# --------------------------------------------------------------------------
# Game logic (no Qt here, so it can be tested on its own)
# --------------------------------------------------------------------------

LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]

MOVE_ORDER = [4, 0, 2, 6, 8, 1, 3, 5, 7]  # centre, corners, edges


def other(player):
    return "O" if player == "X" else "X"


def result(board):
    """Return (outcome, winning_line).

    outcome is "X", "O", "draw" or None (game still running).
    winning_line is a tuple of 3 indices, or () if there is no winner.
    """
    for line in LINES:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], line

    if all(board):
        return "draw", ()

    return None, ()


@lru_cache(maxsize=None)
def _minimax(board, player, ai_symbol):
    """Score a position from the computer's point of view.

    `board` is a tuple so results can be cached. Wins found earlier score
    higher; this depends only on the number of empty squares, which keeps
    the score a pure function of the position (and therefore cacheable).
    The whole game tree is only ~5,500 distinct positions, so after the
    first call every lookup is instant.
    """
    outcome, _ = result(board)
    empties = board.count("")

    if outcome == ai_symbol:
        return 1 + empties
    if outcome == "draw":
        return 0
    if outcome:
        return -(1 + empties)

    scores = [
        _minimax(
            board[:i] + (player,) + board[i + 1:],
            other(player),
            ai_symbol,
        )
        for i in MOVE_ORDER
        if not board[i]
    ]

    return max(scores) if player == ai_symbol else min(scores)


def best_move(board, ai_symbol="O"):
    """Perfect play: pick the strongest move for the computer."""
    state = tuple(board)
    best, best_score = None, float("-inf")

    for i in MOVE_ORDER:
        if not state[i]:
            nxt = state[:i] + (ai_symbol,) + state[i + 1:]
            score = _minimax(nxt, other(ai_symbol), ai_symbol)
            if score > best_score:
                best, best_score = i, score

    return best


def choose_move(board, ai_symbol):
    """Pick the computer's move (always the strongest one)."""
    if all(board):
        return None

    return best_move(board, ai_symbol)


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------

# Dark palette to match the host "Games" window
TEXT = "#E6F1F5"
MUTED = "#7F98A5"
PANEL = "#0D2533"
BORDER = "#1F4054"
ACCENT = "#22D3EE"
X_COLOR = "#22D3EE"
O_COLOR = "#F5A623"
WIN_BG = "#12394A"
AI_DELAY_MS = 400
NEXT_ROUND_MS = 1500


def cell_style(color=TEXT, background=PANEL, border=BORDER):
    return f"""
        QPushButton#gameCell {{
            background-color: {background};
            color: {color};
            border: 2px solid {border};
            border-radius: 12px;
            font-weight: bold;
        }}
        QPushButton#gameCell:hover:enabled {{
            border-color: {ACCENT};
        }}
    """


class BoardView(QWidget):
    """3x3 grid that stays square, centred, and scales with the window."""

    cellClicked = Signal(int)

    def __init__(self):
        super().__init__()
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.setMinimumHeight(150)

        self.holder = QWidget(self)
        grid = QGridLayout(self.holder)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        self.cells = []
        for i in range(9):
            button = QPushButton("")
            button.setObjectName("gameCell")
            button.setMinimumSize(36, 36)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, index=i: self.cellClicked.emit(index)
            )
            grid.addWidget(button, i // 3, i % 3)
            self.cells.append(button)

    def resizeEvent(self, event):
        side = max(0, min(self.width(), self.height()))
        self.holder.setGeometry(
            (self.width() - side) // 2,
            (self.height() - side) // 2,
            side,
            side,
        )

        font = QFont()
        font.setBold(True)
        font.setPixelSize(max(14, int(side / 3 * 0.5)))
        for cell in self.cells:
            cell.setFont(font)

        super().resizeEvent(event)


class TicTacToeWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("ticTacToeWidget")

        self.scores = {"X": 0, "O": 0, "draw": 0}
        self.board = [""] * 9
        self.turn = "X"
        self.over = False

        # The computer "thinks" briefly so moves don't feel instant
        self.ai_timer = QTimer(self)
        self.ai_timer.setSingleShot(True)
        self.ai_timer.setInterval(AI_DELAY_MS)
        self.ai_timer.timeout.connect(self.computer_turn)

        # With no New Game button, the next round starts by itself
        self.next_timer = QTimer(self)
        self.next_timer.setSingleShot(True)
        self.next_timer.setInterval(NEXT_ROUND_MS)
        self.next_timer.timeout.connect(self.new_game)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 12)
        layout.setSpacing(10)

        title = QLabel("TIC TAC TOE")
        title.setObjectName("gameTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Settings (single row)
        settings = QHBoxLayout()
        settings.setSpacing(8)

        self.mode = QComboBox()
        self.mode.addItems(["You vs Computer", "Two Players"])

        self.symbol = QComboBox()
        self.symbol.addItems(["X", "O"])

        self.play_label = QLabel("Play as")

        settings.addWidget(self.mode, 3)
        settings.addWidget(self.play_label)
        settings.addWidget(self.symbol, 2)
        layout.addLayout(settings)

        # Changing a setting changes what the scoreboard means,
        # so it restarts the scores as well as the board.
        for combo in (self.mode, self.symbol):
            combo.currentIndexChanged.connect(self.reset_scores)

        # Buttons (single row)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        self.reset_button = QPushButton("Reset Scores")
        self.reset_button.setObjectName("resetButton")
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.clicked.connect(self.reset_scores)

        buttons.addWidget(self.reset_button)
        layout.addLayout(buttons)

        # Scoreboard
        scoreboard = QHBoxLayout()
        self.name_labels = {}
        self.score_labels = {}

        for key in ("X", "O", "draw"):
            card = QVBoxLayout()
            card.setSpacing(0)

            name_label = QLabel()
            name_label.setObjectName("scoreName")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            score_label = QLabel("0")
            score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            score_label.setObjectName("scoreNumber")

            self.name_labels[key] = name_label
            self.score_labels[key] = score_label

            card.addWidget(name_label)
            card.addWidget(score_label)
            scoreboard.addLayout(card)

        layout.addLayout(scoreboard)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setObjectName("gameStatus")
        layout.addWidget(self.status)

        # Board takes all remaining space and stays square
        self.board_view = BoardView()
        self.board_view.cellClicked.connect(self.play)
        self.cells = self.board_view.cells
        layout.addWidget(self.board_view, 1)

        self.setStyleSheet(self._stylesheet())

        self.reset_scores()

    # ---- helpers ---------------------------------------------------------

    @property
    def vs_computer(self):
        return self.mode.currentIndex() == 0

    def _stylesheet(self):
        return f"""
            QLabel {{ color: {TEXT}; }}
            QLabel#gameTitle {{
                font-size: 22px; font-weight: bold;
                letter-spacing: 3px; color: {TEXT};
            }}
            QLabel#scoreName {{
                font-size: 11px; letter-spacing: 2px; color: {MUTED};
            }}
            QLabel#scoreNumber {{
                font-size: 22px; font-weight: bold; color: {ACCENT};
            }}
            QLabel#gameStatus {{
                background-color: {PANEL}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 8px; font-size: 14px; font-weight: bold;
            }}
            QComboBox {{
                background-color: {PANEL}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 7px;
                padding: 4px 8px; min-height: 22px;
            }}
            QComboBox:hover {{ border-color: {ACCENT}; }}
            QComboBox:disabled {{ color: {MUTED}; }}
            QComboBox QAbstractItemView {{
                background-color: {PANEL}; color: {TEXT};
                selection-background-color: {BORDER};
                selection-color: {TEXT};
            }}
            QPushButton#resetButton {{
                background-color: transparent; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 7px; font-weight: bold;
            }}
            QPushButton#resetButton:hover {{ border-color: {ACCENT}; }}
            {cell_style()}
        """

    def refresh_names(self):
        """Label the scoreboard with who is X and who is O."""
        human = self.symbol.currentText()
        if self.vs_computer:
            names = {
                human: f"YOU ({human})",
                other(human): f"COMPUTER ({other(human)})",
            }
        else:
            names = {
                human: f"PLAYER 1 ({human})",
                other(human): f"PLAYER 2 ({other(human)})",
            }

        for key, text in names.items():
            self.name_labels[key].setText(text)
        self.name_labels["draw"].setText("DRAWS")

    def update_scoreboard(self):
        for key, label in self.score_labels.items():
            label.setText(str(self.scores[key]))

    def player_name(self, symbol):
        if not self.vs_computer:
            return "Player 1" if symbol == self.human_symbol else "Player 2"
        return "You" if symbol == self.human_symbol else "Computer"

    # ---- game flow -------------------------------------------------------

    def reset_scores(self):
        self.scores = {"X": 0, "O": 0, "draw": 0}
        self.update_scoreboard()
        self.new_game()

    def new_game(self):
        """Start a new round."""
        self.ai_timer.stop()  # cancel any pending computer move
        self.next_timer.stop()  # cancel any pending auto-restart

        self.board = [""] * 9
        self.over = False

        self.human_symbol = self.symbol.currentText()
        self.computer_symbol = other(self.human_symbol)

        # vs Computer: X always goes first.
        # Two Players: Player 1 (the chosen symbol) goes first.
        self.turn = "X" if self.vs_computer else self.human_symbol

        self.symbol.setEnabled(True)
        self.play_label.setText("Play as" if self.vs_computer else "Player 1")
        self.refresh_names()

        for button in self.cells:
            button.setText("")
            button.setEnabled(True)
            button.setStyleSheet("")

        # The computer opens if the human chose O
        if self.vs_computer and self.turn == self.computer_symbol:
            self.start_computer_turn()
        else:
            self.update_status()

    def update_status(self):
        if self.vs_computer:
            self.status.setText(f"Your turn ({self.human_symbol})")
        else:
            n = 1 if self.turn == self.human_symbol else 2
            self.status.setText(f"Player {n}'s turn ({self.turn})")

    def play(self, index):
        """Handle a click on a cell."""
        if self.over or self.board[index]:
            return

        # Ignore clicks while it is the computer's turn
        if self.vs_computer and self.turn != self.human_symbol:
            return

        self._place(index)

    def start_computer_turn(self):
        self.status.setText("Computer is thinking...")
        self.ai_timer.start()

    def computer_turn(self):
        if (
            self.over
            or not self.vs_computer
            or self.turn != self.computer_symbol
        ):
            return

        index = choose_move(self.board, self.computer_symbol)

        if index is not None:
            self._place(index)

    def _place(self, index):
        """Place the current player's symbol and advance the game."""
        player = self.turn
        self.board[index] = player

        color = X_COLOR if player == "X" else O_COLOR
        button = self.cells[index]
        button.setText(player)
        button.setEnabled(False)
        button.setStyleSheet(cell_style(color, PANEL, color))

        outcome, line = result(self.board)

        if outcome:
            self.finish(outcome, line)
            return

        self.turn = other(self.turn)

        if self.vs_computer and self.turn == self.computer_symbol:
            self.start_computer_turn()
        else:
            self.update_status()

    def finish(self, outcome, line):
        self.over = True
        self.scores[outcome] += 1
        self.update_scoreboard()

        if outcome == "draw":
            self.status.setText("It's a draw!")
        else:
            who = self.player_name(outcome)
            verb = "win" if who == "You" else "wins"
            self.status.setText(f"{who} {verb}!")

            # Highlight the winning line
            color = X_COLOR if outcome == "X" else O_COLOR
            for i in line:
                self.cells[i].setStyleSheet(cell_style(color, WIN_BG, color))

        for cell in self.cells:
            cell.setEnabled(False)

        self.next_timer.start()  # start the next round automatically


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TicTacToeWidget()
    window.setWindowTitle("Tic Tac Toe")
    window.resize(520, 640)
    window.setStyleSheet(f"QWidget#ticTacToeWidget {{ background: #06141D; }}" + window.styleSheet())
    window.show()
    sys.exit(app.exec())