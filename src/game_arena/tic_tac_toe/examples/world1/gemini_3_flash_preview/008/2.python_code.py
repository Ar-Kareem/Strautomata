
import math

def check_winner(board):
    # Check rows and columns
    for i in range(3):
        if sum(board[i]) == 3: return 1
        if sum(board[i]) == -3: return -1
        if board[0][i] + board[1][i] + board[2][i] == 3: return 1
        if board[0][i] + board[1][i] + board[2][i] == -3: return -1
    
    # Check diagonals
    diag1 = board[0][0] + board[1][1] + board[2][2]
    diag2 = board[0][2] + board[1][1] + board[2][0]
    if diag1 == 3 or diag2 == 3: return 1
    if diag1 == -3 or diag2 == -3: return -1
    
    # Check for draw or ongoing
    for row in board:
        if 0 in row:
            return None # Game ongoing
    return 0 # Draw

def minimax(board, is_maximizing):
    res = check_winner(board)
    if res is not None:
        return res

    if is_maximizing:
        best_score = -math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1
                    score = minimax(board, False)
                    board[r][c] = 0
                    best_score = max(score, best_score)
        return best_score
    else:
        best_score = math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1
                    score = minimax(board, True)
                    board[r][c] = 0
                    best_score = min(score, best_score)
        return best_score

def policy(board: list[list[int]]) -> tuple[int, int]:
    best_val = -math.inf
    move = (0, 0)
    
    # If board is empty, starting in a corner or center is stronger
    if all(all(cell == 0 for cell in row) for row in board):
        return (1, 1)

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                move_val = minimax(board, False)
                board[r][c] = 0
                
                if move_val > best_val:
                    best_val = move_val
                    move = (r, c)
                    
    return move
