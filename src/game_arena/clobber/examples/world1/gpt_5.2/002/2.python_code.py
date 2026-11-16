
import time
from typing import List, Tuple, Optional, Dict

# 5x6 board => 30 squares, row-major index = r*6 + c
ROWS, COLS = 5, 6
N = ROWS * COLS
BOARD_MASK = (1 << N) - 1

# Column masks for wrap-safe shifting
COL0_MASK = sum(1 << (r * COLS + 0) for r in range(ROWS))
COL5_MASK = sum(1 << (r * COLS + (COLS - 1)) for r in range(ROWS))
NOT_COL0 = BOARD_MASK ^ COL0_MASK
NOT_COL5 = BOARD_MASK ^ COL5_MASK

# Mate-like scores
MATE = 10**9


def _to_flat_list(a) -> List[int]:
    """Accepts flat list, 2D list, or numpy-like arrays; returns flat length-30 list."""
    # numpy arrays
    if hasattr(a, "shape") and hasattr(a, "flatten"):
        return [int(x) for x in a.flatten().tolist()]
    # 2D python list
    if isinstance(a, (list, tuple)) and len(a) == ROWS and isinstance(a[0], (list, tuple)):
        out = []
        for r in range(ROWS):
            row = a[r]
            for c in range(COLS):
                out.append(int(row[c]))
        return out
    # flat
    return [int(x) for x in a]


def _list_to_bitboard(flat: List[int]) -> int:
    b = 0
    # Expect length N; if not, be defensive and use min length
    m = min(len(flat), N)
    for i in range(m):
        if flat[i]:
            b |= (1 << i)
    return b


def _count_moves(me: int, opp: int) -> int:
    """Counts legal captures for side 'me' against 'opp'."""
    # Up: origin i captures i-6 => destination d = i-6
    up = (me >> 6) & opp
    # Down
    down = ((me << 6) & BOARD_MASK) & opp
    # Left (avoid col0 origins)
    left = ((me & NOT_COL0) >> 1) & opp
    # Right (avoid col5 origins)
    right = ((me & NOT_COL5) << 1) & opp
    return (up | down | left | right).bit_count()


def _iter_set_bits(x: int):
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        yield idx
        x ^= lsb


def _generate_moves(me: int, opp: int) -> List[Tuple[int, int, str]]:
    """
    Returns list of moves as (from_idx, to_idx, dir_char).
    dir_char is direction of movement from origin to destination.
    """
    moves: List[Tuple[int, int, str]] = []

    # Up: destination squares that contain opp and have our piece below
    dests = (me >> 6) & opp
    for d in _iter_set_bits(dests):
        moves.append((d + 6, d, "U"))

    # Down
    dests = ((me << 6) & BOARD_MASK) & opp
    for d in _iter_set_bits(dests):
        moves.append((d - 6, d, "D"))

    # Left
    dests = ((me & NOT_COL0) >> 1) & opp
    for d in _iter_set_bits(dests):
        moves.append((d + 1, d, "L"))

    # Right
    dests = ((me & NOT_COL5) << 1) & opp
    for d in _iter_set_bits(dests):
        moves.append((d - 1, d, "R"))

    return moves


def _apply_move(me: int, opp: int, frm: int, to: int) -> Tuple[int, int]:
    """Applies capture move for 'me' from frm to to (to occupied by opp). Returns (new_me, new_opp)."""
    fmask = 1 << frm
    tmask = 1 << to
    new_me = (me ^ fmask) | tmask
    new_opp = opp ^ tmask
    return new_me, new_opp


def _evaluate(me: int, opp: int) -> int:
    """Heuristic evaluation for the side to move (me). Higher is better for 'me'."""
    my_moves = _count_moves(me, opp)
    if my_moves == 0:
        return -MATE  # should be terminal anyway

    opp_moves = _count_moves(opp, me)
    # Mobility is the main signal; material is a small tie-break.
    material = (me.bit_count() - opp.bit_count())
    return 15 * (my_moves - opp_moves) + 2 * material


