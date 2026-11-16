
import numpy as np
import time
import sys

# All 49 winning lines in 3x3x3
WINNING_LINES = []

# Generate all lines
# 3x3x3 grid indices: 0..26 mapped to (i,j,k)

def _generate_lines():
    lines = []
    # Rows along each axis
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # z-axis
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])  # y-axis
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])  # x-axis

    # Face diagonals (on each xy, xz, yz plane)
    for i in range(3):
        lines.append([(i, j, j) for j in range(3)])
        lines.append([(i, j, 2 - j) for j in range(3)])
    for j in range(3):
        lines.append([(i, j, i) for i in range(3)])
        lines.append([(i, j, 2 - i) for i in range(3)])
    for k in range(3):
        lines.append([(i, i, k) for i in range(3)])
        lines.append([(i, 2 - i, k) for i in range(3)])

    # Space diagonals (corner to corner through center)
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2 - i) for i in range(3)])
    lines.append([(i, 2 - i, i) for i in range(3)])
    lines.append([(i, 2 - i, 2 - i) for i in range(3)])

    return lines

WINNING_LINES = _generate_lines()

# Pre-compute line indices for faster evaluation
LINE_INDICES = []
for line in WINNING_LINES:
    idx_line = []
    for (i, j, k) in line:
        idx_line.append((i, j, k))
    LINE_INDICES.append(idx_line)

# Order moves for better pruning: center first, then corners, then edges
MOVE_ORDER = []
# Center
MOVE_ORDER.append((1, 1, 1))
# Corners (8 corners)
for i in [0, 2]:
    for j in [0, 2]:
        for k in [0, 2]:
            if (i, j, k) != (1, 1, 1):
                MOVE_ORDER.append((i, j, k))
# Face centers
for i in [0, 2]:
    for j in [1]:
        for k in [1]:
            MOVE_ORDER.append((i, j, k))
for i in [1]:
    for j in [0, 2]:
        for k in [1]:
            MOVE_ORDER.append((i, j, k))
for i in [1]:
    for j in [1]:
        for k in [0, 2]:
            MOVE_ORDER.append((i, j, k))
# Edges
for i in [0, 2]:
    for j in [0, 2]:
        for k in [1]:
            MOVE_ORDER.append((i, j, k))
for i in [0, 2]:
    for j in [1]:
        for k in [0, 2]:
            MOVE_ORDER.append((i, j, k))
for i in [1]:
    for j in [0, 2]:
        for k in [0, 2]:
            MOVE_ORDER.append((i, j, k))

def check_winner(board):
    """Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    for line in LINE_INDICES:
        s = sum(board[i][j][k] for i, j, k in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def get_empty_cells(board):
    """Return list of empty cells."""
    empty = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty.append((i, j, k))
    return empty

def is_full(board):
    """Check if board is full."""
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return False
    return True

def evaluate_board(board):
    """Heuristic evaluation of board state."""
    score = 0
    for line in LINE_INDICES:
        s = sum(board[i][j][k] for i, j, k in line)
        if s == 3:
            return 10000
        if s == -3:
            return -10000
        if s == 2 and any(board[i][j][k] == 0 for i, j, k in line):
            score += 100
        if s == -2 and any(board[i][j][k] == 0 for i, j, k in line):
            score -= 100
        if s == 1 and all(board[i][j][k] != -1 for i, j, k in line):
            score += 10
        if s == -1 and all(board[i][j][k] != 1 for i, j, k in line):
            score -= 10
    return score

def minimax(board, depth, alpha, beta, is_maximizing, start_time, time_limit):
    """Minimax with alpha-beta pruning and time limit."""
    if time.time() - start_time > time_limit:
        return evaluate_board(board), None
    
    winner = check_winner(board)
    if winner == 1:
        return 10000 + depth, None
    if winner == -1:
        return -10000 - depth, None
    if is_full(board) or depth == 0:
        return evaluate_board(board), None
    
    # Get empty cells sorted by move order heuristic
    empty = get_empty_cells(board)
    
    # Sort moves: prefer those in MOVE_ORDER first, then rest
    move_order_map = {m: i for i, m in enumerate(MOVE_ORDER)}
    empty_sorted = sorted(empty, key=lambda m: move_order_map.get(m, 100))
    
    if is_maximizing:
        max_eval = -float('inf')
        best_move = None
        for move in empty_sorted:
            if time.time() - start_time > time_limit:
                return max_eval, best_move
            i, j, k = move
            board[i][j][k] = 1
            eval_val, _ = minimax(board, depth - 1, alpha, beta, False, start_time, time_limit)
            board[i][j][k] = 0
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = move
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for move in empty_sorted:
            if time.time() - start_time > time_limit:
                return min_eval, best_move
            i, j, k = move
            board[i][j][k] = -1
            eval_val, _ = minimax(board, depth - 1, alpha, beta, True, start_time, time_limit)
            board[i][j][k] = 0
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = move
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board):
    """
    Policy function for 3D Tic Tac Toe.
    Returns the best move as (i, j, k).
    """
    start_time = time.time()
    time_limit = 0.95  # Leave some margin
    
    # Convert to mutable list
    board_list = [[[board[i][j][k] for k in range(3)] for j in range(3)] for i in range(3)]
    
    empty = get_empty_cells(board_list)
    if not empty:
        return (0, 0, 0)  # fallback, shouldn't happen
    
    # If first move or board empty except maybe one opponent move, play center
    player_moves = sum(1 for i in range(3) for j in range(3) for k in range(3) if board_list[i][j][k] == 1)
    opponent_moves = sum(1 for i in range(3) for j in range(3) for k in range(3) if board_list[i][j][k] == -1)
    
    if player_moves == 0 and opponent_moves <= 1 and board_list[1][1][1] == 0:
        return (1, 1, 1)
    
    # Check for immediate winning move
    for i, j, k in empty:
        board_list[i][j][k] = 1
        if check_winner(board_list) == 1:
            board_list[i][j][k] = 0
            return (i, j, k)
        board_list[i][j][k] = 0
    
    # Check for immediate blocking move
    for i, j, k in empty:
        board_list[i][j][k] = -1
        if check_winner(board_list) == -1:
            board_list[i][j][k] = 0
            return (i, j, k)
        board_list[i][j][k] = 0
    
    # Iterative deepening search
    best_move = empty[0]  # default
    max_depth = 1
    
    # Determine reasonable max depth based on empty cells
    num_empty = len(empty)
    if num_empty > 15:
        max_depth = 3
    elif num_empty > 10:
        max_depth = 5
    else:
        max_depth = 10
    
    current_depth = 1
    while current_depth <= max_depth:
        if time.time() - start_time > time_limit * 0.6 and current_depth > 2:
            break
        _, move = minimax(board_list, current_depth, -float('inf'), float('inf'), True, start_time, time_limit)
        if move is not None:
            best_move = move
        current_depth += 1
        # If time is running out, break
        if time.time() - start_time > time_limit * 0.5:
            break
    
    # Ensure we return a tuple of ints
    return (int(best_move[0]), int(best_move[1]), int(best_move[2]))
