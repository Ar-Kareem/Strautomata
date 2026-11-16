
from typing import List
from math import inf

def check_winner(board: List[List[int]]) -> int:
    """Check the winner of the board. Returns 1, -1, or 0 (no winner)."""
    # Check rows
    for row in board:
        if row[0] != 0 and row[0] == row[1] == row[2]:
            return row[0]
    # Check columns
    for col in range(3):
        if board[0][col] != 0 and board[0][col] == board[1][col] == board[2][col]:
            return board[0][col]
    # Check diagonals
    if board[0][0] != 0 and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] != 0 and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    return 0

def is_full(board: List[List[int]]) -> bool:
    """Check if the board is full (no empty cells)."""
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return False
    return True

def minimax(board: List[List[int]], depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
    """Minimax algorithm with alpha-beta pruning. Returns the best score from the perspective of player 1."""
    winner = check_winner(board)
    if winner == 1:
        return 10 - depth  # Player 1 wins
    elif winner == -1:
        return depth - 10  # Player -1 wins (so we lose)
    elif is_full(board):
        return 0  # Draw
    
    if is_maximizing:
        best_score = -inf
        for move in range(1, 10):
            row = (move - 1) // 3
            col = (move - 1) % 3
            if board[row][col] == 0:
                new_board = [row[:] for row in board]
                new_board[row][col] = 1  # Our move
                score = minimax(new_board, depth + 1, False, alpha, beta)
                best_score = max(best_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break  # Prune
        return best_score
    else:
        best_score = inf
        for move in range(1, 10):
            row = (move - 1) // 3
            col = (move - 1) % 3
            if board[row][col] == 0:
                new_board = [row[:] for row in board]
                new_board[row][col] = -1  # Opponent's move
                score = minimax(new_board, depth + 1, True, alpha, beta)
                best_score = min(best_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break  # Prune
        return best_score

def policy(board: List[List[int]]) -> int:
    """Return the best move (1-9) for the current board state."""
    # Define move order: center, corners, then edges
    move_order = [5, 1, 3, 7, 9, 2, 4, 6, 8]
    available_moves = [move for move in move_order if board[(move - 1) // 3][(move - 1) % 3] == 0]
    
    # Check for immediate win
    for move in available_moves:
        row = (move - 1) // 3
        col = (move - 1) % 3
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1
        if check_winner(temp_board) == 1:
            return move
    
    # Check for blocking opponent's immediate win
    for move in available_moves:
        row = (move - 1) // 3
        col = (move - 1) % 3
        temp_board = [row[:] for row in board]
        temp_board[row][col] = -1
        if check_winner(temp_board) == -1:
            return move
    
    # Use minimax to determine the best move
    best_score = -inf
    best_move = None
    for move in available_moves:
        row = (move - 1) // 3
        col = (move - 1) % 3
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1
        score = minimax(temp_board, 1, False, -inf, inf)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
