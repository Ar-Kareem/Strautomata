import importlib.util
import os
from typing import Optional


FILES = "abcdefgh"
RANKS = "12345678"


def _load_piece_values():
    base = os.path.join(os.path.dirname(__file__), "chess_ai", "chess_engine", "piece_values.py")
    spec = importlib.util.spec_from_file_location("piece_values", base)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_piece_values_module = _load_piece_values()
if _piece_values_module is not None:
    PIECE_VALUES = _piece_values_module.individual_piece_values
    PST = {
        "P": _piece_values_module.pawntable,
        "N": _piece_values_module.knightstable,
        "B": _piece_values_module.bishopstable,
        "R": _piece_values_module.rookstable,
        "Q": _piece_values_module.queenstable,
        "K": _piece_values_module.kingstable,
    }
else:
    PIECE_VALUES = {"p": 100, "n": 300, "b": 300, "r": 500, "q": 900, "k": 100000}
    PST = {k: [0] * 64 for k in "PNBRQK"}


def _square_to_coords(square: str) -> tuple[int, int]:
    return FILES.index(square[0]), int(square[1]) - 1


def _coords_to_square(file_idx: int, rank_idx: int) -> str:
    return f"{FILES[file_idx]}{RANKS[rank_idx]}"


def _square_to_index(square: str) -> int:
    file_idx, rank_idx = _square_to_coords(square)
    return rank_idx * 8 + file_idx


def _mirror_index(index: int) -> int:
    rank_idx = index // 8
    file_idx = index % 8
    return (7 - rank_idx) * 8 + file_idx


def _path_clear(src: str, dst: str, occupied: set[str]) -> bool:
    sf, sr = _square_to_coords(src)
    tf, tr = _square_to_coords(dst)
    df = tf - sf
    dr = tr - sr
    step_f = (df > 0) - (df < 0)
    step_r = (dr > 0) - (dr < 0)
    cf, cr = sf + step_f, sr + step_r
    while (cf, cr) != (tf, tr):
        if _coords_to_square(cf, cr) in occupied:
            return False
        cf += step_f
        cr += step_r
    return True


def _disamb_matches(disamb: str, square: str) -> bool:
    if not disamb:
        return True
    for ch in disamb:
        if ch in FILES and square[0] != ch:
            return False
        if ch in RANKS and square[1] != ch:
            return False
    return True


def _can_reach(piece_type: str, src: str, dst: str, color: str, capture: bool, board: dict[str, str]) -> bool:
    sf, sr = _square_to_coords(src)
    tf, tr = _square_to_coords(dst)
    df = tf - sf
    dr = tr - sr
    occupied = set(board.keys())

    if piece_type == "P":
        direction = 1 if color == "w" else -1
        if capture:
            return abs(df) == 1 and dr == direction
        if df != 0:
            return False
        if dr == direction:
            return dst not in occupied
        if dr == 2 * direction and ((sr == 1 and color == "w") or (sr == 6 and color == "b")):
            intermediate = _coords_to_square(sf, sr + direction)
            return intermediate not in occupied and dst not in occupied
        return False

    if piece_type == "N":
        return (abs(df), abs(dr)) in ((1, 2), (2, 1))

    if piece_type == "K":
        return max(abs(df), abs(dr)) == 1

    if piece_type == "B":
        if abs(df) != abs(dr):
            return False
        return _path_clear(src, dst, occupied)

    if piece_type == "R":
        if df != 0 and dr != 0:
            return False
        return _path_clear(src, dst, occupied)

    if piece_type == "Q":
        if abs(df) != abs(dr) and df != 0 and dr != 0:
            return False
        return _path_clear(src, dst, occupied)

    return False


def _find_source_square(
    board: dict[str, str],
    piece_type: str,
    target: str,
    disamb: str,
    capture: bool,
    to_play: str,
) -> Optional[str]:
    color = "w" if to_play == "white" else "b"
    candidates = []
    for square, code in board.items():
        if code != color + piece_type:
            continue
        if not _disamb_matches(disamb, square):
            continue
        if _can_reach(piece_type, square, target, color, capture, board):
            candidates.append(square)
    if candidates:
        return candidates[0]
    return None


def _sanitize_san(move: str) -> str:
    move = move.replace("0-0-0", "O-O-O").replace("0-0", "O-O")
    while move and move[-1] in "+#!?":
        move = move[:-1]
    return move


def _parse_san(move: str) -> dict:
    clean = _sanitize_san(move)
    if clean in ("O-O", "O-O-O"):
        return {"castle": clean}

    promotion = None
    if "=" in clean:
        clean, promo = clean.split("=", 1)
        promotion = promo[0]

    piece_type = "P"
    if clean and clean[0] in "KQRBN":
        piece_type = clean[0]
        rest = clean[1:]
    else:
        rest = clean

    target = rest[-2:]
    before_target = rest[:-2]
    capture = "x" in before_target

    if piece_type == "P":
        disamb = before_target[0] if capture and before_target else ""
    else:
        disamb = before_target.replace("x", "")

    return {
        "castle": None,
        "piece_type": piece_type,
        "target": target,
        "capture": capture,
        "disamb": disamb,
        "promotion": promotion,
    }


