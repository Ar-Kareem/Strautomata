
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Returns the best move for the current player (1) in a 4x4 Tic Tac Toe game.

    Args:
        board: 4x4 list of lists where 0 is empty, 1 is player, -1 is opponent.

    Returns:
        Tuple of (row, column) for the best move.
    """
    # Convert to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)

    # Check if the game is already won or drawn
    if is_terminal(board_np):
        # If it's a win for the opponent, return a random move (shouldn't happen in proper play)
        if np.any(board_np == -1 * np.ones((4, 4))):
            return (np.random.randint(4), np.random.randint(4))
        return (0, 0)  # Shouldn't reach here if game is properly played

    # Get all possible moves
    moves = [(i, j) for i in range(4) for j in range(4) if board_np[i, j] == 0]

    # If no moves left (shouldn't happen), return a default
    if not moves:
        return (0, 0)

    # Evaluate each possible move using minimax with alpha-beta pruning
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    for move in moves:
        # Make the move
        board_np[move] = 1
        score = minimax(board_np, 0, alpha, beta, True)
        board_np[move] = 0  # Undo the move

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """
    Minimax algorithm with alpha-beta pruning for evaluating board positions.
    """
    if is_terminal(board):
        return evaluate_board(board)

    if maximizing_player:
        max_eval = -float('inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = 1
                    eval = minimax(board, depth + 1, alpha, beta, False)
                    board[i, j] = 0
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = -1
                    eval = minimax(board, depth + 1, alpha, beta, True)
                    board[i, j] = 0
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return min_eval

def is_terminal(board: np.ndarray) -> bool:
    """
    Check if the game is in a terminal state (win or draw).
    """
    # Check rows, columns, and diagonals for a winner
    for i in range(4):
        if np.all(board[i, :] == 1) or np.all(board[:, i] == 1):
            return True
        if np.all(board[i, :] == -1) or np.all(board[:, i] == -1):
            return True

    # Check diagonals
    if np.all(np.diag(board) == 1) or np.all(np.diag(np.fliplr(board)) == 1):
        return True
    if np.all(np.diag(board) == -1) or np.all(np.diag(np.fliplr(board)) == -1):
        return True

    # Check if the board is full
    if np.all(board != 0):
        return True

    return False

def evaluate_board(board: np.ndarray) -> float:
    """
    Evaluate the board position from the perspective of player 1.
    Higher values are better for player 1, lower for player -1.
    """
    # Check for immediate wins/losses
    if np.any(board == 1 * np.ones((4, 4))):
        return 1000
    if np.any(board == -1 * np.ones((4, 4))):
        return -1000

    # Check rows, columns, and diagonals for potential wins
    score = 0

    # Check rows
    for i in range(4):
        row = board[i, :]
        if np.sum(row == 1) == 3:
            score += 10
        if np.sum(row == -1) == 3:
            score -= 10

    # Check columns
    for j in range(4):
        col = board[:, j]
        if np.sum(col == 1) == 3:
            score += 10
        if np.sum(col == -1) == 3:
            score -= 10

    # Check diagonals
    diag1 = np.diag(board)
    diag2 = np.diag(np.fliplr(board))
    if np.sum(diag1 == 1) == 3:
        score += 10
    if np.sum(diag1 == -1) == 3:
        score -= 10
    if np.sum(diag2 == 1) == 3:
        score += 10
    if np.sum(diag2 == -1) == 3:
        score -= 10

    # Center control bonus
    if board[1, 1] == 1:
        score += 5
    if board[1, 1] == -1:
        score -= 5

    # Corner control bonus
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for (i, j) in corners:
        if board[i, j] == 1:
            score += 3
        if board[i, j] == -1:
            score -= 3

    # Edge control bonus
    edges = [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)]
    for (i, j) in edges:
        if board[i, j] == 1:
            score += 1
        if board[i, j] == -1:
            score -= 1

    return score
