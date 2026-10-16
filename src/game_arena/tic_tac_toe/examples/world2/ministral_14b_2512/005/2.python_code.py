
import numpy as np
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    current_player = 1  # Assuming the policy is for player 1

    # Check for immediate win or block
    move = find_immediate_win_or_block(board_np, current_player)
    if move is not None:
        return move

    # Evaluate all possible moves using minimax
    best_move = None
    best_score = -float('inf')
    for row in range(4):
        for col in range(4):
            if board_np[row, col] == 0:
                board_np[row, col] = current_player
                score = minimax(board_np, 0, -float('inf'), float('inf'), False)
                board_np[row, col] = 0
                if score > best_score:
                    best_score = score
                    best_move = (row, col)
    return best_move

def find_immediate_win_or_block(board: np.ndarray, player: int) -> tuple[int, int]:
    opponent = -player
    # Check all possible lines (rows, columns, diagonals)
    for row in range(4):
        for col in range(4):
            if board[row, col] == 0:
                board[row, col] = player
                if is_win(board, player):
                    board[row, col] = 0
                    return (row, col)
                board[row, col] = 0

    for row in range(4):
        for col in range(4):
            if board[row, col] == 0:
                board[row, col] = opponent
                if is_win(board, opponent):
                    board[row, col] = 0
                    return (row, col)
                board[row, col] = 0
    return None

def is_win(board: np.ndarray, player: int) -> bool:
    # Check rows
    for row in range(4):
        if all(board[row, col] == player for col in range(4)):
            return True
    # Check columns
    for col in range(4):
        if all(board[row, col] == player for row in range(4)):
            return True
    # Check diagonals
    if all(board[i, i] == player for i in range(4)):
        return True
    if all(board[i, 3 - i] == player for i in range(4)):
        return True
    return False

@lru_cache(maxsize=None)
def minimax(board: tuple, depth: int, alpha: float, beta: float, maximizing_player: bool) -> int:
    board_np = np.array(list(board))
    current_player = 1 if maximizing_player else -1
    opponent = -current_player

    # Check terminal states
    if is_win(board_np, current_player):
        return 10 - depth  # Higher score for immediate win
    if is_win(board_np, opponent):
        return -10 + depth  # Lower score for opponent's win
    if np.all(board_np != 0):
        return 0  # Draw

    if maximizing_player:
        max_eval = -float('inf')
        for row in range(4):
            for col in range(4):
                if board_np[row, col] == 0:
                    board_np[row, col] = current_player
                    eval = minimax(tuple(map(tuple, board_np)), depth + 1, alpha, beta, False)
                    board_np[row, col] = 0
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for row in range(4):
            for col in range(4):
                if board_np[row, col] == 0:
                    board_np[row, col] = opponent
                    eval = minimax(tuple(map(tuple, board_np)), depth + 1, alpha, beta, True)
                    board_np[row, col] = 0
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
        return min_eval
