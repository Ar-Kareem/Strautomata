
import numpy as np

def is_terminal(board: list[list[int]]) -> bool:
    """Check if the game is over (win or tie)."""
    board_np = np.array(board)

    # Check rows
    for row in board_np:
        if np.all(row == 1) or np.all(row == -1):
            return True

    # Check columns
    for col in range(3):
        if np.all(board_np[:, col] == 1) or np.all(board_np[:, col] == -1):
            return True

    # Check diagonals
    if np.all(np.diag(board_np) == 1) or np.all(np.diag(board_np) == -1):
        return True
    if np.all(np.diag(np.fliplr(board_np)) == 1) or np.all(np.diag(np.fliplr(board_np)) == -1):
        return True

    # Check if the board is full
    if np.all(board_np != 0):
        return True

    return False

def evaluate(board: list[list[int]], player: int) -> int:
    """Evaluate the board for the given player.
    Returns:
        10 if player wins,
        -10 if opponent wins,
        0 if it's a tie or game continues.
    """
    board_np = np.array(board)

    # Check rows
    for row in board_np:
        if np.all(row == player):
            return 10
        if np.all(row == -player):
            return -10

    # Check columns
    for col in range(3):
        if np.all(board_np[:, col] == player):
            return 10
        if np.all(board_np[:, col] == -player):
            return -10

    # Check diagonals
    if np.all(np.diag(board_np) == player):
        return 10
    if np.all(np.diag(board_np) == -player):
        return -10
    if np.all(np.diag(np.fliplr(board_np)) == player):
        return 10
    if np.all(np.diag(np.fliplr(board_np)) == -player):
        return -10

    # If no winner, return 0
    return 0

def minimax(board: list[list[int]], depth: int, is_maximizing: bool, alpha: float, beta: float) -> tuple[int, int]:
    """Minimax algorithm with alpha-beta pruning to find the best move."""
    board_np = np.array(board)
    if is_terminal(board):
        return evaluate(board, 1), None  # Assuming player 1 is me

    if is_maximizing:
        best_score = -float('inf')
        best_move = None
        for i in range(3):
            for j in range(3):
                if board_np[i, j] == 0:
                    board_np[i, j] = 1
                    score, _ = minimax(board.tolist(), depth + 1, False, alpha, beta)
                    board_np[i, j] = 0
                    if score > best_score:
                        best_score = score
                        best_move = (i, j)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return best_score, best_move
    else:
        best_score = float('inf')
        best_move = None
        for i in range(3):
            for j in range(3):
                if board_np[i, j] == 0:
                    board_np[i, j] = -1
                    score, _ = minimax(board.tolist(), depth + 1, True, alpha, beta)
                    board_np[i, j] = 0
                    if score < best_score:
                        best_score = score
                        best_move = (i, j)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return best_score, best_move

def policy(board: list[list[int]]) -> tuple[int, int]:
    """Determine the best move for player 1 (me) using minimax with alpha-beta pruning."""
    best_score = -float('inf')
    best_move = None
    board_np = np.array(board)

    for i in range(3):
        for j in range(3):
            if board_np[i, j] == 0:
                board_np[i, j] = 1
                score, _ = minimax(board.tolist(), 0, False, -float('inf'), float('inf'))
                board_np[i, j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)

    return best_move
