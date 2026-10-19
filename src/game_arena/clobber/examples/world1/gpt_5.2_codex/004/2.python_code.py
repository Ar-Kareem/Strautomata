
import time
from typing import List, Tuple

# Board constants
ROWS, COLS = 5, 6
SIZE = ROWS * COLS

# Precompute neighbors for each cell
NEIGHBORS = [[] for _ in range(SIZE)]
DIRS = [('U', -1, 0), ('D', 1, 0), ('L', 0, -1), ('R', 0, 1)]
for r in range(ROWS):
    for c in range(COLS):
        idx = r * COLS + c
        for dch, dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                nidx = nr * COLS + nc
                NEIGHBORS[idx].append((nidx, dch))

def to_bitboard(arr) -> int:
    """Convert input array to bitboard integer."""
    # Handle flat or 2D arrays (list or numpy)
    if hasattr(arr, '__len__') and len(arr) == SIZE:
        # flat
        bits = 0
        for i in range(SIZE):
            if arr[i]:
                bits |= (1 << i)
        return bits
    else:
        bits = 0
        for r in range(ROWS):
            for c in range(COLS):
                if arr[r][c]:
                    bits |= (1 << (r * COLS + c))
        return bits

def gen_moves(you: int, opp: int) -> List[Tuple[int,int,str]]:
    """Generate all legal moves."""
    moves = []
    pieces = you
    while pieces:
        lsb = pieces & -pieces
        idx = lsb.bit_length() - 1
        pieces ^= lsb
        for nidx, dch in NEIGHBORS[idx]:
            if (opp >> nidx) & 1:
                moves.append((idx, nidx, dch))
    return moves

def apply_move(you: int, opp: int, move: Tuple[int,int,str]) -> Tuple[int,int]:
    src, dst, _ = move
    you2 = (you & ~(1 << src)) | (1 << dst)
    opp2 = opp & ~(1 << dst)
    return you2, opp2

def evaluate(you: int, opp: int) -> int:
    """Heuristic evaluation."""
    my_moves = len(gen_moves(you, opp))
    opp_moves = len(gen_moves(opp, you))
    my_count = you.bit_count()
    opp_count = opp.bit_count()
    return 2 * (my_moves - opp_moves) + (my_count - opp_count)

# Transposition table
TT = {}

def negamax(you: int, opp: int, depth: int, alpha: int, beta: int, start_time: float, limit: float) -> int:
    if time.time() - start_time > limit:
        return evaluate(you, opp)

    key = (you, opp, depth)
    if key in TT:
        return TT[key]

    moves = gen_moves(you, opp)
    if not moves:
        return -10000 - depth  # lose
    if depth == 0:
        return evaluate(you, opp)

    best = -10**9
    # Simple move ordering: prefer moves that reduce opponent mobility
    scored_moves = []
    for m in moves:
        y2, o2 = apply_move(you, opp, m)
        scored_moves.append((len(gen_moves(o2, y2)), m))
    scored_moves.sort(key=lambda x: x[0])  # fewer opp moves first

    for _, m in scored_moves:
        y2, o2 = apply_move(you, opp, m)
        val = -negamax(o2, y2, depth-1, -beta, -alpha, start_time, limit)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = best
    return best

def policy(you: List[int], opponent: List[int]) -> str:
    start_time = time.time()
    time_limit = 0.95  # seconds

    you_bits = to_bitboard(you)
    opp_bits = to_bitboard(opponent)

    moves = gen_moves(you_bits, opp_bits)
    if not moves:
        # Should not happen in normal play, but return something
        return "0,0,U"

    best_move = moves[0]
    best_val = -10**9

    max_depth = 6
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > time_limit:
            break

        # order moves for this depth
        scored_moves = []
        for m in moves:
            y2, o2 = apply_move(you_bits, opp_bits, m)
            scored_moves.append((len(gen_moves(o2, y2)), m))
        scored_moves.sort(key=lambda x: x[0])

        for _, m in scored_moves:
            if time.time() - start_time > time_limit:
                break
            y2, o2 = apply_move(you_bits, opp_bits, m)
            val = -negamax(o2, y2, depth-1, -10**9, 10**9, start_time, time_limit)
            if val > best_val:
                best_val = val
                best_move = m

    src, _, dch = best_move
    r, c = divmod(src, COLS)
    return f"{r},{c},{dch}"
