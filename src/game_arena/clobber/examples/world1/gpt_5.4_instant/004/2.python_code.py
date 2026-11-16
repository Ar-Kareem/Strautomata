
from typing import List, Tuple

ROWS = 5
COLS = 6
N = ROWS * COLS

# Precompute neighbors and directions for each square.
_NEI = [[] for _ in range(N)]  # list of (to_idx, dir_char)
_DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in _DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                _NEI[i].append((j, ch))

# Center weights for mild positional preference.
_CENTER_W = []
for r in range(ROWS):
    for c in range(COLS):
        # Manhattan distance from board center (2, 2.5)
        d = abs(r - 2) + abs(c - 2.5)
        _CENTER_W.append(int(10 - 2 * d))

def _to_bitboards(you: List[List[int]], opp: List[List[int]]) -> Tuple[int, int]:
    y = 0
    o = 0
    bit = 1
    for r in range(ROWS):
        rowy = you[r]
        rowo = opp[r]
        for c in range(COLS):
            if rowy[c]:
                y |= bit
            elif rowo[c]:
                o |= bit
            bit <<= 1
    return y, o

def _moves(y: int, o: int):
    """Generate legal moves as tuples:
       (from_idx, to_idx, dir_char, new_y, new_o)
       where new_y/new_o are from next player's perspective after the move.
       Since players swap roles each ply, after moving from y vs o,
       next state is (o_without_captured, y_after_move).
    """
    res = []
    yy = y
    while yy:
        lsb = yy & -yy
        i = lsb.bit_length() - 1
        for j, ch in _NEI[i]:
            if (o >> j) & 1:
                y2 = (y ^ (1 << i)) | (1 << j)
                o2 = o ^ (1 << j)
                # Swap perspective for next player:
                res.append((i, j, ch, o2, y2))
        yy ^= lsb
    return res

def _mobility(y: int, o: int) -> int:
    cnt = 0
    yy = y
    while yy:
        lsb = yy & -yy
        i = lsb.bit_length() - 1
        for j, _ in _NEI[i]:
            cnt += (o >> j) & 1
        yy ^= lsb
    return cnt

def _piece_count(x: int) -> int:
    return x.bit_count()

def _center_score(bits: int) -> int:
    s = 0
    bb = bits
    while bb:
        lsb = bb & -bb
        i = lsb.bit_length() - 1
        s += _CENTER_W[i]
        bb ^= lsb
    return s

def _evaluate(y: int, o: int) -> int:
    mym = _mobility(y, o)
    if mym == 0:
        return -100000
    oppm = _mobility(o, y)
    if oppm == 0:
        return 100000

    myp = _piece_count(y)
    oppp = _piece_count(o)

    # Main factor is mobility difference.
    score = 120 * (mym - oppm)

    # Small piece-count preference; in Clobber fewer pieces can be okay,
    # so keep this secondary.
    score += 8 * (myp - oppp)

    # Mild center activity preference.
    score += (_center_score(y) - _center_score(o)) // 4

    # Parity-like tiebreak.
    score += (mym * 3 + myp) - (oppm * 3 + oppp)

    return score

_TT = {}

def _ordered_moves(y: int, o: int):
    ms = _moves(y, o)
    if not ms:
        return ms

    scored = []
    for mv in ms:
        _, _, _, ny, no = mv
        # Immediate win if opponent to move has no legal moves.
        opp_moves = _mobility(ny, no)
        if opp_moves == 0:
            pri = 10**9
        else:
            # Favor reducing opponent mobility and increasing our next mobility.
            my_next = _mobility(no, ny)
            pri = 1000 * (20 - opp_moves) + 50 * my_next
        scored.append((pri, mv))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in scored]

def _search(y: int, o: int, depth: int, alpha: int, beta: int) -> int:
    key = (y, o, depth, alpha, beta)
    if key in _TT:
        return _TT[key]

    ms = _ordered_moves(y, o)
    if not ms:
        return -100000 + (10 - depth)

    if depth == 0:
        val = _evaluate(y, o)
        _TT[key] = val
        return val

    best = -10**9
    for _, _, _, ny, no in ms:
        val = -_search(ny, no, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    _TT[key] = best
    return best

def policy(you: list[int], opponent: list[int]) -> str:
    y, o = _to_bitboards(you, opponent)
    legal = _moves(y, o)

    # Safety: always return a legal move string if one exists.
    # In proper arena states, there should always be at least one legal move,
    # but handle edge cases robustly.
    if not legal:
        # No legal move exists; return a syntactically valid fallback.
        # This should never be used in valid game states.
        return "0,0,R"

    # Immediate winning move check.
    for i, j, ch, ny, no in legal:
        if _mobility(ny, no) == 0:
            r, c = divmod(i, COLS)
            return f"{r},{c},{ch}"

    total_pieces = _piece_count(y) + _piece_count(o)
    num_moves = len(legal)

    # Adaptive depth for 1-second budget.
    if total_pieces <= 8:
        depth = 9
    elif total_pieces <= 12:
        depth = 8
    elif total_pieces <= 16:
        depth = 7
    elif num_moves <= 6:
        depth = 7
    else:
        depth = 6

    global _TT
    _TT = {}

    best_move = legal[0]
    best_val = -10**9
    alpha = -10**9
    beta = 10**9

    for mv in _ordered_moves(y, o):
        i, j, ch, ny, no = mv
        val = -_search(ny, no, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    i, j, ch, ny, no = best_move
    r, c = divmod(i, COLS)
    return f"{r},{c},{ch}"
