
import numpy as np

ROWS = 6
COLS = 7

def get_drop_row(board, c):
    for r in reversed(range(ROWS)):
        if board[r][c] == 0:
            return r
    return -1

def check_win(board, player):
    def check_line(a, b, c, d):
        return all(board[i][j] == player for i, j in [a, b, c, d])
    
    for r in range(ROWS):
        for c in range(COLS - 3):
            if check_line((r, c), (r, c+1), (r, c+2), (r, c+3)):
                return True
    for c in range(COLS):
        for r in range(ROWS - 3):
            if check_line((r, c), (r+1, c), (r+2, c), (r+3, c)):
                return True
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if check_line((r, c), (r+1, c+1), (r+2, c+2), (r+3, c+3)):
                return True
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            if check_line((r, c), (r+1, c-1), (r+2, c-2), (r+3, c-3)):
                return True
    return False

def evaluate(board, player):
    score = 0
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == player:
                for dr, dc in directions:
                    count = 1
                    for i in range(1, 4):
                        rr = r + dr * i
                        cc = c + dc * i
                        if 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
                            count += 1
                        else:
                            break
                    if count >= 3:
                        score += count
    return score

def policy(board: list[list[int]]) -> int:
    b = np.array(board)
    # Note: b is numpy array for potential future use, but board is list of lists
    
    legal = [c for c in range(COLS) if board[0][c] == 0]
    
    if not legal:
        return 0  # Fallback, though shouldn't happen
    
    # Check for winning moves
    for c in legal:
        row = get_drop_row(board, c)
        if row != -1:
            board[row][c] = 1
            if check_win(board, 1):
                board[row][c] = 0
                return c
            board[row][c] = 0
    
    # Check for blocking opponent's win
    for c in legal:
        row = get_drop_row(board, c)
        if row != -1:
            board[row][c] = -1
            if check_win(board, -1):
                board[row][c] = 0
                return c
            board[row][c] = 0
    
    # No immediate win/block, evaluate each legal move
    scores = []
    for c in legal:
        row = get_drop_row(board, c)
        if row != -1:
            board[row][c] = 1
            score = evaluate(board, 1) - evaluate(board, -1)
            board[row][c] = 0
            scores.append(score)
    
    # Choose the move with the highest score
    best_index = scores.index(max(scores))
    return legal[best_index]
