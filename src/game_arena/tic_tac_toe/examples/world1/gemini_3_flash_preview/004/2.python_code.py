
import math

def check_winner(board):
    # Check rows, columns and diagonals
    for i in range(3):
        if abs(sum(board[i])) == 3:
            return board[i][0]
        if abs(sum(board[j][i] for j in range(3))) == 3:
            return board[0][i]
    
    if abs(sum(board[i][i] for i in range(3))) == 3:
        return board[0][0]
    if abs(sum(board[i][2-i] for i in range(3))) == 3:
        return board[0][2]
    
    # Check for draw or ongoing
    if any(0 in row for row in board):
        return None  # Game ongoing
    return 0  # Draw

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
    move = (-1, -1)
    
    # Check if board is empty (optimization for first move)
    if all(all(cell == 0 for cell in row) for row in board):
        return (0, 0)

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
