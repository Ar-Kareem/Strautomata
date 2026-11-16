
import math
from typing import List, Tuple

# Precompute all winning lines in 3x3x3
LINES = []
# Axis-aligned lines
for j in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for i in range(3)])
for i in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for j in range(3)])
for i in range(3):
    for j in range(3):
        LINES.append([(i, j, k) for k in range(3)])
# Plane diagonals
for k in range(3):
    LINES.append([(i, i, k) for i in range(3)])
    LINES.append([(i, 2 - i, k) for i in range(3)])
for j in range(3):
    LINES.append([(i, j, i) for i in range(3)])
    LINES.append([(i, j, 2 - i) for i in range(3)])
for i in range(3):
    LINES.append([(i, j, j) for j in range(3)])
    LINES.append([(i, j, 2 - j) for j in range(3)])
# Space diagonals
LINES.append([(0,0,0),(1,1,1),(2,2,2)])
LINES.append([(0,0,2),(1,1,1),(2,2,0)])
LINES.append([(0,2,0),(1,1,1),(2,0,2)])
LINES.append([(0,2,2),(1,1,1),(2,0,0)])

WEIGHTS = {1: 1, 2: 5}

def check_winner(board):
    for line in LINES:
        s = sum(board[i][j][k] for i,j,k in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def heuristic(board):
    score = 0
    for line in LINES:
        vals = [board[i][j][k] for i,j,k in line]
        if 1 in vals and -1 in vals:
            continue
        s = sum(vals)
        if s > 0:
            score += WEIGHTS.get(s, 0)
        elif s < 0:
            score -= WEIGHTS.get(-s, 0)
    # slight preference for center
    if board[1][1][1] == 1:
        score += 1
    elif board[1][1][1] == -1:
        score -= 1
    return score

def minimax(board, depth, player, alpha, beta):
    winner = check_winner(board)
    if winner != 0:
        return winner * 1000 + depth
    moves = [(i,j,k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    if depth == 0 or not moves:
        return heuristic(board)
    if player == 1:
        value = -math.inf
        for i,j,k in moves:
            board[i][j][k] = 1
            value = max(value, minimax(board, depth-1, -1, alpha, beta))
            board[i][j][k] = 0
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:
        value = math.inf
        for i,j,k in moves:
            board[i][j][k] = -1
            value = min(value, minimax(board, depth-1, 1, alpha, beta))
            board[i][j][k] = 0
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

def policy(board: List[List[List[int]]]) -> Tuple[int,int,int]:
    moves = [(i,j,k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    if not moves:
        return (0,0,0)
    # If empty board, take center
    if len(moves) == 27 and board[1][1][1] == 0:
        return (1,1,1)
    # Immediate win
    for i,j,k in moves:
        board[i][j][k] = 1
        if check_winner(board) == 1:
            board[i][j][k] = 0
            return (i,j,k)
        board[i][j][k] = 0
    # Block opponent win
    for i,j,k in moves:
        board[i][j][k] = -1
        if check_winner(board) == -1:
            board[i][j][k] = 0
            return (i,j,k)
        board[i][j][k] = 0
    # Minimax search
    depth = 3 if len(moves) <= 12 else 2
    best_val = -math.inf
    best_move = moves[0]
    for i,j,k in moves:
        board[i][j][k] = 1
        val = minimax(board, depth-1, -1, -math.inf, math.inf)
        board[i][j][k] = 0
        if val > best_val:
            best_val = val
            best_move = (i,j,k)
    return best_move
