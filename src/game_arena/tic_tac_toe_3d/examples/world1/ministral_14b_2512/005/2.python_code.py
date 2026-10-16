
import numpy as np
import random
import time

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Hybrid minimax policy with heuristic evaluation for 3D Tic Tac Toe.
    Returns the best move (i, j, k) as a tuple.
    """
    start_time = time.time()
    best_move = None
    best_score = -np.inf

    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)

    # Check if the current player can win immediately
    immediate_win = find_immediate_win(board_np, 1)
    if immediate_win:
        return immediate_win

    # Check if the opponent can win immediately and block them
    opponent_immediate_win = find_immediate_win(board_np, -1)
    if opponent_immediate_win:
        return opponent_immediate_win

    # If no immediate win/block, use minimax with alpha-beta pruning
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i, j, k] == 0:
                    # Simulate the move
                    board_np[i, j, k] = 1
                    score = minimax(board_np, -1, -np.inf, np.inf, start_time + 0.9)  # Leave 100ms for other moves
                    board_np[i, j, k] = 0  # Undo the move

                    if score > best_score:
                        best_score = score
                        best_move = (i, j, k)

    # If no optimal move found (e.g., time ran out), return a random legal move
    if best_move is None:
        legal_moves = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board_np[i, j, k] == 0]
        return random.choice(legal_moves)

    return best_move

def minimax(board: np.ndarray, player: int, alpha: float, beta: float, time_limit: float) -> float:
    """
    Minimax with alpha-beta pruning for 3D Tic Tac Toe.
    Returns the score of the best move for the current player.
    """
    if time.time() > time_limit:
        return -np.inf if player == 1 else np.inf

    # Check if the game is over
    game_result = check_game_over(board)
    if game_result == 1:
        return 10 - get_depth(board)  # Higher score for deeper wins
    elif game_result == -1:
        return -10 + get_depth(board)  # Lower score for deeper losses
    elif game_result == 0:
        return 0  # Draw

    # If it's the opponent's turn, minimize their score
    if player == -1:
        best_score = np.inf
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i, j, k] == 0:
                        board[i, j, k] = -1
                        score = minimax(board, 1, alpha, beta, time_limit)
                        board[i, j, k] = 0
                        best_score = min(score, best_score)
                        alpha = min(alpha, score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
        return best_score
    else:
        # If it's our turn, maximize our score
        best_score = -np.inf
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i, j, k] == 0:
                        board[i, j, k] = 1
                        score = minimax(board, -1, alpha, beta, time_limit)
                        board[i, j, k] = 0
                        best_score = max(score, best_score)
                        beta = max(beta, score)
                        if beta >= alpha:
                            break
                if beta >= alpha:
                    break
        return best_score

def get_depth(board: np.ndarray) -> int:
    """
    Returns the depth of the current board state (number of empty cells).
    """
    return np.sum(board == 0)

def check_game_over(board: np.ndarray) -> int:
    """
    Checks if the game is over (win/loss/draw).
    Returns 1 if current player wins, -1 if opponent wins, 0 if draw.
    """
    # Check all rows, columns, and depth layers
    for i in range(3):
        for j in range(3):
            if np.all(board[i, j, :] == 1):
                return 1
            if np.all(board[i, :, k] == 1):
                return 1
            if np.all(board[:, j, k] == 1):
                return 1
            if np.all(board[i, j, :] == -1):
                return -1
            if np.all(board[i, :, k] == -1):
                return -1
            if np.all(board[:, j, k] == -1):
                return -1

    # Check all 4-space diagonals
    if np.all([board[i, i, i] == 1 for i in range(3)]):
        return 1
    if np.all([board[i, i, 2 - i] == 1 for i in range(3)]):
        return 1
    if np.all([board[i, 2 - i, i] == 1 for i in range(3)]):
        return 1
    if np.all([board[i, 2 - i, 2 - i] == 1 for i in range(3)]):
        return 1
    if np.all([board[i, i, i] == -1 for i in range(3)]):
        return -1
    if np.all([board[i, i, 2 - i] == -1 for i in range(3)]):
        return -1
    if np.all([board[i, 2 - i, i] == -1 for i in range(3)]):
        return -1
    if np.all([board[i, 2 - i, 2 - i] == -1 for i in range(3)]):
        return -1

    # Check if the board is full (draw)
    if get_depth(board) == 0:
        return 0

    return None  # Game is not over yet

def find_immediate_win(board: np.ndarray, player: int) -> tuple[int, int, int]:
    """
    Finds an immediate winning move for the given player.
    Returns the move (i, j, k) if found, otherwise None.
    """
    # Check all rows, columns, and depth layers
    for i in range(3):
        for j in range(3):
            if np.sum(board[i, j, :] == 0) == 1 and np.sum(board[i, j, :] == player) == 2:
                k = np.where(board[i, j, :] == 0)[0][0]
                return (i, j, k)
            if np.sum(board[i, :, k] == 0) == 1 and np.sum(board[i, :, k] == player) == 2:
                j = np.where(board[i, :, k] == 0)[0][0]
                return (i, j, k)
            if np.sum(board[:, j, k] == 0) == 1 and np.sum(board[:, j, k] == player) == 2:
                i = np.where(board[:, j, k] == 0)[0][0]
                return (i, j, k)

    # Check all 4-space diagonals
    for i in range(3):
        diagonal = [board[i, i, i], board[i, i, 2 - i], board[i, 2 - i, i], board[i, 2 - i, 2 - i]]
        if np.sum(diagonal == 0) == 1 and np.sum(diagonal == player) == 2:
            # Find the empty cell in the diagonal
            if diagonal[0] == 0:
                return (i, i, i)
            elif diagonal[1] == 0:
                return (i, i, 2 - i)
            elif diagonal[2] == 0:
                return (i, 2 - i, i)
            elif diagonal[3] == 0:
                return (i, 2 - i, 2 - i)

    return None  # No immediate win found
