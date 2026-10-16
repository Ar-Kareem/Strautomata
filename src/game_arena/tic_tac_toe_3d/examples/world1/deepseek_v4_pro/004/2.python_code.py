
import time

# ----------------------------------------------------------------------
# Precomputed winning lines in a 3x3x3 board (flat indices 0..26)
# ----------------------------------------------------------------------
def _build_lines_3d():
    lines = []
    # rows along x (i varies)
    for j in range(3):
        for k in range(3):
            lines.append(((0, j, k), (1, j, k), (2, j, k)))
    # rows along y (j varies)
    for i in range(3):
        for k in range(3):
            lines.append(((i, 0, k), (i, 1, k), (i, 2, k)))
    # rows along z (k varies)
    for i in range(3):
        for j in range(3):
            lines.append(((i, j, 0), (i, j, 1), (i, j, 2)))
    # 2D diagonals in xy-planes
    for z in range(3):
        lines.append(((0, 0, z), (1, 1, z), (2, 2, z)))
        lines.append(((0, 2, z), (1, 1, z), (2, 0, z)))
    # 2D diagonals in xz-planes
    for y in range(3):
        lines.append(((0, y, 0), (1, y, 1), (2, y, 2)))
        lines.append(((0, y, 2), (1, y, 1), (2, y, 0)))
    # 2D diagonals in yz-planes
    for x in range(3):
        lines.append(((x, 0, 0), (x, 1, 1), (x, 2, 2)))
        lines.append(((x, 0, 2), (x, 1, 1), (x, 2, 0)))
    # 4 space diagonals
    lines.append(((0, 0, 0), (1, 1, 1), (2, 2, 2)))
    lines.append(((0, 0, 2), (1, 1, 1), (2, 2, 0)))
    lines.append(((0, 2, 0), (1, 1, 1), (2, 0, 2)))
    lines.append(((2, 0, 0), (1, 1, 1), (0, 2, 2)))
    return lines

LINES_3D = _build_lines_3d()
# Flat indices: 9*i + 3*j + k
FLAT_LINES = tuple(
    tuple(9 * i + 3 * j + k for (i, j, k) in line) for line in LINES_3D
)

# Cell classification for static move ordering
CENTER = 13
CORNERS = {0, 2, 6, 8, 18, 20, 24, 26}
EDGES = {1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25}

# ----------------------------------------------------------------------
# Transposition table entry
# ----------------------------------------------------------------------
class TTEntry:
    __slots__ = ('value', 'depth', 'flag')
    def __init__(self, value, depth, flag):
        self.value = value
        self.depth = depth
        self.flag = flag  # 0 = exact, 1 = lower bound, 2 = upper bound (only exact used here)

