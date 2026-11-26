import random

import chess
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

LIGHT, DARK = QColor("#f0d9b5"), QColor("#b58863")
PROMOTIONS = {"Queen": chess.QUEEN, "Rook": chess.ROOK, "Bishop": chess.BISHOP, "Knight": chess.KNIGHT}

AI_DELAY_MS = 400
AI_DEPTH = 3

# --------------------------------------------------------------------------
# Computer opponent (no Qt here): simple negamax with alpha-beta pruning
# --------------------------------------------------------------------------

VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}
MATE = 100000


def evaluate(board):
    """Score the position from the point of view of the side to move."""
    score = 0
    for square, piece in board.piece_map().items():
        value = VALUES[piece.piece_type]
        file_, rank = chess.square_file(square), chess.square_rank(square)

        if piece.piece_type in (chess.PAWN, chess.KNIGHT, chess.BISHOP):
            # small bonus for central squares
            centre = 3.5 - max(abs(file_ - 3.5), abs(rank - 3.5))
            value += centre * 6
        if piece.piece_type == chess.PAWN:
            # small bonus for advanced pawns
            progress = rank if piece.color == chess.WHITE else 7 - rank
            value += progress * 5

        score += value if piece.color == board.turn else -value
    return score


def _ordered_moves(board):
    """Captures and promotions first, so pruning works better."""

    def key(move):
        score = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            victim_value = VALUES[victim.piece_type] if victim else VALUES[chess.PAWN]
            attacker_value = VALUES[board.piece_at(move.from_square).piece_type]
            score += 10 * victim_value - attacker_value
        if move.promotion:
            score += VALUES[move.promotion]
        return -score

    return sorted(board.legal_moves, key=key)


def _negamax(board, depth, alpha, beta):
    moves = _ordered_moves(board)
    if not moves:
        return -(MATE + depth) if board.is_check() else 0
    if depth == 0:
        return evaluate(board)

    best = float("-inf")
    for move in moves:
        board.push(move)
        score = -_negamax(board, depth - 1, -beta, -alpha)
        board.pop()
        if score > best:
            best = score
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best


def best_move(board, depth=AI_DEPTH):
    """Pick a good move for the side to move (random among equal best)."""
    best_score = float("-inf")
    best_moves = []
    alpha = float("-inf")

    for move in _ordered_moves(board):
        board.push(move)
        score = -_negamax(board, depth - 1, float("-inf"), -alpha + 1)
        board.pop()

        if score > best_score:
            best_score, best_moves = score, [move]
        elif score == best_score:
            best_moves.append(move)
        alpha = max(alpha, best_score)

    return random.choice(best_moves) if best_moves else None


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------


