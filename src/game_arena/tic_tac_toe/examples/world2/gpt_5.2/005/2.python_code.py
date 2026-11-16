
import time
from typing import List, Tuple, Dict

# 4x4 Tic Tac Toe (4 in a row wins)
N = 4
FULL_MASK = (1 << (N * N)) - 1
MATE = 10_000_000

# Precompute win masks (4 rows, 4 cols, 2 diags)
WIN_MASKS = []
# Rows
for r in range(N):
    m = 0
    for c in range(N):
        m |= 1 << (r * N + c)
    WIN_MASKS.append(m)
# Cols
for c in range(N):
    m = 0
    for r in range(N):
        m |= 1 << (r * N + c)
    WIN_MASKS.append(m)
# Diagonals
d1 = 0
d2 = 0
for i in range(N):
    d1 |= 1 << (i * N + i)
    d2 |= 1 << (i * N + (N - 1 - i))
WIN_MASKS.append(d1)
WIN_MASKS.append(d2)

# Positional weights: prefer central control (important on 4x4)
# Layout indices:
#  0  1  2  3
#  4  5  6  7
#  8  9 10 11
# 12 13 14 15
POS_W = [
    3, 2, 2, 3,
    2, 4, 4, 2,
    2, 4, 4, 2,
    3, 2, 2, 3,
]

# Line potential weights for heuristic (unblocked line with k stones)
LINE_W = [0, 2, 12, 80, 2000]  # index = count in line (0..4)


def _win(bits: int) -> bool:
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False


def _iter_empty_squares(pbits: int, obits: int):
    empties = (~(pbits | obits)) & FULL_MASK
    while empties:
        lsb = empties & -empties
        idx = (lsb.bit_length() - 1)
        yield idx
        empties ^= lsb


def _board_to_bits(board: List[List[int]]) -> Tuple[int, int]:
    pbits = 0
    obits = 0
    for r in range(N):
        row = board[r]
        for c in range(N):
            v = row[c]
            idx = r * N + c
            if v == 1:
                pbits |= 1 << idx
            elif v == -1:
                obits |= 1 << idx
    return pbits, obits


def _heuristic(cur: int, other: int) -> int:
    # If someone has already won, return a huge value
    if _win(cur):
        return MATE
    if _win(other):
        return -MATE

    score = 0

    # Positional weights
    cb = cur
    while cb:
        lsb = cb & -cb
        idx = lsb.bit_length() - 1
        score += POS_W[idx]
        cb ^= lsb

    ob = other
    while ob:
        lsb = ob & -ob
        idx = lsb.bit_length() - 1
        score -= POS_W[idx]
        ob ^= lsb

    # Line potential
    for m in WIN_MASKS:
        c = (cur & m).bit_count()
        o = (other & m).bit_count()
        if c and o:
            continue  # blocked
        if c:
            score += LINE_W[c]
        elif o:
            score -= LINE_W[o]

    return score


class _Timeout(Exception):
    pass


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Returns a legal move (row, col) for player '1' given a 4x4 board with:
    0 = empty, 1 = us, -1 = opponent.
    """
    pbits, obits = _board_to_bits(board)

    # Collect legal moves (indices) early; ensure we always return something legal.
    legal = list(_iter_empty_squares(pbits, obits))
    if not legal:
        # No legal moves; should not happen in normal play.
        return (0, 0)

    # Immediate tactical checks: win now, or block opponent win now.
    for idx in legal:
        if _win(pbits | (1 << idx)):
            return divmod(idx, N)

    for idx in legal:
        if _win(obits | (1 << idx)):
            return divmod(idx, N)

    deadline = time.perf_counter() + 0.95  # time budget

    # Transposition table: (cur_bits, other_bits, depth) -> value
    # Using depth in key keeps correctness for depth-limited search.
    tt: Dict[Tuple[int, int, int], int] = {}

    def ordered_moves(cur: int, other: int):
        # Strong move ordering improves alpha-beta:
        # 1) immediate wins
        # 2) immediate blocks
        # 3) otherwise sort by a shallow heuristic after the move
        moves = list(_iter_empty_squares(cur, other))
        wins = []
        blocks = []
        rest = []
        for idx in moves:
            bit = 1 << idx
            if _win(cur | bit):
                wins.append(idx)
            elif _win(other | bit):  # placing here blocks their immediate win
                blocks.append(idx)
            else:
                # quick move ordering score: heuristic after move (with role swap)
                # current plays idx, then opponent to move
                h = _heuristic(other, cur | bit)  # from next player's perspective
                rest.append((h, idx))
        rest.sort()  # lower h is better for current (since it hurts the next player)
        return wins + blocks + [idx for _, idx in rest]

    def negamax(cur: int, other: int, depth: int, alpha: int, beta: int) -> int:
        if time.perf_counter() > deadline:
            raise _Timeout

        # Terminal checks
        if _win(cur):
            return MATE + depth  # prefer quicker win (bigger is better)
        if _win(other):
            return -MATE - depth  # prefer delaying loss
        if depth == 0:
            return _heuristic(cur, other)

        key = (cur, other, depth)
        if key in tt:
            return tt[key]

        # If board full, draw-ish
        if ((cur | other) & FULL_MASK) == FULL_MASK:
            val = _heuristic(cur, other)
            tt[key] = val
            return val

        best = -MATE * 2
        for idx in ordered_moves(cur, other):
            bit = 1 << idx
            # Play move, swap roles
            val = -negamax(other, cur | bit, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[key] = best
        return best

    def search_root(depth: int) -> Tuple[int, int]:
        best_idx = legal[0]
        best_val = -MATE * 2
        alpha = -MATE * 2
        beta = MATE * 2

        for idx in ordered_moves(pbits, obits):
            if ((pbits | obits) >> idx) & 1:
                continue  # not legal (shouldn't happen)
            bit = 1 << idx
            val = -negamax(obits, pbits | bit, depth - 1, -beta, -alpha)
            if val > best_val:
                best_val = val
                best_idx = idx
            if best_val > alpha:
                alpha = best_val
        return divmod(best_idx, N)

    # Iterative deepening: keep best completed depth.
    best_move = divmod(legal[0], N)
    try:
        # Max depth is remaining moves; cap to 16.
        remaining = 16 - (pbits | obits).bit_count()
        max_depth = max(1, min(16, remaining))
        for d in range(1, max_depth + 1):
            best_move = search_root(d)
    except _Timeout:
        pass

    # Ensure the move is legal; if not (extremely unlikely), fall back.
    r, c = best_move
    if 0 <= r < 4 and 0 <= c < 4 and board[r][c] == 0:
        return best_move

    # Fallback: first legal
    idx = legal[0]
    return divmod(idx, N)
