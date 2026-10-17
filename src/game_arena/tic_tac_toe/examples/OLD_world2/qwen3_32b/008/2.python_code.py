
from typing import Tuple, List

Board = List[List[int]]

def policy(board: Board) -> Tuple[int, int]:
    # Check for immediate win
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                temp = [row[:] for row in board]
                temp[i][j] = 1
                if is_win(temp, 1):
                    return (i, j)
    
    # Check if opponent can win in their next move and block
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                temp = [row[:] for row in board]
                temp[i][j] = -1
                if is_win(temp, -1):
                    return (i, j)
    
    # If no immediate win or threat, select best move based on heuristics
    best_score = -1
    best_move = (0, 0)
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                score = calculate_score(board, i, j)
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
                # Tie-breaker based on center proximity
                elif abs(score - best_score) < 1e-9:
                    current_i, current_j = best_move
                    d1 = (current_i - 1.5) ** 2 + (current_j - 1.5) ** 2
                    d2 = (i - 1.5) ** 2 + (j - 1.5) ** 2
                    if d2 < d1:
                        best_move = (i, j)
    
    return best_move

def is_win(board: Board, player: int) -> bool:
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    
    # Check main diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3 - i] == player for i in range(4)):
        return True
    
    return False

def calculate_score(board: Board, i: int, j: int) -> float:
    score = 0

    # Row check
    count_row = sum(1 for x in range(4) if board[i][x] == 1)
    score += count_row + 1  # Add the current move

    # Column check
    count_col = sum(1 for x in range(4) if board[x][j] == 1)
    score += count_col + 1

    # Main diagonal if i == j
    if i == j:
        count_diag = sum(1 for x in range(4) if board[x][x] == 1)
        score += count_diag + 1

    # Anti-diagonal if i + j == 3
    if i + j == 3:
        count_anti = sum(1 for x in range(4) if board[x][3 - x] == 1)
        score += count_anti + 1

    # Add a small bonus for center
    if (i, j) in [(1, 1), (1, 2), (2, 1), (2, 2)]:
        score += 0.1

    return score
