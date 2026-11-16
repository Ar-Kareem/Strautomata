
import sys
import random
sys.setrecursionlimit(10000)

# ----------------------------------------------------------------------
# Pre‑computed winning lines (rows, columns, two diagonals)
WINNING_LINES = [
    # rows
    [(0,0),(0,1),(0,2),(0,3)],
    [(1,0),(1,1),(1,2),(1,3)],
    [(2,0),(2,1),(2,2),(2,3)],
    [(3,0),(3,1),(3,2),(3,3)],
    # columns
    [(0,0),(1,0),(2,0),(3,0)],
    [(0,1),(1,1),(2,1),(3,1)],
    [(0,2),(1,2),(2,2),(3,2)],
    [(0,3),(1,3),(2,3),(3,3)],
    # diagonals
    [(0,0),(1,1),(2,2),(3,3)],
    [(0,3),(1,2),(2,1),(3,0)]
]

# ----------------------------------------------------------------------
def check_win(board, player):
    """Return True if `player` has a full line on the board."""
    for line in WINNING_LINES:
        if all(board[r][c] == player for r, c in line):
            return True
    return False

def get_empty_cells(board):
    """List of (row, col) tuples for empty cells."""
    empties = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empties.append((r, c))
    return empties

def evaluate(board):
    """
    Simple heuristic: +10^k for a line with k of our pieces, -10^k for a line
    with k opponent pieces. Blocked lines (both players present) are ignored.
    """
    score = 0
    for line in WINNING_LINES:
        my_cnt = opp_cnt = 0
        for r, c in line:
            v = board[r][c]
            if v == 1:
                my_cnt += 1
            elif v == -1:
                opp_cnt += 1
        # a line containing both symbols is blocked for both sides
        if my_cnt > 0 and opp_cnt > 0:
            continue
        if my_cnt:
            score += 10 ** my_cnt
        if opp_cnt:
            score -= 10 ** opp_cnt
    return score

# ----------------------------------------------------------------------
# Minimax with alpha‑beta pruning (depth‑limited)
def minimax(board, depth, alpha, beta, is_maximizing):
    # Terminal checks
    if check_win(board, 1):
        return 100000
    if check_win(board, -1):
        return -100000

    empties = get_empty_cells(board)
    if not empties or depth == 0:
        return evaluate(board)

    if is_maximizing:      # our turn (player = 1)
        max_eval = -float('inf')
        for r, c in empties:
            board[r][c] = 1
            ev = minimax(board, depth - 1, alpha, beta, False)
            board[r][c] = 0
            max_eval = max(max_eval, ev)
            alpha = max(alpha, ev)
            if beta <= alpha:
                break
        return max_eval
    else:                 # opponent's turn (player = -1)
        min_eval = float('inf')
        for r, c in empties:
            board[r][c] = -1
            ev = minimax(board, depth - 1, alpha, beta, True)
            board[r][c] = 0
            min_eval = min(min_eval, ev)
            beta = min(beta, ev)
            if beta <= alpha:
                break
        return min_eval

# ----------------------------------------------------------------------
def policy(board):
    """
    Main entry point. `board` is a 4x4 list of lists:
    0 = empty, 1 = us, -1 = opponent.
    Returns a tuple (row, col) with a legal move.
    """
    empties = get_empty_cells(board)
    if not empties:
        # Should not happen, but return a dummy value
        return (0, 0)

    # 1) Immediate win
    for r, c in empties:
        board[r][c] = 1
        if check_win(board, 1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 2) Block opponent's immediate win
    for r, c in empties:
        board[r][c] = -1
        if check_win(board, -1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 3) Use minimax (depth limited) to pick the best move
    depth = min(8, len(empties))          # deeper when fewer empty squares
    best_score = -float('inf')
    best_move = empties[0]

    # Simple move ordering: evaluate each empty cell and sort descending
    move_scores = []
    for r, c in empties:
        board[r][c] = 1
        # one‑ply heuristic as an estimate
        score = evaluate(board)
        board[r][c] = 0
        move_scores.append(((r, c), score))

    # Try moves with higher heuristic first (helps alpha‑beta)
    move_scores.sort(key=lambda x: -x[1])
    alpha = -float('inf')
    beta = float('inf')

    for (r, c), _ in move_scores:
        board[r][c] = 1
        score = minimax(board, depth - 1, alpha, beta, False)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
        alpha = max(alpha, score)

    return best_move
