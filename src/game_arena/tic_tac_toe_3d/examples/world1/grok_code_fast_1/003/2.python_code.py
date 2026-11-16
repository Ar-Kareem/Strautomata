
import numpy as np

lines = []
# Slice z: for each z, the 2D board
for z in range(3):
    # Rows (y varying, x fixed, z fixed)
    for i in range(3):
        lines.append([(i, j, z) for j in range(3)])
    # Columns (x varying, y fixed, z fixed)
    for j in range(3):
        lines.append([(i, j, z) for i in range(3)])
    # Diagonals
    lines.append([(i, i, z) for i in range(3)])
    lines.append([(i, 2-i, z) for i in range(3)])
# Vertical (z varying, x fixed, y fixed)
for i in range(3):
    for j in range(3):
        lines.append([(i, j, k) for k in range(3)])
# Cube diagonals
lines.append([(i, i, i) for i in range(3)])
lines.append([(i, i, 2-i) for i in range(3)])
lines.append([(i, 2-i, i) for i in range(3)])
lines.append([(i, 2-i, 2-i) for i in range(3)])

def check_win(board):
    for line in lines:
        s = sum(board[pos] for pos in line)
        if s == 3 or s == -3:
            return True
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    board = np.array(board)
    
    # First, check for immediate winning moves
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == 0:
                    board_temp = board.copy()
                    board_temp[i, j, k] = 1
                    if check_win(board_temp):
                        return (i, j, k)
    
    # Then, check for blocking moves (prevent opponent win)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == 0:
                    board_temp = board.copy()
                    board_temp[i, j, k] = -1
                    if check_win(board_temp):
                        return (i, j, k)
    
    # Check if center is available and prefer it
    if board[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Evaluate remaining moves: choose the one maximizing threats
    max_score = -1
    best_move = None
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == 0:
                    board_temp = board.copy()
                    board_temp[i, j, k] = 1
                    score = 0
                    for line in lines:
                        has_opp = any(board_temp[pos] == -1 for pos in line)
                        s = sum(board_temp[pos] for pos in line)
                        if not has_opp and s == 2:
                            score += 1
                    if score > max_score:
                        max_score = score
                        best_move = (i, j, k)
                    elif score == max_score and best_move is None:
                        best_move = (i, j, k)  # Tie-breaker: first encountered
    
    if best_move is not None:
        return best_move
    
    # Fallback: should not reach here if legal moves exist
    raise ValueError("No legal moves available")
