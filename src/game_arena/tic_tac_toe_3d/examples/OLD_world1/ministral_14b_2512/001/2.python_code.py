
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Determines the next move for a 3D Tic Tac Toe game using minimax with alpha-beta pruning.

    Args:
        board: A 3x3x3 list of lists representing the game board. 0 = empty, 1 = player, -1 = opponent.

    Returns:
        A tuple (x, y, z) representing the coordinates of the chosen empty cell.
    """
    # Convert the board to a numpy array for easier manipulation
    board_np = np.array(board, dtype=int)

    # Find all empty cells
    empty_cells = np.argwhere(board_np == 0)

    # If there are no empty cells, return None (though this shouldn't happen in a valid game)
    if len(empty_cells) == 0:
        return (0, 0, 0)  # fallback, though game should be over

    # Use minimax with alpha-beta pruning to find the best move
    best_score = -float('inf')
    best_move = empty_cells[0]

    # We'll use a depth limit to prevent excessive computation
    depth_limit = 5

    for cell in empty_cells:
        x, y, z = cell
        board_np[x, y, z] = 1  # Assume player is 1
        score = minimax(board_np, depth_limit, -float('inf'), float('inf'), False)
        board_np[x, y, z] = 0  # Undo the move

        if score > best_score:
            best_score = score
            best_move = cell

    return tuple(best_move)

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, is_maximizing: bool) -> int:
    """
    Minimax algorithm with alpha-beta pruning for 3D Tic Tac Toe.

    Args:
        board: Current game board.
        depth: Current depth in the search tree.
        alpha: Best value that the maximizer can guarantee so far.
        beta: Best value that the minimizer can guarantee so far.
        is_maximizing: Whether the current player is the maximizer (player) or minimizer (opponent).

    Returns:
        The score of the current board position.
    """
    # Check if the game is over
    winner = check_winner(board)
    if winner != 0:
        if winner == 1:
            return 10 - depth  # Player wins, higher score
        else:
            return -10 + depth  # Opponent wins, lower score

    # Check if the board is full (draw)
    if np.all(board != 0):
        return 0

    if depth == 0:
        return evaluate_board(board)

    if is_maximizing:
        best_score = -float('inf')
        for cell in np.argwhere(board == 0):
            x, y, z = cell
            board[x, y, z] = 1
            score = minimax(board, depth - 1, alpha, beta, False)
            board[x, y, z] = 0
            best_score = max(score, best_score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score
    else:
        best_score = float('inf')
        for cell in np.argwhere(board == 0):
            x, y, z = cell
            board[x, y, z] = -1
            score = minimax(board, depth - 1, alpha, beta, True)
            board[x, y, z] = 0
            best_score = min(score, best_score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return best_score

def check_winner(board: np.ndarray) -> int:
    """
    Checks if there is a winner on the 3D Tic Tac Toe board.

    Args:
        board: Current game board.

    Returns:
        1 if player wins, -1 if opponent wins, 0 otherwise.
    """
    n = board.shape[0]

    # Check rows in each layer
    for layer in range(n):
        for row in range(n):
            for col in range(n - 2):
                if board[layer, row, col] != 0 and board[layer, row, col] == board[layer, row, col + 1] == board[layer, row, col + 2]:
                    return board[layer, row, col]

    # Check columns in each layer
    for layer in range(n):
        for row in range(n - 2):
            for col in range(n):
                if board[layer, row, col] != 0 and board[layer, row, col] == board[layer, row + 1, col] == board[layer, row + 2, col]:
                    return board[layer, row, col]

    # Check depth (layers) in each row
    for row in range(n):
        for col in range(n):
            for layer in range(n - 2):
                if board[layer, row, col] != 0 and board[layer, row, col] == board[layer + 1, row, col] == board[layer + 2, row, col]:
                    return board[layer, row, col]

    # Check depth (layers) in each column
    for row in range(n - 2):
        for col in range(n):
            for layer in range(n):
                if board[layer, row, col] != 0 and board[layer, row, col] == board[layer + 1, row + 1, col] == board[layer + 2, row + 2, col]:
                    return board[layer, row, col]

    # Check diagonals in each layer
    for layer in range(n):
        # Main diagonal
        if board[layer, 0, 0] != 0 and board[layer, 0, 0] == board[layer, 1, 1] == board[layer, 2, 2]:
            return board[layer, 0, 0]
        # Anti-diagonal
        if board[layer, 0, 2] != 0 and board[layer, 0, 2] == board[layer, 1, 1] == board[layer, 2, 0]:
            return board[layer, 0, 2]

    # Check 3D diagonals
    # Main 3D diagonal
    if board[0, 0, 0] != 0 and board[0, 0, 0] == board[1, 1, 1] == board[2, 2, 2]:
        return board[0, 0, 0]
    # Anti-3D diagonal
    if board[0, 0, 2] != 0 and board[0, 0, 2] == board[1, 1, 1] == board[2, 2, 0]:
        return board[0, 0, 2]
    # Other 3D diagonals
    if board[0, 2, 0] != 0 and board[0, 2, 0] == board[1, 1, 1] == board[2, 0, 2]:
        return board[0, 2, 0]
    if board[0, 2, 2] != 0 and board[0, 2, 2] == board[1, 1, 1] == board[2, 0, 0]:
        return board[0, 2, 2]

    return 0

def evaluate_board(board: np.ndarray) -> int:
    """
    Evaluates the current board position using a heuristic.

    Args:
        board: Current game board.

    Returns:
        A heuristic score for the current board position.
    """
    score = 0
    n = board.shape[0]

    # Count player and opponent pieces
    player_count = np.sum(board == 1)
    opponent_count = np.sum(board == -1)
    score += player_count - opponent_count

    # Check for potential winning moves (2 in a row)
    for layer in range(n):
        for row in range(n):
            for col in range(n - 2):
                if board[layer, row, col] == 1 and board[layer, row, col + 1] == 1 and board[layer, row, col + 2] == 0:
                    score += 5
                if board[layer, row, col] == -1 and board[layer, row, col + 1] == -1 and board[layer, row, col + 2] == 0:
                    score -= 5

    # Check for potential winning moves in columns
    for layer in range(n):
        for row in range(n - 2):
            for col in range(n):
                if board[layer, row, col] == 1 and board[layer, row + 1, col] == 1 and board[layer, row + 2, col] == 0:
                    score += 5
                if board[layer, row, col] == -1 and board[layer, row + 1, col] == -1 and board[layer, row + 2, col] == 0:
                    score -= 5

    # Check for potential winning moves in depth
    for row in range(n):
        for col in range(n):
            for layer in range(n - 2):
                if board[layer, row, col] == 1 and board[layer + 1, row, col] == 1 and board[layer + 2, row, col] == 0:
                    score += 5
                if board[layer, row, col] == -1 and board[layer + 1, row, col] == -1 and board[layer + 2, row, col] == 0:
                    score -= 5

    # Check for potential winning moves in diagonals
    for layer in range(n):
        if board[layer, 0, 0] == 1 and board[layer, 1, 1] == 1 and board[layer, 2, 2] == 0:
            score += 5
        if board[layer, 0, 0] == -1 and board[layer, 1, 1] == -1 and board[layer, 2, 2] == 0:
            score -= 5
        if board[layer, 0, 2] == 1 and board[layer, 1, 1] == 1 and board[layer, 2, 0] == 0:
            score += 5
        if board[layer, 0, 2] == -1 and board[layer, 1, 1] == -1 and board[layer, 2, 0] == 0:
            score -= 5

    # Check for potential 3D winning moves
    if board[0, 0, 0] == 1 and board[1, 1, 1] == 1 and board[2, 2, 2] == 0:
        score += 5
    if board[0, 0, 0] == -1 and board[1, 1, 1] == -1 and board[2, 2, 2] == 0:
        score -= 5
    if board[0, 0, 2] == 1 and board[1, 1, 1] == 1 and board[2, 2, 0] == 0:
        score += 5
    if board[0, 0, 2] == -1 and board[1, 1, 1] == -1 and board[2, 2, 0] == 0:
        score -= 5
    if board[0, 2, 0] == 1 and board[1, 1, 1] == 1 and board[2, 0, 2] == 0:
        score += 5
    if board[0, 2, 0] == -1 and board[1, 1, 1] == -1 and board[2, 0, 2] == 0:
        score -= 5
    if board[0, 2, 2] == 1 and board[1, 1, 1] == 1 and board[2, 0, 0] == 0:
        score += 5
    if board[0, 2, 2] == -1 and board[1, 1, 1] == -1 and board[2, 0, 0] == 0:
        score -= 5

    return score
