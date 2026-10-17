
from typing import List, Tuple

# Precompute all 49 winning lines in 3x3x3 Tic Tac Toe
LINES = []

# Axis-aligned lines (27 lines)
for i in range(3):
    for j in range(3):
        LINES.append([(i, j, k) for k in range(3)])  # z-axis
for i in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for j in range(3)])  # y-axis
for j in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for i in range(3)])  # x-axis

# Face diagonals (18 lines)
for k in range(3):
    LINES.append([(i, i, k) for i in range(3)])      # xy plane
    LINES.append([(i, 2-i, k) for i in range(3)])    # xy plane anti
for j in range(3):
    LINES.append([(i, j, i) for i in range(3)])      # xz plane
    LINES.append([(i, j, 2-i) for i in range(3)])    # xz plane anti
for i in range(3):
    LINES.append([(i, j, j) for j in range(3)])      # yz plane
    LINES.append([(i, j, 2-j) for j in range(3)])    # yz plane anti

# Space diagonals (4 lines)
LINES.append([(i, i, i) for i in range(3)])
LINES.append([(i, i, 2-i) for i in range(3)])
LINES.append([(i, 2-i, i) for i in range(3)])
LINES.append([(i, 2-i, 2-i) for i in range(3)])


def _check_win(board: List[List[List[int]]], player: int) -> bool:
    """Check if the specified player has completed any line."""
    for line in LINES:
        if all(board[i][j][k] == player for i, j, k in line):
            return True
    return False


def _evaluate(board: List[List[List[int]]]) -> int:
    """
    Heuristic evaluation function.
    Scores: 3-in-row=1000, 2-in-row=100, 1-in-row=10 (and negatives for opponent).
    """
    score = 0
    for line in LINES:
        vals = [board[i][j][k] for i, j, k in line]
        us = vals.count(1)
        them = vals.count(-1)
        empty = vals.count(0)
        
        if us == 3:
            score += 1000
        elif us == 2 and empty == 1:
            score += 100
        elif us == 1 and empty == 2:
            score += 10
            
        if them == 3:
            score -= 1000
        elif them == 2 and empty == 1:
            score -= 100
        elif them == 1 and empty == 2:
            score -= 10
    return score


def _minimax(board: List[List[List[int]]], depth: int, alpha: float, beta: float, is_max: bool) -> float:
    """Minimax with alpha-beta pruning."""
    if _check_win(board, 1):
        return 10000
    if _check_win(board, -1):
        return -10000
    if depth == 0:
        return _evaluate(board)
    
    empty = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    if not empty:
        return 0
    
    if is_max:
        value = -float('inf')
        for i, j, k in empty:
            board[i][j][k] = 1
            value = max(value, _minimax(board, depth-1, alpha, beta, False))
            board[i][j][k] = 0
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        for i, j, k in empty:
            board[i][j][k] = -1
            value = min(value, _minimax(board, depth-1, alpha, beta, True))
            board[i][j][k] = 0
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Get empty cells
    empty = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    
    if not empty:
        return (0, 0, 0)  # Should not occur in valid game
    
    # 1. Immediate win
    for move in empty:
        i, j, k = move
        board[i][j][k] = 1
        if _check_win(board, 1):
            board[i][j][k] = 0
            return move
        board[i][j][k] = 0
    
    # 2. Immediate block
    for move in empty:
        i, j, k = move
        board[i][j][k] = -1
        if _check_win(board, -1):
            board[i][j][k] = 0
            return move
        board[i][j][k] = 0
    
    # 3. Opening heuristic: center is strongest
    if (1, 1, 1) in empty:
        return (1, 1, 1)
    
    # 4. Move ordering for better pruning: center > corners > faces > edges
    def priority(m):
        i, j, k = m
        if i == 1 and j == 1 and k == 1:
            return 0
        if (i in [0, 2]) and (j in [0, 2]) and (k in [0, 2]):
            return 1
        if (i == 1 and j == 1) or (i == 1 and k == 1) or (j == 1 and k == 1):
            return 2
        return 3
    
    empty.sort(key=priority)
    
    # 5. Minimax search with adaptive depth
    # Use depth 4 for endgame, depth 3 for midgame to ensure speed
    depth = 4 if len(empty) <= 10 else 3
    
    best_move = empty[0]
    best_score = -float('inf')
    
    for move in empty:
        i, j, k = move
        board[i][j][k] = 1
        score = _minimax(board, depth, -float('inf'), float('inf'), False)
        board[i][j][k] = 0
        
        if score > best_score:
            best_score = score
            best_move = move
            if score >= 10000:  # Winning move found
                break
    
    return best_move