class ChessBoard(QWidget):
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.board = chess.Board()
        self.selected = None
        self.targets = set()

        self.vs_computer = True
        self.human_color = chess.WHITE
        self.flipped = False  # False = White at the bottom, True = Black at the bottom

        # The computer "thinks" briefly so moves don't feel instant
        self.ai_timer = QTimer(self)
        self.ai_timer.setSingleShot(True)
        self.ai_timer.setInterval(AI_DELAY_MS)
        self.ai_timer.timeout.connect(self._computer_move)

        self.setMinimumSize(400, 400)
        self.font_ = QFont()
        self.font_.setFamilies(["Segoe UI Symbol", "Apple Symbols", "DejaVu Sans", "Noto Sans Symbols2"])

    # ----- geometry -----
    def _metrics(self):
        size = min(self.width(), self.height()) // 8
        return size, (self.width() - size * 8) // 2, (self.height() - size * 8) // 2

    def _square_at(self, pos):
        size, ox, oy = self._metrics()
        col, row = (pos.x() - ox) // size, (pos.y() - oy) // size
        if 0 <= col < 8 and 0 <= row < 8:
            col, row = int(col), int(row)
            if self.flipped:
                return chess.square(7 - col, row)
            return chess.square(col, 7 - row)
        return None

    def _screen_cell(self, square):
        """Return (column, row) on screen for a chess square."""
        file_, rank = chess.square_file(square), chess.square_rank(square)
        if self.flipped:
            return 7 - file_, rank
        return file_, 7 - rank

    # ----- input -----
    def _human_can_move(self):
        if self.board.is_game_over():
            return False
        if self.vs_computer and self.board.turn != self.human_color:
            return False  # computer's turn
        return True

    def mousePressEvent(self, event):
        if not self._human_can_move():
            return
        square = self._square_at(event.position().toPoint())
        if square is None:
            return
        if self.selected is not None and square in self.targets:
            self._move(self.selected, square)
        else:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected = square
                self.targets = {m.to_square for m in self.board.legal_moves if m.from_square == square}
            else:
                self.selected, self.targets = None, set()
        self.update()

    def _move(self, start, end):
        move = chess.Move(start, end)
        piece = self.board.piece_at(start)
        if piece.piece_type == chess.PAWN and chess.square_rank(end) in (0, 7):
            choice, ok = QInputDialog.getItem(self, "Promotion", "Promote to:", list(PROMOTIONS), 0, False)
            move.promotion = PROMOTIONS[choice] if ok else chess.QUEEN
        self.board.push(move)
        self.selected, self.targets = None, set()
        self.status_changed.emit(self.status_text())
        self._maybe_start_computer()

    # ----- computer -----
    def _maybe_start_computer(self):
        if self.vs_computer and not self.board.is_game_over() and self.board.turn != self.human_color:
            self.status_changed.emit("Computer is thinking...")
            self.ai_timer.start()

    def _computer_move(self):
        if not self.vs_computer or self.board.is_game_over() or self.board.turn == self.human_color:
            return
        move = best_move(self.board)
        if move is not None:
            self.board.push(move)
        self.status_changed.emit(self.status_text())
        self.update()

    # ----- game control -----
    def set_side(self, color):
        """Choose which colour you play (and which sits at the bottom)."""
        self.human_color = color
        self.flipped = color == chess.BLACK
        self.new_game()

    def set_vs_computer(self, flag):
        self.vs_computer = flag
        self.new_game()

    def new_game(self):
        self.ai_timer.stop()  # cancel any pending computer move
        self.board = chess.Board()
        self.selected, self.targets = None, set()
        self.status_changed.emit(self.status_text())
        self.update()
        self._maybe_start_computer()  # computer opens if you chose Black

    def undo(self):
        self.ai_timer.stop()
        if not self.board.move_stack:
            return
        self.board.pop()
        if self.vs_computer:
            # go back to the human's turn
            while self.board.move_stack and self.board.turn != self.human_color:
                self.board.pop()
        self.selected, self.targets = None, set()
        self.status_changed.emit(self.status_text())
        self.update()
        self._maybe_start_computer()

    def status_text(self):
        b = self.board
        if b.is_checkmate():
            return f"Checkmate — {'Black' if b.turn else 'White'} wins"
        if b.is_stalemate():
            return "Stalemate — draw"
        if b.is_game_over():
            return "Draw"
        text = f"{'White' if b.turn else 'Black'} to move"
        return text + " — check!" if b.is_check() else text

    # ----- drawing -----
    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size, ox, oy = self._metrics()
        check_square = self.board.king(self.board.turn) if self.board.is_check() else None

        for square in chess.SQUARES:
            file_, rank = chess.square_file(square), chess.square_rank(square)
            col, row = self._screen_cell(square)
            rect = QRectF(ox + col * size, oy + row * size, size, size)
            painter.fillRect(rect, LIGHT if (file_ + rank) % 2 else DARK)
            if square == check_square:
                painter.fillRect(rect, QColor(220, 50, 50, 140))
            if square == self.selected:
                painter.fillRect(rect, QColor(246, 246, 105, 170))
            piece = self.board.piece_at(square)
            if piece:
                self._draw_piece(painter, rect, piece)
            if square in self.targets:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(20, 120, 20, 150))
                radius = size * (0.42 if piece else 0.15)
                if piece:  # capture: ring
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.setPen(QPen(QColor(20, 120, 20, 180), size * 0.07))
                painter.drawEllipse(rect.center(), radius, radius)

    def _draw_piece(self, painter, rect, piece):
        font = QFont(self.font_)
        font.setPixelSize(int(rect.width() * 0.8))
        glyph = chess.Piece(piece.piece_type, chess.BLACK).unicode_symbol()  # solid glyph for both sides
        path = QPainterPath()
        path.addText(0, 0, font, glyph)
        bounds = path.boundingRect()
        path.translate(rect.center().x() - bounds.center().x(), rect.center().y() - bounds.center().y())
        white = piece.color == chess.WHITE
        painter.setPen(QPen(QColor("#222"), 1.6))
        painter.setBrush(QColor("#fafafa") if white else QColor("#1c1c1c"))
        painter.drawPath(path)


class ChessWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Settings row
        settings = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(["You vs Computer", "Two Players"])
        self.side = QComboBox()
        self.side.addItems(["White", "Black"])
        settings.addWidget(self.mode, 2)
        settings.addWidget(QLabel("Play as"))
        settings.addWidget(self.side, 1)
        layout.addLayout(settings)

        # Status + buttons row
        row = QHBoxLayout()
        self.status = QLabel("White to move")
        new_button, undo_button = QPushButton("New game"), QPushButton("Undo")
        row.addWidget(self.status, stretch=1)
        row.addWidget(undo_button)
        row.addWidget(new_button)
        layout.addLayout(row)

        self.board = ChessBoard()
        self.board.status_changed.connect(self.status.setText)
        self.mode.currentIndexChanged.connect(lambda i: self.board.set_vs_computer(i == 0))
        self.side.currentIndexChanged.connect(self.change_side)
        new_button.clicked.connect(self.board.new_game)
        undo_button.clicked.connect(self.board.undo)
        layout.addWidget(self.board, stretch=1)

    def change_side(self, index):
        self.board.set_side(chess.WHITE if index == 0 else chess.BLACK)