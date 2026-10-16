
from typing import List, Tuple, Dict

# Precompute all winning lines (rows, cols, diagonals)
LINES = []
for r in range(4):
    LINES.append([(r, c) for c in range(4)])
for c in range(4):
    LINES.append([(r, c) for r in range(4)])
LINES.append([(i, i) for i in range(4)])
LINES.append([(i, 3 - i) for i in range(4)])

# Move ordering weights: center > corner > edge
WEIGHTS = [[1, 2, 2, 1],
           [2, 3, 3, 2],
           [2, 3, 3, 2],
           [1, 2, 2, 1]]

Cache: Dict[Tuple[Tuple[int, ...], int, int], int] = {}

def board_to_tuple(board: List[List[int]]) -> Tuple[int, ...]:
    return tuple(cell for row in board for cell in row)

def check_winner(board: List[List[int]]) -> int:
    for line in LINES:
        s = sum(board[r][c] for r, c in line)
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0

def heuristic(board: List[List[int]]) -> int:
    score = 0
    for line in LINES:
        vals = [board[r][c] for r, c in line]
        if 1 in vals and -1 in vals:
            continue
        c1 = vals.count(1)
        c2 = vals.count(-1)
        if c1 > 0:
            score += 10 ** c1
        elif c2 > 0:
            score -= 10 ** c2
    return score

def negamax(board: List[List[int]], player: int, depth: int, alpha: int, beta: int) -> int:
    key = (board_to_tuple(board), player, depth)
    if key in Cache:
        return Cache[key]

    winner = check_winner(board)
    if winner == player:
        return 100000 + depth
    elif winner == -player:
        return -100000 - depth

    empties = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    if depth == 0 or not empties:
        return player * heuristic(board)

    # Order moves by positional weight
    empties.sort(key=lambda x: WEIGHTS[x[0]][x[1]], reverse=True)

    best = -10**9
    for r, c in empties:
        board[r][c] = player
        val = -negamax(board, -player, depth - 1, -beta, -alpha)
        board[r][c] = 0
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    Cache[key] = best
    return best

def policy(board: List[List[int]]) -> Tuple[int, int]:
    empties = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    if not empties:
        return (0, 0)

    # Immediate win
    for r, c in empties:
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Immediate block
    for r, c in empties:
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Depth selection based on remaining moves
    n = len(empties)
    if n <= 8:
        depth = n
    elif n <= 10:
        depth = 8
    else:
        depth = 6

    # Order moves by positional weight
    empties.sort(key=lambda x: WEIGHTS[x[0]][x[1]], reverse=True)

    best_move = empties[0]
    best_score = -10**9

    for r, c in empties:
        board[r][c] = 1
        score = -negamax(board, -1, depth - 1, -10**9, 10**9)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
