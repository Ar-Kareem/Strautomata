
import sys

sys.setrecursionlimit(10000)

# Winning lines – rows, columns, main diagonal and anti‑diagonal (4 cells each)
WINNING_LINES = [
    [(i, 0), (i, 1), (i, 2), (i, 3)] for i in range(4)
] + [
    [(0, j), (1, j), (2, j), (3, j)] for j in range(4)
] + [
    [(0, 0), (1, 1), (2, 2), (3, 3)],
    [(0, 3), (1, 2), (2, 1), (3, 0)]
]

# Caches – (board_state, turn) -> best_score for that position
# turn = True  → maximizer (our turn)
# turn = False → minimizer (opponent's turn)
_caches = {}

def _state(board):
    """Convert mutable board to an immutable hashable key."""
    return tuple(tuple(row) for row in board)

def evaluate(board):
    """Return 1 if we win, -1 if opponent wins, 0 otherwise."""
    for line in WINNING_LINES:
        if all(board[i][j] == 1 for i, j in line):
            return 1
        if all(board[i][j] == -1 for i, j in line):
            return -1
    return 0

def find_win(board):
    """Return all empty cells that complete a four‑in‑a‑row for us."""
    wins = []
    for line in WINNING_LINES:
        vals = [board[i][j] for i, j in line]
        if vals.count(1) == 3 and vals.count(0) == 1:
            for i, j in line:
                if board[i][j] == 0:
                    wins.append((i, j))
                    break
    return wins

def opponent_threats(board):
    """Return all empty cells that would give opponent an immediate win."""
    threats = []
    for line in WINNING_LINES:
        vals = [board[i][j] for i, j in line]
        if vals.count(-1) == 3 and vals.count(0) == 1:
            for i, j in line:
                if board[i][j] == 0:
                    threats.append((i, j))
                    break
    return threats

def move_score(pos, board, side):
    """
    Heuristic score used to order moves.
    Larger for more line involvement and when the side already has two marks
    in a line (promotes forks or blocks).
    side = 1 → our move, side = -1 → opponent move.
    """
    r, c = pos
    line_cnt = sum(1 for line in WINNING_LINES if pos in line)
    our_cnt = sum(1 for line in WINNING_LINES if pos in line
                  for i, j in line if board[i][j] == 1)
    opp_cnt = sum(1 for line in WINNING_LINES if pos in line
                  for i, j in line if board[i][j] == -1)

    base = line_cnt * 10
    if side == 1 and our_cnt >= 2:
        base += our_cnt * 5
    elif side == -1 and opp_cnt >= 2:
        base += opp_cnt * 5
    return base

def alphabeta(board, is_max, alpha, beta):
    """
    Alpha‑beta search with move ordering and result caching.
    Returns:
        - (score, move) when is_max=True
        - score                when is_max=False
    """
    state = _state(board)
    key = (state, is_max)
    if key in _caches:
        # Cache stores only the score for the side that has the move.
        if is_max:
            return _caches[key]
        else:
            return _caches[key]

    # Terminal: win/loss/draw
    score = evaluate(board)
    if score != 0:
        _caches[key] = score
        return score
    if not any(cell == 0 for row in board for cell in row):
        _caches[key] = 0
        return 0

    empty_cells = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

    if is_max:  # our turn
        moves = sorted(empty_cells, key=lambda pos: move_score(pos, board, 1), reverse=True)
        best_score = -float('inf')
        best_move = None
        for r, c in moves:
            nb = [row[:] for row in board]   # shallow copy, then modify
            nb[r][c] = 1
            val = alphabeta(nb, False, alpha, beta)
            if val > best_score:
                best_score = val
                best_move = (r, c)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        _caches[key] = best_score
        return (best_score, best_move)

    else:  # opponent's turn
        moves = sorted(empty_cells, key=lambda pos: move_score(pos, board, -1), reverse=True)
        best_score = float('inf')
        for r, c in moves:
            nb = [row[:] for row in board]
            nb[r][c] = -1
            val = alphabeta(nb, True, alpha, beta)[0]
            if val < best_score:
                best_score = val
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        _caches[key] = best_score
        return best_score

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next optimal move as a (row, col) tuple (0‑based).
    Guarantees a legal move and tries to block opponent threats first.
    """
    empty = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

    # 1️⃣ Block opponent immediate win
    threats = opponent_threats(board)
    if threats:
        return min(threats)                     # lexicographically smallest

    # 2️⃣ Win immediately
    wins = find_win(board)
    if wins:
        return min(wins)

    # 3️⃣ Full minimax search with caching and heuristic move ordering
    best_score, move = alphabeta(board, True, -float('inf'), float('inf'))
    return move
