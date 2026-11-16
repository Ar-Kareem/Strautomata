
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game using minimax with alpha-beta pruning.

    Args:
        board: A 4x4 list of lists where:
            - 0 represents an empty cell
            - 1 represents the player's pieces
            - -1 represents the opponent's pieces

    Returns:
        A tuple (row, col) indicating the next move (0-3, 0-3)
    """
    # Convert to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)

    # Find all empty cells
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board_np[i, j] == 0]

    if not empty_cells:
        return (0, 0)  # Shouldn't happen in normal play

    # Initialize best move and score
    best_move = empty_cells[0]
    best_score = -float('inf')

    # Iterate through all possible moves
    for move in empty_cells:
        # Make the move
        board_np[move] = 1

        # Get the score of this move
        score = minimax(board_np, 0, -float('inf'), float('inf'), False)

        # Undo the move
        board_np[move] = 0

        # Update best move if this move is better
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, is_maximizing: bool) -> int:
    """
    Minimax algorithm with alpha-beta pruning to evaluate board positions.

    Args:
        board: Current board state
        depth: Current depth in the search tree
        alpha: Best value that the maximizer can guarantee
        beta: Best value that the minimizer can guarantee
        is_maximizing: Whether the current player is maximizing (True) or minimizing (False)

    Returns:
        The evaluated score of the board position
    """
    # Check if the game is over
    score = evaluate(board)

    if score != 0:
        return score

    if is_maximizing:
        best_score = -float('inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = 1
                    score = minimax(board, depth + 1, alpha, beta, False)
                    board[i, j] = 0
                    best_score = max(score, best_score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return best_score
    else:
        best_score = float('inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = -1
                    score = minimax(board, depth + 1, alpha, beta, True)
                    board[i, j] = 0
                    best_score = min(score, best_score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return best_score

def evaluate(board: np.ndarray) -> int:
    """
    Evaluates the current board state and returns a score.

    Args:
        board: Current board state

    Returns:
        Positive score if the current player is winning,
        Negative score if the opponent is winning,
        0 if the game is still ongoing or it's a draw
    """
    # Check rows
    for row in range(4):
        if board[row, 0] == board[row, 1] == board[row, 2] == board[row, 3] != 0:
            return 100 if board[row, 0] == 1 else -100

    # Check columns
    for col in range(4):
        if board[0, col] == board[1, col] == board[2, col] == board[3, col] != 0:
            return 100 if board[0, col] == 1 else -100

    # Check diagonals
    if board[0, 0] == board[1, 1] == board[2, 2] == board[3, 3] != 0:
        return 100 if board[0, 0] == 1 else -100
    if board[0, 3] == board[1, 2] == board[2, 1] == board[3, 0] != 0:
        return 100 if board[0, 3] == 1 else -100

    # Check for potential winning moves (3 in a row)
    # Rows
    for row in range(4):
        for col in range(1, 4):
            if board[row, col] == 0:
                board[row, col] = 1
                if evaluate(board) == 100:
                    board[row, col] = 0
                    return 50
                board[row, col] = -1
                if evaluate(board) == -100:
                    board[row, col] = 0
                    return -50
                board[row, col] = 0

    # Columns
    for col in range(4):
        for row in range(1, 4):
            if board[row, col] == 0:
                board[row, col] = 1
                if evaluate(board) == 100:
                    board[row, col] = 0
                    return 50
                board[row, col] = -1
                if evaluate(board) == -100:
                    board[row, col] = 0
                    return -50
                board[row, col] = 0

    # Diagonals
    for d in [(0, 0), (0, 3)]:
        for i in range(1, 4):
            row, col = d
            if row + i >= 4 or col + i >= 4:
                continue
            if board[row + i, col + i] == 0:
                board[row + i, col + i] = 1
                if evaluate(board) == 100:
                    board[row + i, col + i] = 0
                    return 50
                board[row + i, col + i] = -1
                if evaluate(board) == -100:
                    board[row + i, col + i] = 0
                    return -50
                board[row + i, col + i] = 0

    # Check for potential winning moves (2 in a row)
    # Rows
    for row in range(4):
        for col in range(4):
            if board[row, col] == 0:
                board[row, col] = 1
                if evaluate(board) == 50:
                    board[row, col] = 0
                    return 20
                board[row, col] = -1
                if evaluate(board) == -50:
                    board[row, col] = 0
                    return -20
                board[row, col] = 0

    # Columns
    for col in range(4):
        for row in range(4):
            if board[row, col] == 0:
                board[row, col] = 1
                if evaluate(board) == 50:
                    board[row, col] = 0
                    return 20
                board[row, col] = -1
                if evaluate(board) == -50:
                    board[row, col] = 0
                    return -20
                board[row, col] = 0

    # Diagonals
    for d in [(0, 0), (0, 3)]:
        for i in range(4):
            row, col = d
            if row + i >= 4 or col + i >= 4:
                continue
            if board[row + i, col + i] == 0:
                board[row + i, col + i] = 1
                if evaluate(board) == 50:
                    board[row + i, col + i] = 0
                    return 20
                board[row + i, col + i] = -1
                if evaluate(board) == -50:
                    board[row + i, col + i] = 0
                    return -20
                board[row + i, col + i] = 0

    # Count pieces
    player_pieces = np.count_nonzero(board == 1)
    opponent_pieces = np.count_nonzero(board == -1)
    return player_pieces - opponent_pieces