class _Search:
    def __init__(self, deadline: float):
        self.deadline = deadline
        # Transposition table: (me, opp) -> (depth, value)
        self.tt: Dict[Tuple[int, int], Tuple[int, int]] = {}

    def _time_up(self) -> bool:
        return time.perf_counter() >= self.deadline

    def negamax(self, me: int, opp: int, depth: int, alpha: int, beta: int, ply: int) -> int:
        if self._time_up():
            raise TimeoutError

        key = (me, opp)
        hit = self.tt.get(key)
        if hit is not None:
            hit_depth, hit_val = hit
            if hit_depth >= depth:
                return hit_val

        moves = _generate_moves(me, opp)
        if not moves:
            # No legal moves => lose now. Prefer quicker wins / slower losses.
            return -MATE + ply

        if depth == 0:
            val = _evaluate(me, opp)
            self.tt[key] = (depth, val)
            return val

        # Simple move ordering:
        # prioritize moves that immediately leave opponent with no moves,
        # otherwise fewer opponent replies is better.
        ordered = []
        for frm, to, dch in moves:
            nme, nopp = _apply_move(me, opp, frm, to)
            # After our move, opponent to play with (nopp vs nme)
            opp_reply_count = _count_moves(nopp, nme)
            win_now = 1 if opp_reply_count == 0 else 0
            ordered.append((win_now, -opp_reply_count, frm, to, dch))
        ordered.sort(reverse=True)

        best = -MATE
        a = alpha
        for win_now, _, frm, to, dch in ordered:
            nme, nopp = _apply_move(me, opp, frm, to)
            # swap roles for opponent's turn
            val = -self.negamax(nopp, nme, depth - 1, -beta, -a, ply + 1)
            if val > best:
                best = val
            if best > a:
                a = best
            if a >= beta:
                break

        self.tt[key] = (depth, best)
        return best

    def search_root(self, me: int, opp: int, depth: int) -> Tuple[int, Tuple[int, int, str]]:
        moves = _generate_moves(me, opp)
        if not moves:
            # No legal move exists; game-losing state. Arena should not ask here,
            # but we must still return something. We'll just return a dummy;
            # note: may be illegal if truly no moves.
            return -MATE, (0, 0, "U")

        # Pre-order root moves similarly
        scored = []
        for frm, to, dch in moves:
            nme, nopp = _apply_move(me, opp, frm, to)
            opp_reply_count = _count_moves(nopp, nme)
            win_now = 1 if opp_reply_count == 0 else 0
            scored.append((win_now, -opp_reply_count, frm, to, dch))
        scored.sort(reverse=True)

        best_val = -MATE
        best_move = (scored[0][2], scored[0][3], scored[0][4])

        alpha, beta = -MATE, MATE
        a = alpha
        for win_now, _, frm, to, dch in scored:
            if self._time_up():
                raise TimeoutError
            nme, nopp = _apply_move(me, opp, frm, to)
            val = -self.negamax(nopp, nme, depth - 1, -beta, -a, 1)
            if val > best_val:
                best_val = val
                best_move = (frm, to, dch)
            if best_val > a:
                a = best_val
        return best_val, best_move


def policy(you: list[int], opponent: list[int]) -> str:
    # Convert input to bitboards
    y_flat = _to_flat_list(you)
    o_flat = _to_flat_list(opponent)
    me = _list_to_bitboard(y_flat)
    opp = _list_to_bitboard(o_flat)

    # Ensure we always return a legal move if one exists
    legal = _generate_moves(me, opp)
    if not legal:
        # No legal moves: losing position. Return a syntactically valid move string anyway.
        # (Arena typically won't call policy in terminal states.)
        return "0,0,U"

    # Time budget (keep margin for Python overhead)
    start = time.perf_counter()
    deadline = start + 0.93

    searcher = _Search(deadline=deadline)

    # Default: first legal move
    best_move = legal[0]

    # Iterative deepening
    depth = 1
    while True:
        try:
            _, mv = searcher.search_root(me, opp, depth)
            best_move = mv
            depth += 1
            if depth > 20:  # hard cap
                break
        except TimeoutError:
            break

    frm, to, dch = best_move
    r, c = divmod(frm, COLS)
    return f"{r},{c},{dch}"
