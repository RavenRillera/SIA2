import chess
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QInputDialog, QLabel, QPushButton, QVBoxLayout, QWidget

LIGHT, DARK = QColor("#f0d9b5"), QColor("#b58863")
PROMOTIONS = {"Queen": chess.QUEEN, "Rook": chess.ROOK, "Bishop": chess.BISHOP, "Knight": chess.KNIGHT}


class ChessBoard(QWidget):
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.board = chess.Board()
        self.selected = None
        self.targets = set()
        self.setMinimumSize(400, 400)
        self.font_ = QFont()
        self.font_.setFamilies(["Segoe UI Symbol", "Apple Symbols", "DejaVu Sans", "Noto Sans Symbols2"])

    # ----- geometry -----
    def _metrics(self):
        size = min(self.width(), self.height()) // 8
        return size, (self.width() - size * 8) // 2, (self.height() - size * 8) // 2

    def _square_at(self, pos):
        size, ox, oy = self._metrics()
        file_, row = (pos.x() - ox) // size, (pos.y() - oy) // size
        if 0 <= file_ < 8 and 0 <= row < 8:
            return chess.square(int(file_), 7 - int(row))
        return None

    # ----- input -----
    def mousePressEvent(self, event):
        square = self._square_at(event.position().toPoint())
        if square is None or self.board.is_game_over():
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

    # ----- game control -----
    def new_game(self):
        self.board = chess.Board()
        self.selected, self.targets = None, set()
        self.status_changed.emit(self.status_text())
        self.update()

    def undo(self):
        if self.board.move_stack:
            self.board.pop()
            self.selected, self.targets = None, set()
            self.status_changed.emit(self.status_text())
            self.update()

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
            rect = QRectF(ox + file_ * size, oy + (7 - rank) * size, size, size)
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
        row = QHBoxLayout()
        self.status = QLabel("White to move")
        new_button, undo_button = QPushButton("New game"), QPushButton("Undo")
        row.addWidget(self.status, stretch=1)
        row.addWidget(undo_button)
        row.addWidget(new_button)
        layout.addLayout(row)
        self.board = ChessBoard()
        self.board.status_changed.connect(self.status.setText)
        new_button.clicked.connect(self.board.new_game)
        undo_button.clicked.connect(self.board.undo)
        layout.addWidget(self.board, stretch=1)