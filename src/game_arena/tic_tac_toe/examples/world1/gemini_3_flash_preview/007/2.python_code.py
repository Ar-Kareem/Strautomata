
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the best move (row, col) for player 1 using Minimax.
    """
    
    def check_winner(b):
        # Rows and Columns
        for i in range(3):
            if sum(b[i]) == 3 or sum(row[i] for row in b) == 3:
                return 1
            if sum(b[i]) == -3 or sum(row[i] for row in b) == -3:
                return -1
        # Diagonals
        diag1 = b[0][0] + b[1][1] + b[2][2]
        diag2 = b[0][2] + b[1][1] + b[2][0]
        if diag1 == 3 or diag2 == 3:
            return 1
        if diag1 == -3 or diag2 == -3:
            return -1
        return 0

    def is_full(b):
        return all(cell != 0 for row in b for cell in row)

    def minimax(b, depth, is_maximizing):
        winner = check_winner(b)
        if winner == 1: return 10 - depth
        if winner == -1: return depth - 10
        if is_full(b): return 0

        if is_maximizing:
            best_score = -float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = 1
                        score = minimax(b, depth + 1, False)
                        b[r][c] = 0
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -1
                        score = minimax(b, depth + 1, True)
                        b[r][c] = 0
                        best_score = min(score, best_score)
            return best_score

    best_val = -float('inf')
    move = (-1, -1)
    
    # Check if board is empty to speed up first move
    if all(cell == 0 for row in board for cell in row):
        return (0, 0)

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                move_val = minimax(board, 0, False)
                board[r][c] = 0
                if move_val > best_val:
                    best_val = move_val
                    move = (r, c)
                    
    return move
