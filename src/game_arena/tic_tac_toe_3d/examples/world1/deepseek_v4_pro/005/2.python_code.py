
import time

# ---------- Precomputation of winning lines and masks ----------
WIN_LINES = []

# Rows along x (y, z fixed)
for y in range(3):
    for z in range(3):
        WIN_LINES.append(tuple(x*9 + y*3 + z for x in range(3)))
# Rows along y (x, z fixed)
for x in range(3):
    for z in range(3):
        WIN_LINES.append(tuple(x*9 + y*3 + z for y in range(3)))
# Rows along z (x, y fixed)
for x in range(3):
    for y in range(3):
        WIN_LINES.append(tuple(x*9 + y*3 + z for z in range(3)))
# Face diagonals on x-planes
for x in range(3):
    WIN_LINES.append(tuple(x*9 + i*3 + i for i in range(3)))
    WIN_LINES.append(tuple(x*9 + i*3 + (2-i) for i in range(3)))
# Face diagonals on y-planes
for y in range(3):
    WIN_LINES.append(tuple(i*9 + y*3 + i for i in range(3)))
    WIN_LINES.append(tuple(i*9 + y*3 + (2-i) for i in range(3)))
# Face diagonals on z-planes
for z in range(3):
    WIN_LINES.append(tuple(i*9 + i*3 + z for i in range(3)))
    WIN_LINES.append(tuple(i*9 + (2-i)*3 + z for i in range(3)))
# Body diagonals
WIN_LINES.append(tuple(i*9 + i*3 + i for i in range(3)))
WIN_LINES.append(tuple(i*9 + i*3 + (2-i) for i in range(3)))
WIN_LINES.append(tuple(i*9 + (2-i)*3 + i for i in range(3)))
WIN_LINES.append(tuple((2-i)*9 + i*3 + i for i in range(3)))

LINE_MASKS = []
for line in WIN_LINES:
    mask = 0
    for idx in line:
        mask |= 1 << idx
    LINE_MASKS.append(mask)

# Static weights for move ordering (number of winning lines through each cell)
CELL_WEIGHTS = [0] * 27
for line in WIN_LINES:
    for idx in line:
        CELL_WEIGHTS[idx] += 1

FULL_MASK = (1 << 27) - 1

# Fast popcount using a byte lookup table
POPCOUNT_8 = [bin(i).count('1') for i in range(256)]
def popcount(x: int) -> int:
    return (POPCOUNT_8[x & 0xFF] + POPCOUNT_8[(x >> 8) & 0xFF] +
            POPCOUNT_8[(x >> 16) & 0xFF] + POPCOUNT_8[(x >> 24) & 0xFF])

# Custom timeout exception
class Timeout(Exception):
    pass

# Global timing variables
start_time = 0.0
TIME_LIMIT = 0.95
nodes = 0

def check_win(bb: int) -> bool:
    """Return True if the bitboard bb contains a winning line."""
    for mask in LINE_MASKS:
        if (bb & mask) == mask:
            return True
    return False

def evaluate(my: int, opp: int) -> int:
    """Heuristic evaluation of the board.
    my: bitboard of our pieces (1)
    opp: bitboard of opponent pieces (-1)
    """
    score = 0
    for mask in LINE_MASKS:
        my_count = popcount(my & mask)
        opp_count = popcount(opp & mask)
        if my_count > 0 and opp_count > 0:
            continue  # line is blocked
        if my_count == 3:
            return 10000
        if opp_count == 3:
            return -10000
        if my_count == 2:
            score += 10
        elif my_count == 1:
            score += 1
        if opp_count == 2:
            score -= 10
        elif opp_count == 1:
            score -= 1
    return score

def get_moves(empty: int) -> list:
    """Return list of empty cell indices sorted by static weight (best first)."""
    moves = []
    e = empty
    while e:
        lsb = e & -e
        idx = lsb.bit_length() - 1
        moves.append(idx)
        e ^= lsb
    moves.sort(key=lambda i: CELL_WEIGHTS[i], reverse=True)
    return moves

def alphabeta(my: int, opp: int, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """Alpha-beta pruning search."""
    global nodes, start_time
    nodes += 1
    if nodes % 5000 == 0:
        if time.time() - start_time > TIME_LIMIT:
            raise Timeout()

    if check_win(my):
        return 10000 + depth  # prefer faster win
    if check_win(opp):
        return -10000 - depth
    if depth == 0:
        return evaluate(my, opp)

    empty = FULL_MASK & ~(my | opp)
    if empty == 0:
        return 0  # draw

    moves = get_moves(empty)
    if maximizing:
        best = -float('inf')
        for move in moves:
            new_my = my | (1 << move)
            val = alphabeta(new_my, opp, depth - 1, alpha, beta, False)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = float('inf')
        for move in moves:
            new_opp = opp | (1 << move)
            val = alphabeta(my, new_opp, depth - 1, alpha, beta, True)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """Return the next move as (i, j, k) for a 3x3x3 3D Tic Tac Toe board."""
    global start_time, nodes
    # Convert board to bitboards (1 -> our pieces, -1 -> opponent pieces)
    my = 0
    opp = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                val = board[i][j][k]
                idx = i * 9 + j * 3 + k
                if val == 1:
                    my |= 1 << idx
                elif val == -1:
                    opp |= 1 << idx

    empty = FULL_MASK & ~(my | opp)
    if empty == 0:  # should never happen
        return (0, 0, 0)

    moves = get_moves(empty)

    # 1. Immediate win
    for move in moves:
        if check_win(my | (1 << move)):
            return (move // 9, (move // 3) % 3, move % 3)

    # 2. Iterative deepening search with time limit
    start_time = time.time()
    nodes = 0
    best_move = None
    depth = 1
    max_depth = popcount(empty)

    try:
        while depth <= max_depth:
            best_val = -float('inf')
            alpha = -float('inf')
            beta = float('inf')
            best_move_at_depth = None
            for move in moves:
                new_my = my | (1 << move)
                val = alphabeta(new_my, opp, depth - 1, alpha, beta, False)
                if val > best_val:
                    best_val = val
                    best_move_at_depth = move
                if best_val > alpha:
                    alpha = best_val
                if alpha >= beta:
                    break
            best_move = best_move_at_depth
            if best_val >= 10000 or depth == max_depth:
                break
            depth += 1
    except Timeout:
        pass  # use the best move found so far

    if best_move is None:
        best_move = moves[0]  # fallback to the statically best move

    i = best_move // 9
    j = (best_move // 3) % 3
    k = best_move % 3
    return (i, j, k)
