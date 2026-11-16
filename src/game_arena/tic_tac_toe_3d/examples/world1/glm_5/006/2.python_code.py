
import sys

# Precompute all 49 winning lines (indices in a flattened 27-cell board)
# Board indices: i*9 + j*3 + k
LINES = []
# 1. Rows (fixed i, j; k varies) and Columns (fixed i, k; j varies) and Pillars (fixed j, k; i varies)
# Axial lines
for i in range(3):
    for j in range(3):
        LINES.append([i*9 + j*3 + k for k in range(3)]) # z-axis (pillar)
    for k in range(3):
        LINES.append([i*9 + j*3 + k for j in range(3)]) # y-axis (column)

for j in range(3):
    for k in range(3):
        LINES.append([i*9 + j*3 + k for i in range(3)]) # x-axis (row)

# 2. 2D Diagonals within planes
# Planes XY (fixed z)
for k in range(3):
    LINES.append([i*9 + i*3 + k for i in range(3)])
    LINES.append([i*9 + (2-i)*3 + k for i in range(3)])
# Planes XZ (fixed y)
for j in range(3):
    LINES.append([i*9 + j*3 + i for i in range(3)])
    LINES.append([i*9 + j*3 + (2-i) for i in range(3)])
# Planes YZ (fixed x)
for i in range(3):
    LINES.append([i*9 + j*3 + j for j in range(3)])
    LINES.append([i*9 + j*3 + (2-j) for j in range(3)])

# 3. 4 Main 3D Diagonals
LINES.append([i*9 + i*3 + i for i in range(3)])
LINES.append([i*9 + i*3 + (2-i) for i in range(3)])
LINES.append([i*9 + (2-i)*3 + i for i in range(3)])
LINES.append([i*9 + (2-i)*3 + (2-i) for i in range(3)])

# Strategy constants
WIN_SCORE = 100000
DEPTH = 5

# Center, Corners, Edges ordering for move pruning
# Indices in flattened board
CENTER = [13]
CORNERS = [0, 2, 6, 8, 18, 20, 24, 26]
EDGES = [1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25] 
# Faces (center of faces) are also good, practically edges in this logic
FACES = [4, 10, 12, 14, 16, 22] 
MOVE_ORDER = CENTER + CORNERS + FACES + EDGES

def check_winner(board_flat):
    for line in LINES:
        s = board_flat[line[0]] + board_flat[line[1]] + board_flat[line[2]]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def evaluate(board_flat):
    score = 0
    for line in LINES:
        line_sum = board_flat[line[0]] + board_flat[line[1]] + board_flat[line[2]]
        
        if line_sum == 3:
            score += WIN_SCORE
        elif line_sum == -3:
            score -= WIN_SCORE
        elif line_sum == 2: # Two 1s and one 0
            score += 100
        elif line_sum == -2: # Two -1s and one 0
            score -= 100
        elif line_sum == 1: # One 1 and two 0s
            # Check if blocked
            if -1 not in [board_flat[line[0]], board_flat[line[1]], board_flat[line[2]]]:
                score += 10
        elif line_sum == -1: # One -1 and two 0s
            if 1 not in [board_flat[line[0]], board_flat[line[1]], board_flat[line[2]]]:
                score -= 10
    return score

def minimax(board_flat, depth, alpha, beta, maximizing_player):
    winner = check_winner(board_flat)
    if winner != 0:
        return winner * WIN_SCORE
    if depth == 0 or 0 not in board_flat:
        return evaluate(board_flat)
    
    # Generate moves in pre-defined order
    moves = [i for i in MOVE_ORDER if board_flat[i] == 0]
    
    if not moves:
        return evaluate(board_flat)

    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            board_flat[move] = 1
            eval_val = minimax(board_flat, depth - 1, alpha, beta, False)
            board_flat[move] = 0
            if eval_val > max_eval:
                max_eval = eval_val
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            board_flat[move] = -1
            eval_val = minimax(board_flat, depth - 1, alpha, beta, True)
            board_flat[move] = 0
            if eval_val < min_eval:
                min_eval = eval_val
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Flatten board
    flat = []
    for i in range(3):
        for j in range(3):
            flat.extend(board[i][j])
    
    # If empty, take center (fastest path to win/fork)
    if 1 not in flat and -1 not in flat:
        return (1, 1, 1)

    # If center is taken by opponent, take a corner? 
    # Or just let minimax handle it. Minimax will handle it.

    best_move = -1
    best_value = -float('inf')
    
    # We are player 1 (maximizing)
    # Iterate through possible moves in strategic order
    possible_moves = [i for i in MOVE_ORDER if flat[i] == 0]
    
    # If no moves in preferred order (shouldn't happen often), take any
    if not possible_moves:
        possible_moves = [i for i in range(27) if flat[i] == 0]

    for move in possible_moves:
        flat[move] = 1
        # Check immediate win
        if check_winner(flat) == 1:
            flat[move] = 0
            best_move = move
            break
        
        move_value = minimax(flat, DEPTH - 1, -float('inf'), float('inf'), False)
        flat[move] = 0
        
        if move_value > best_value:
            best_value = move_value
            best_move = move

    # Convert flat index back to (i, j, k)
    i = best_move // 9
    j = (best_move % 9) // 3
    k = best_move % 3
    
    return (i, j, k)
