
import numpy as np

# Directions for queen-like movement
DIRS = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1)
]

INF = 10**9

def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def reachable(board, start):
    """All reachable empty squares from start with queen-like moves."""
    r0, c0 = start
    for dr, dc in DIRS:
        r, c = r0 + dr, c0 + dc
        while in_bounds(r, c) and board[r, c] == 0:
            yield (r, c)
            r += dr
            c += dc

def get_moves(board, player):
    """Generate all legal moves for player."""
    moves = []
    positions = np.argwhere(board == player)
    for r, c in positions:
        for to in reachable(board, (r, c)):
            # simulate move
            b2 = board.copy()
            b2[r, c] = 0
            b2[to[0], to[1]] = player
            for arrow in reachable(b2, to):
                moves.append(((r, c), to, arrow))
    return moves

def apply_move(board, move, player):
    b = board.copy()
    (fr, fc), (tr, tc), (ar, ac) = move
    b[fr, fc] = 0
    b[tr, tc] = player
    b[ar, ac] = -1
    return b

def mobility(board, player):
    total = 0
    positions = np.argwhere(board == player)
    for r, c in positions:
        total += sum(1 for _ in reachable(board, (r, c)))
    return total

def evaluate(board):
    return mobility(board, 1) - mobility(board, 2)

def minimax(board, depth, maximizing, alpha, beta):
    player = 1 if maximizing else 2
    moves = get_moves(board, player)
    if not moves:
        return -INF if maximizing else INF
    if depth == 0:
        return evaluate(board)

    if maximizing:
        best = -INF
        for mv in moves:
            b2 = apply_move(board, mv, player)
            val = minimax(b2, depth - 1, False, alpha, beta)
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = INF
        for mv in moves:
            b2 = apply_move(board, mv, player)
            val = minimax(b2, depth - 1, True, alpha, beta)
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def move_to_str(move):
    (fr, fc), (tr, tc), (ar, ac) = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

def policy(board) -> str:
    board = np.array(board)
    moves = get_moves(board, 1)
    if not moves:
        # Should not happen, but return a dummy string if no legal move
        return "0,0:0,0:0,0"

    # Adjust depth based on branching factor
    depth = 3 if len(moves) <= 40 else 2

    best_val = -INF
    best_move = moves[0]

    for mv in moves:
        b2 = apply_move(board, mv, 1)
        # Immediate win
        if not get_moves(b2, 2):
            return move_to_str(mv)
        val = minimax(b2, depth - 1, False, -INF, INF)
        if val > best_val:
            best_val = val
            best_move = mv

    return move_to_str(best_move)
