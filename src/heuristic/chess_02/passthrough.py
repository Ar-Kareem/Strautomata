from pathlib import Path
import time
from types import ModuleType
from typing import Any

from src.game_arena import utils


SUNFISH_PATH = Path(__file__).resolve().parent / "sunfish" / "sunfish.py"


def _load_sunfish_core() -> ModuleType:
    source = SUNFISH_PATH.read_text()
    cutoff = source.rfind("# minifier-hide start")
    if cutoff != -1:
        source = source[:cutoff]
    module = ModuleType("sunfish_core")
    exec(compile(source, str(SUNFISH_PATH), "exec"), module.__dict__)
    return module


_sunfish = _load_sunfish_core()

FILES = "abcdefgh"
RANKS = "12345678"
MAX_SEARCH_DEPTH = 5
TIME_CHECK_INTERVAL_NODES = 128


class _SearchTimeout(RuntimeError):
    pass


class _TimedSearcher(_sunfish.Searcher):
    def __init__(self, deadline: float):
        super().__init__()
        self.deadline = deadline

    def _check_deadline(self) -> None:
        if (
            self.nodes == 1
            or self.nodes % TIME_CHECK_INTERVAL_NODES == 0
        ) and time.perf_counter() >= self.deadline:
            raise _SearchTimeout

    def bound(self, pos, gamma, depth, can_null=True):
        self.nodes += 1
        self._check_deadline()

        depth = max(depth, 0)

        if pos.score <= -_sunfish.MATE_LOWER:
            return -_sunfish.MATE_UPPER

        entry = self.tp_score.get(
            (pos, depth, can_null),
            _sunfish.Entry(-_sunfish.MATE_UPPER, _sunfish.MATE_UPPER),
        )
        if entry.lower >= gamma:
            return entry.lower
        if entry.upper < gamma:
            return entry.upper

        if can_null and depth > 0 and pos in self.history:
            return 0

        def moves():
            if depth > 2 and can_null and abs(pos.score) < 500:
                yield None, -self.bound(pos.rotate(nullmove=True), 1 - gamma, depth - 3)

            if depth == 0:
                yield None, pos.score

            killer = self.tp_move.get(pos)

            if not killer and depth > 2:
                self.bound(pos, gamma, depth - 3, can_null=False)
                killer = self.tp_move.get(pos)

            val_lower = _sunfish.QS - depth * _sunfish.QS_A

            if killer and pos.value(killer) >= val_lower:
                yield killer, -self.bound(pos.move(killer), 1 - gamma, depth - 1)

            for val, move in sorted(((pos.value(m), m) for m in pos.gen_moves()), reverse=True):
                self._check_deadline()
                if val < val_lower:
                    break

                if depth <= 1 and pos.score + val < gamma:
                    yield move, pos.score + val if val < _sunfish.MATE_LOWER else _sunfish.MATE_UPPER
                    break

                yield move, -self.bound(pos.move(move), 1 - gamma, depth - 1)

        best = -_sunfish.MATE_UPPER
        for move, score in moves():
            best = max(best, score)
            if best >= gamma:
                if move is not None:
                    self.tp_move[pos] = move
                break

        if depth > 2 and best == -_sunfish.MATE_UPPER:
            flipped = pos.rotate(nullmove=True)
            in_check = self.bound(flipped, _sunfish.MATE_UPPER, 0) == _sunfish.MATE_UPPER
            best = -_sunfish.MATE_LOWER if in_check else 0

        if best >= gamma:
            self.tp_score[pos, depth, can_null] = _sunfish.Entry(best, entry.upper)
        if best < gamma:
            self.tp_score[pos, depth, can_null] = _sunfish.Entry(entry.lower, best)

        return best

    def search(self, history):
        self.nodes = 0
        self.history = set(history)
        self.tp_score.clear()

        gamma = 0
        for depth in range(1, MAX_SEARCH_DEPTH + 1):
            lower, upper = -_sunfish.MATE_LOWER, _sunfish.MATE_LOWER
            while lower < upper - _sunfish.EVAL_ROUGHNESS:
                self._check_deadline()
                score = self.bound(history[-1], gamma, depth, can_null=False)
                if score >= gamma:
                    lower = score
                if score < gamma:
                    upper = score
                yield depth, gamma, score, self.tp_move.get(history[-1])
                gamma = (lower + upper + 1) // 2


def _empty_board(template: str) -> list[str]:
    return ["." if c.isalpha() else c for c in template]


def _castling_rights(pieces: dict[str, str], color: str) -> tuple[bool, bool]:
    if color == "white":
        king_sq = pieces.get("e1") == "wK"
        rook_a = pieces.get("a1") == "wR"
        rook_h = pieces.get("h1") == "wR"
    else:
        king_sq = pieces.get("e8") == "bK"
        rook_a = pieces.get("a8") == "bR"
        rook_h = pieces.get("h8") == "bR"
    if not king_sq:
        return False, False
    return rook_a, rook_h