# ----------------------------------------------------------------------
# Game logic helpers
# ----------------------------------------------------------------------
def check_winner(flat_board):
    """Return 1 if player 1 wins, -1 if opponent wins, 0 otherwise."""
    for a, b, c in FLAT_LINES:
        s = flat_board[a] + flat_board[b] + flat_board[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def is_full(flat_board):
    return all(v != 0 for v in flat_board)

def evaluate(flat_board):
    """Heuristic evaluation of a non-terminal board."""
    score = 0
    for a, b, c in FLAT_LINES:
        va, vb, vc = flat_board[a], flat_board[b], flat_board[c]
        has_us = (va == 1) or (vb == 1) or (vc == 1)
        has_opp = (va == -1) or (vb == -1) or (vc == -1)
        if has_us and has_opp:
            continue
        if has_us:
            cnt = (va == 1) + (vb == 1) + (vc == 1)
            score += 10 ** cnt
        elif has_opp:
            cnt = (va == -1) + (vb == -1) + (vc == -1)
            score -= 10 ** cnt
    return score

def order_moves(moves, flat_board, maximizing):
    """Order moves: wins > blocks > center > corners > edges."""
    static = {m: 4 if m == CENTER else (3 if m in CORNERS else 2) for m in moves}
    wins, blocks, others = [], [], []

    for m in moves:
        if maximizing:
            # immediate win for us
            tmp = list(flat_board)
            tmp[m] = 1
            if check_winner(tmp) == 1:
                wins.append(m)
                continue
            # block opponent's immediate win
            tmp[m] = -1
            if check_winner(tmp) == -1:
                blocks.append(m)
                continue
        else:
            # immediate win for opponent
            tmp = list(flat_board)
            tmp[m] = -1
            if check_winner(tmp) == -1:
                wins.append(m)
                continue
            # block our win
            tmp[m] = 1
            if check_winner(tmp) == 1:
                blocks.append(m)
                continue
        others.append(m)

    wins.sort(key=lambda x: static[x], reverse=True)
    blocks.sort(key=lambda x: static[x], reverse=True)
    others.sort(key=lambda x: static[x], reverse=True)
    return wins + blocks + others

# ----------------------------------------------------------------------
# Time management
# ----------------------------------------------------------------------
class TimeLimitExceeded(Exception):
    pass

# ----------------------------------------------------------------------
# Alpha-beta search with transposition table
# ----------------------------------------------------------------------
def alpha_beta(flat_board, depth, alpha, beta, maximizing, start_time, time_limit, tt):
    # Check time
    if time.time() - start_time > time_limit:
        raise TimeLimitExceeded()

    key = flat_board
    # TT lookup (only exact values used for simplicity)
    if key in tt:
        entry = tt[key]
        if entry.depth >= depth and entry.flag == 0:
            return entry.value

    winner = check_winner(flat_board)
    if winner != 0:
        val = winner * (depth + 1)
        tt[key] = TTEntry(val, depth, 0)
        return val
    if is_full(flat_board):
        tt[key] = TTEntry(0, depth, 0)
        return 0
    if depth == 0:
        val = evaluate(flat_board)
        tt[key] = TTEntry(val, depth, 0)
        return val

    moves = [i for i, v in enumerate(flat_board) if v == 0]
    moves = order_moves(moves, flat_board, maximizing)

    if maximizing:
        value = -float('inf')
        for move in moves:
            new_board = list(flat_board)
            new_board[move] = 1
            child = alpha_beta(tuple(new_board), depth - 1, alpha, beta,
                               False, start_time, time_limit, tt)
            if child > value:
                value = child
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        else:
            tt[key] = TTEntry(value, depth, 0)
        return value
    else:
        value = float('inf')
        for move in moves:
            new_board = list(flat_board)
            new_board[move] = -1
            child = alpha_beta(tuple(new_board), depth - 1, alpha, beta,
                               True, start_time, time_limit, tt)
            if child < value:
                value = child
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        else:
            tt[key] = TTEntry(value, depth, 0)
        return value

# ----------------------------------------------------------------------
# Main entry point: iterative deepening with time limit
# ----------------------------------------------------------------------
def get_best_move(board_3d, time_limit=0.95):
    flat_board = tuple(board_3d[i][j][k] for i in range(3) for j in range(3) for k in range(3))

    # 1. Immediate win
    for m in range(27):
        if flat_board[m] == 0:
            tmp = list(flat_board)
            tmp[m] = 1
            if check_winner(tmp) == 1:
                return m

    # 2. Immediate block
    for m in range(27):
        if flat_board[m] == 0:
            tmp = list(flat_board)
            tmp[m] = -1
            if check_winner(tmp) == -1:
                return m

    start = time.time()
    tt = {}
    best_move = None
    # fallback: first empty cell
    for i in range(27):
        if flat_board[i] == 0:
            best_move = i
            break

    try:
        for depth in range(1, 28):
            value = -float('inf')
            alpha = -float('inf')
            beta = float('inf')
            moves = [i for i, v in enumerate(flat_board) if v == 0]
            moves = order_moves(moves, flat_board, True)
            current_best = moves[0]

            for move in moves:
                new_board = list(flat_board)
                new_board[move] = 1
                child_val = alpha_beta(tuple(new_board), depth - 1, alpha, beta,
                                       False, start, time_limit, tt)
                if child_val > value:
                    value = child_val
                    current_best = move
                if value > alpha:
                    alpha = value

            best_move = current_best
            # Forced win found
            if value > 10000:
                break
    except TimeLimitExceeded:
        pass

    return best_move

# ----------------------------------------------------------------------
# Required API
# ----------------------------------------------------------------------
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """Return the next move (i, j, k) for a 3x3x3 3D Tic Tac Toe board."""
    idx = get_best_move(board)
    i = idx // 9
    j = (idx % 9) // 3
    k = idx % 3
    return (i, j, k)