def _apply_castle(board: dict[str, str], to_play: str, side: str) -> dict[str, str]:
    color = "w" if to_play == "white" else "b"
    new_board = dict(board)
    if color == "w":
        king_src = "e1"
        if side == "O-O":
            rook_src, king_dst, rook_dst = "h1", "g1", "f1"
        else:
            rook_src, king_dst, rook_dst = "a1", "c1", "d1"
    else:
        king_src = "e8"
        if side == "O-O":
            rook_src, king_dst, rook_dst = "h8", "g8", "f8"
        else:
            rook_src, king_dst, rook_dst = "a8", "c8", "d8"

    new_board.pop(king_src, None)
    new_board.pop(rook_src, None)
    new_board[king_dst] = color + "K"
    new_board[rook_dst] = color + "R"
    return new_board


def _apply_move(
    board: dict[str, str],
    src: str,
    dst: str,
    piece_type: str,
    promotion: Optional[str],
    capture: bool,
    to_play: str,
) -> dict[str, str]:
    color = "w" if to_play == "white" else "b"
    new_board = dict(board)
    new_board.pop(src, None)

    if dst in new_board:
        new_board.pop(dst, None)
    elif piece_type == "P" and capture:
        sf, sr = _square_to_coords(src)
        tf, tr = _square_to_coords(dst)
        if sf != tf:
            behind_rank = tr - (1 if color == "w" else -1)
            if 0 <= behind_rank < 8:
                behind_sq = _coords_to_square(tf, behind_rank)
                if new_board.get(behind_sq) == ("b" if color == "w" else "w") + "P":
                    new_board.pop(behind_sq, None)

    placed_type = promotion if promotion else piece_type
    new_board[dst] = color + placed_type
    return new_board


def _evaluate_board(board: dict[str, str]) -> int:
    score = 0
    for square, code in board.items():
        if not code or len(code) != 2:
            continue
        color = code[0]
        piece_type = code[1]
        sign = 1 if color == "b" else -1
        score += PIECE_VALUES.get(piece_type.lower(), 0) * sign
        pst = PST.get(piece_type)
        if pst:
            idx = _square_to_index(square)
            if color == "b":
                idx = _mirror_index(idx)
            score += pst[idx] * sign
    return score


def _is_uci_move(move: str) -> bool:
    return (
        isinstance(move, str)
        and len(move) in (4, 5)
        and move[0] in FILES
        and move[1] in RANKS
        and move[2] in FILES
        and move[3] in RANKS
        and (len(move) == 4 or move[4] in "qrbnQRBN")
    )


def _apply_uci_move(board: dict[str, str], move: str, to_play: str) -> dict[str, str]:
    src, dst = move[:2], move[2:4]
    promo = move[4].upper() if len(move) == 5 else None
    color = "w" if to_play == "white" else "b"
    opp = "b" if color == "w" else "w"
    new_board = dict(board)
    piece = new_board.pop(src, None)
    if piece is None:
        return new_board
    piece_type = piece[1]

    if piece_type == "K" and src[0] == "e" and dst in ("g1", "c1", "g8", "c8"):
        if dst[0] == "g":
            rook_src, rook_dst = ("h1", "f1") if color == "w" else ("h8", "f8")
        else:
            rook_src, rook_dst = ("a1", "d1") if color == "w" else ("a8", "d8")
        rook = new_board.pop(rook_src, None)
        if rook is not None:
            new_board[rook_dst] = rook

    if piece_type == "P" and src[0] != dst[0] and dst not in new_board:
        tf, tr = _square_to_coords(dst)
        capture_sq = _coords_to_square(tf, tr - (1 if color == "w" else -1))
        if new_board.get(capture_sq) == opp + "P":
            new_board.pop(capture_sq, None)

    new_board.pop(dst, None)
    new_board[dst] = color + (promo if promo else piece_type)
    return new_board


def policy(
    pieces,
    to_play: Optional[str] = None,
    legal_moves: Optional[list[str]] = None,
) -> str:
    if to_play is None and legal_moves is None and isinstance(pieces, dict) and "pieces" in pieces:
        state = pieces
        pieces = state.get("pieces", {})
        to_play = state.get("to_play", "white")
        legal_moves = state.get("legal_moves")
    if to_play is None:
        to_play = "white"

    if not legal_moves:
        return ""

    board = dict(pieces)
    best_move = legal_moves[0]
    best_score = None
    uci_mode = all(_is_uci_move(m) for m in legal_moves)

    for move in legal_moves:
        if uci_mode:
            new_board = _apply_uci_move(board, move, to_play)
        else:
            parsed = _parse_san(move)
            if parsed.get("castle"):
                new_board = _apply_castle(board, to_play, parsed["castle"])
            else:
                target = parsed["target"]
                piece_type = parsed["piece_type"]
                capture = parsed["capture"]
                disamb = parsed["disamb"]
                promotion = parsed["promotion"]
                src = _find_source_square(board, piece_type, target, disamb, capture, to_play)
                if src is None:
                    continue
                new_board = _apply_move(board, src, target, piece_type, promotion, capture, to_play)

        score = _evaluate_board(new_board)
        if to_play == "white":
            score = -score

        if move.endswith("#"):
            score += 1000000
        elif move.endswith("+"):
            score += 50

        if best_score is None or score > best_score:
            best_score = score
            best_move = move

    return best_move