def _evaluate(board: str) -> int:
    score = 0
    for idx, piece in enumerate(board):
        if piece.isupper():
            score += _sunfish.pst[piece][idx]
        elif piece.islower():
            score -= _sunfish.pst[piece.upper()][119 - idx]
    return score


def _position_from_pieces(
    pieces: dict[str, str],
    to_play: str,
    legal_moves: list[str] | None = None,
) -> "_sunfish.Position":
    board = _empty_board(_sunfish.initial)
    for square, code in pieces.items():
        if len(code) != 2:
            continue
        color, ptype = code[0], code[1]
        char = ptype.upper() if color == "w" else ptype.lower()
        idx = _sunfish.parse(square)
        board[idx] = char

    board_str = "".join(board)
    wc = _castling_rights(pieces, "white")
    bc = _castling_rights(pieces, "black")
    if legal_moves is None:
        wc = (False, False)
        bc = (False, False)
    else:
        legal_set = set(legal_moves)
        if to_play == "white":
            wc = (
                wc[0] and ("O-O-O" in legal_set or "e1c1" in legal_set),
                wc[1] and ("O-O" in legal_set or "e1g1" in legal_set),
            )
        else:
            bc = (
                bc[0] and ("O-O-O" in legal_set or "e8c8" in legal_set),
                bc[1] and ("O-O" in legal_set or "e8g8" in legal_set),
            )
    pos = _sunfish.Position(board_str, _evaluate(board_str), wc, bc, 0, 0)
    if to_play == "black":
        pos = pos.rotate()
    return pos


def _square_to_coords(square: str) -> tuple[int, int]:
    return FILES.index(square[0]), int(square[1]) - 1


def _coords_to_square(file_idx: int, rank_idx: int) -> str:
    return f"{FILES[file_idx]}{RANKS[rank_idx]}"


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


def _can_reach(
    piece_type: str,
    src: str,
    dst: str,
    color: str,
    capture: bool,
    board: dict[str, str],
) -> bool:
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
) -> str | None:
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


def _san_to_uci(board: dict[str, str], to_play: str, san: str) -> str | None:
    parsed = _parse_san(san)
    if parsed.get("castle"):
        if to_play == "white":
            return "e1g1" if parsed["castle"] == "O-O" else "e1c1"
        return "e8g8" if parsed["castle"] == "O-O" else "e8c8"

    target = parsed["target"]
    piece_type = parsed["piece_type"]
    capture = parsed["capture"]
    disamb = parsed["disamb"]
    promotion = parsed["promotion"]
    src = _find_source_square(board, piece_type, target, disamb, capture, to_play)
    if src is None:
        return None
    uci = f"{src}{target}"
    if promotion:
        uci += promotion.lower()
    return uci


def _fallback_move(pos) -> "_sunfish.Move | None":
    best = None
    best_value = float("-inf")
    for move in pos.gen_moves():
        value = pos.value(move)
        if value > best_value:
            best = move
            best_value = value
    return best


def _move_to_uci(move, to_play: str) -> str:
    if to_play == "black":
        src = 119 - move.i
        dst = 119 - move.j
    else:
        src = move.i
        dst = move.j
    return _sunfish.render(src) + _sunfish.render(dst) + move.prom.lower()


def policy(pieces, to_play=None, legal_moves=None, move_time_limit_seconds=4.5) -> str:
    if to_play is None and legal_moves is None and isinstance(pieces, dict) and "pieces" in pieces:
        state = pieces
        pieces = state.get("pieces", {})
        to_play = state.get("to_play", "white")
        legal_moves = state.get("legal_moves")
    if to_play is None:
        to_play = "white"
    if legal_moves and len(legal_moves) == 1:
        return legal_moves[0]

    pos = _position_from_pieces(pieces, to_play, legal_moves)
    best = _fallback_move(pos)
    deadline = time.perf_counter() + move_time_limit_seconds
    searcher = _TimedSearcher(deadline)
    try:
        for _depth, gamma, score, move in searcher.search([pos]):
            if move is not None and score >= gamma:
                best = move
    except _SearchTimeout:
        pass
    if best is None:
        raise RuntimeError("Sunfish did not return a move.")

    uci = _move_to_uci(best, to_play)

    if not legal_moves:
        return uci
    if uci in legal_moves:
        return uci

    board = dict[Any, Any](pieces)
    for san in legal_moves:
        san_uci = _san_to_uci(board, to_play, san)
        if san_uci == uci:
            return san
    TEMP_LOGGER = utils.setup_logging('TEMP_LOGGER.log', 'sunfish_policy')
    TEMP_LOGGER.error(f"Unable to map Sunfish move to legal list: {uci}. Legal moves: {legal_moves}. Board: {board}. To play: {to_play}")
    return legal_moves[0]
