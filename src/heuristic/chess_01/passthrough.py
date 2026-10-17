import sys
from pathlib import Path

try:
    import chess
except ImportError:  # pragma: no cover - fallback for environments without python-chess
    chess = None


CHESS_AI_ROOT = Path(__file__).resolve().parent / "chess_ai"
sys.path.append(str(CHESS_AI_ROOT))

try:
    from chess_engine.chess_game import Chess_game
except Exception:
    Chess_game = None


PIECE_MAP = {
    "P": chess.PAWN if chess else None,
    "N": chess.KNIGHT if chess else None,
    "B": chess.BISHOP if chess else None,
    "R": chess.ROOK if chess else None,
    "Q": chess.QUEEN if chess else None,
    "K": chess.KING if chess else None,
}


def _board_from_pieces(pieces: dict[str, str], to_play: str, legal_moves: list[str]):
    board = chess.Board(None)
    for square, code in pieces.items():
        if len(code) != 2:
            continue
        color = chess.WHITE if code[0] == "w" else chess.BLACK
        piece_type = PIECE_MAP.get(code[1])
        if piece_type is None:
            continue
        board.set_piece_at(chess.parse_square(square), chess.Piece(piece_type, color))

    board.turn = to_play == "white"
    board.castling_rights = 0
    if legal_moves:
        if "O-O" in legal_moves:
            board.castling_rights |= chess.BB_H1 if board.turn else chess.BB_H8
        if "O-O-O" in legal_moves:
            board.castling_rights |= chess.BB_A1 if board.turn else chess.BB_A8
    return board


def policy(pieces, to_play=None, legal_moves=None) -> str:
    if to_play is None and legal_moves is None and isinstance(pieces, dict) and "pieces" in pieces:
        state = pieces
        pieces = state.get("pieces", {})
        to_play = state.get("to_play", "white")
        legal_moves = state.get("legal_moves", [])

    if not legal_moves:
        return ""
    if chess is None or Chess_game is None:
        return legal_moves[0]

    board = _board_from_pieces(pieces, to_play, legal_moves)
    engine = Chess_game(plies=2)
    engine.board = board
    engine.turn = 1 if to_play == "white" else 0
    move = engine.make_move()
    if not move:
        return legal_moves[0]

    move_san = board.san(move)
    if move_san in legal_moves:
        return move_san
    return legal_moves[0]
