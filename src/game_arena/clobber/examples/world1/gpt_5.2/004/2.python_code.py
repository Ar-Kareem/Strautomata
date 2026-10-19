
import time
from typing import List, Tuple, Dict, Optional

# Board: 5 rows x 6 cols = 30 squares, index = r*6 + c
ROWS, COLS, N = 5, 6, 30

DIRS = {
    'U': (-1, 0),
    'R': (0, 1),
    'D': (1, 0),
    'L': (0, -1),
}

# Precompute neighbors and direction mapping.
NEIGHBORS: List[List[Tuple[int, str]]] = [[] for _ in range(N)]
SRC_DST_TO_DIR: Dict[Tuple[int, int], str] = {}

for r in range(ROWS):
    for c in range(COLS):
        s = r * COLS + c
        if r > 0:
            d = (r - 1) * COLS + c
            NEIGHBORS[s].append((d, 'U'))
            SRC_DST_TO_DIR[(s, d)] = 'U'
        if c < COLS - 1:
            d = r * COLS + (c + 1)
            NEIGHBORS[s].append((d, 'R'))
            SRC_DST_TO_DIR[(s, d)] = 'R'
        if r < ROWS - 1:
            d = (r + 1) * COLS + c
            NEIGHBORS[s].append((d, 'D'))
            SRC_DST_TO_DIR[(s, d)] = 'D'
        if c > 0:
            d = r * COLS + (c - 1)
            NEIGHBORS[s].append((d, 'L'))
            SRC_DST_TO_DIR[(s, d)] = 'L'

# Simple positional weights (center-ish squares slightly preferred)
POS_W = [0] * N
for r in range(ROWS):
    for c in range(COLS):
        # Manhattan distance to center (2, 2.5)
        dist = abs(r - 2) + abs(c - 2.5)
        # closer to center => larger
        POS_W[r * COLS + c] = int(10 - 2 * dist)  # can be negative on corners

MATE = 10_000_000

# Transposition entry: (depth, value, flag, bestmove)
# flag: 0 exact, 1 lowerbound, 2 upperbound
TT: Dict[Tuple[int, int], Tuple[int, int, int, Optional[Tuple[int, int]]]] = {}

def _flatten30(x) -> List[int]:
    """Accepts flat length-30, nested 5x6, or numpy arrays."""
    try:
        # numpy-like
        import numpy as np  # allowed
        if hasattr(x, "shape"):
            arr = np.array(x, dtype=int).reshape(-1)
            return arr.tolist()
    except Exception:
        pass

    # nested list?
    if isinstance(x, (list, tuple)) and len(x) == ROWS and isinstance(x[0], (list, tuple)):
        out = []
        for r in range(ROWS):
            out.extend(list(x[r]))
        return [int(v) for v in out]

    # assume flat
    return [int(v) for v in list(x)]

def _to_bitboard(arr30: List[int]) -> int:
    bb = 0
    for i, v in enumerate(arr30):
        if v:
            bb |= (1 << i)
    return bb

def _lsb_index(bb: int) -> int:
    return (bb & -bb).bit_length() - 1

def _gen_moves(you: int, opp: int) -> List[Tuple[int, int]]:
    """Return list of (src, dst) captures."""
    moves: List[Tuple[int, int]] = []
    y = you
    while y:
        src = _lsb_index(y)
        y &= y - 1
        for dst, _dch in NEIGHBORS[src]:
            if (opp >> dst) & 1:
                moves.append((src, dst))
    return moves

def _apply_move_swap(you: int, opp: int, mv: Tuple[int, int]) -> Tuple[int, int]:
    """Apply move for side 'you', then swap sides for next ply."""
    src, dst = mv
    you2 = (you ^ (1 << src)) | (1 << dst)
    opp2 = opp ^ (1 << dst)
    # swap: next player to move sees their pieces as 'you'
    return opp2, you2

def _eval(you: int, opp: int) -> int:
    # Mobility (captures available) is the main driver in Clobber tactics.
    my_moves = _gen_moves(you, opp)
    op_moves = _gen_moves(opp, you)
    mob = len(my_moves) - len(op_moves)

    # Material is secondary; it can mislead in zugzwang-y spots, so keep small.
    mat = you.bit_count() - opp.bit_count()

    # Small positional encouragement to keep options.
    pos = 0
    y = you
    while y:
        i = _lsb_index(y)
        y &= y - 1
        pos += POS_W[i]
    o = opp
    while o:
        i = _lsb_index(o)
        o &= o - 1
        pos -= POS_W[i]

    return 30 * mob + 3 * mat + pos

class _Search:
    __slots__ = ("t_end", "stop", "nodes")

    def __init__(self, t_end: float):
        self.t_end = t_end
        self.stop = False
        self.nodes = 0

    def _time_up(self) -> bool:
        if time.perf_counter() >= self.t_end:
            self.stop = True
        return self.stop

    def negamax(self, you: int, opp: int, depth: int, alpha: int, beta: int, ply: int) -> Tuple[int, Optional[Tuple[int, int]]]:
        if self._time_up():
            return _eval(you, opp), None

        self.nodes += 1

        moves = _gen_moves(you, opp)
        if not moves:
            # No legal moves => lose immediately
            return -MATE + ply, None

        if depth <= 0:
            return _eval(you, opp), None

        key = (you, opp)
        tt = TT.get(key)
        if tt is not None:
            tt_depth, tt_val, tt_flag, tt_bm = tt
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_val, tt_bm
                elif tt_flag == 1:  # lower
                    alpha = max(alpha, tt_val)
                else:  # upper
                    beta = min(beta, tt_val)
                if alpha >= beta:
                    return tt_val, tt_bm

        # Move ordering:
        # 1) try TT best move first
        # 2) otherwise prefer moves that leave opponent (next player) with fewer replies
        ordered: List[Tuple[int, int]] = []
        if tt is not None and tt[3] is not None and tt[3] in moves:
            ordered.append(tt[3])
            for m in moves:
                if m != tt[3]:
                    ordered.append(m)
        else:
            # score each move by next-side mobility (lower is better for us)
            scored = []
            for m in moves:
                ny, no = _apply_move_swap(you, opp, m)
                # next player mobility:
                nm = len(_gen_moves(ny, no))
                scored.append((nm, m))
            scored.sort(key=lambda x: x[0])
            ordered = [m for _nm, m in scored]

        best_val = -MATE
        best_move: Optional[Tuple[int, int]] = None
        a0 = alpha

        for m in ordered:
            if self._time_up():
                break
            ny, no = _apply_move_swap(you, opp, m)
            val, _ = self.negamax(ny, no, depth - 1, -beta, -alpha, ply + 1)
            val = -val
            if val > best_val:
                best_val = val
                best_move = m
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        # Store TT entry
        if not self.stop:
            flag = 0
            if best_val <= a0:
                flag = 2  # upper
            elif best_val >= beta:
                flag = 1  # lower
            TT[key] = (depth, best_val, flag, best_move)

        return best_val, best_move

def policy(you: List[int], opponent: List[int]) -> str:
    y_arr = _flatten30(you)
    o_arr = _flatten30(opponent)
    you_bb = _to_bitboard(y_arr)
    opp_bb = _to_bitboard(o_arr)

    legal = _gen_moves(you_bb, opp_bb)
    if not legal:
        # Terminal: no legal move exists. Arena typically won't call policy here,
        # but return a syntactically valid placeholder.
        return "0,0,U"

    # Always keep a legal fallback
    fallback = legal[0]

    # Time management
    t0 = time.perf_counter()
    t_end = t0 + 0.95  # ~1s limit with safety
    search = _Search(t_end)

    best = fallback
    best_val = -MATE

    # Iterative deepening
    # Depths tuned for 30-square board under 1s.
    for depth in range(1, 30):
        if time.perf_counter() >= t_end:
            break
        val, mv = search.negamax(you_bb, opp_bb, depth, -MATE, MATE, 0)
        if search.stop:
            break
        if mv is not None:
            best = mv
            best_val = val
        # If we found a forced win line early, can stop.
        if best_val > MATE // 2:
            break

    src, dst = best
    r, c = divmod(src, COLS)
    dch = SRC_DST_TO_DIR.get((src, dst), 'U')
    return f"{r},{c},{dch}"
