
import numpy as np
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    """
    Returns the next move for the current player (1) in a Connect 4 game.
    Uses a hybrid strategy of immediate win/block detection and minimax search with alpha-beta pruning.
    """
    # Check for immediate win or block
    immediate_move = check_immediate_wins(board)
    if immediate_move is not None:
        return immediate_move

    # Convert board to numpy array for easier manipulation
    np_board = np.array(board, dtype=int)

    # Get legal moves (columns with at least one 0)
    legal_moves = [col for col in range(7) if np_board[0][col] == 0]

    # If no immediate win/block, use minimax with heuristic evaluation
    if len(legal_moves) > 0:
        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        # Search depth (adjustable based on time constraints)
        depth = min(7, len(legal_moves) * 2)  # Cap at 7 or scale with legal moves

        for col in legal_moves:
            # Simulate dropping disc into column
            new_board = drop_disc(np_board.copy(), 1, col)
            score = minimax(new_board, depth, alpha, beta, -1)  # -1 is opponent

            if score > best_score:
                best_score = score
                best_move = col
            elif score == best_score and best_move is not None:
                # Randomly choose between equally good moves
                if random.random() < 0.5:
                    best_move = col

        return best_move if best_move is not None else random.choice(legal_moves)
    else:
        # Board is full (draw), return random column (shouldn't happen in valid game)
        return random.choice(range(7))

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, player: int) -> float:
    """
    Minimax algorithm with alpha-beta pruning to evaluate the best move.
    Returns the score for the current player (1) from the perspective of the maximizing player.
    """
    if depth == 0:
        return evaluate_board(board, player)

    legal_moves = [col for col in range(7) if board[0][col] == 0]
    if not legal_moves:
        return evaluate_board(board, player)

    if player == 1:  # Maximizing player (us)
        value = -float('inf')
        for col in legal_moves:
            new_board = drop_disc(board.copy(), player, col)
            value = max(value, minimax(new_board, depth - 1, alpha, beta, -1))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:  # Minimizing player (opponent)
        value = float('inf')
        for col in legal_moves:
            new_board = drop_disc(board.copy(), player, col)
            value = min(value, minimax(new_board, depth - 1, alpha, beta, 1))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

def evaluate_board(board: np.ndarray, player: int) -> float:
    """
    Heuristic evaluation function for the board.
    Scores higher for player 1 (us) and lower for player -1 (opponent).
    """
    score = 0
    opponent = -1 if player == 1 else 1

    # Check for immediate win
    if check_immediate_wins(board, player) is not None:
        return float('inf') if player == 1 else -float('inf')

    # Check for potential threats (3-in-a-row or 2-in-a-row)
    score += evaluate_potential_threats(board, player)
    score -= evaluate_potential_threats(board, opponent)

    # Center control (column 3 is most valuable)
    center_col = 3
    if board[0][center_col] == 0:
        score += 5  # Bonus for keeping center open

    # Disc count (more discs = better)
    disc_count = np.count_nonzero(board)
    score += disc_count * 0.1

    # Mobility (number of legal moves)
    legal_moves = np.count_nonzero(board[0] == 0)
    score += legal_moves * 0.5

    # Avoid opponent's mobility
    opponent_legal_moves = np.count_nonzero(board[0] == 0)
    score -= opponent_legal_moves * 0.3

    # Height advantage (our discs are higher than opponent's)
    for col in range(7):
        if board[0][col] == 0:
            height = np.sum(board[:, col] == 0)
            for row in range(6):
                if board[row][col] == player:
                    score += (6 - row) * 0.2
                elif board[row][col] == opponent:
                    score -= (6 - row) * 0.2

    return score

def evaluate_potential_threats(board: np.ndarray, player: int) -> float:
    """
    Evaluates potential threats (3-in-a-row or 2-in-a-row) for a player.
    Returns a score based on how close the player is to winning.
    """
    score = 0
    opponent = -1 if player == 1 else 1

    # Check horizontal threats
    for row in range(6):
        for col in range(4):
            window = board[row][col:col+4]
            if np.count_nonzero(window == player) == 3 and np.count_nonzero(window == 0) == 1:
                score += 10
            elif np.count_nonzero(window == player) == 2 and np.count_nonzero(window == 0) == 2:
                score += 5

    # Check vertical threats
    for col in range(7):
        for row in range(3):
            window = board[row:row+4, col]
            if np.count_nonzero(window == player) == 3 and np.count_nonzero(window == 0) == 1:
                score += 10
            elif np.count_nonzero(window == player) == 2 and np.count_nonzero(window == 0) == 2:
                score += 5

    # Check diagonal threats (top-left to bottom-right)
    for row in range(3):
        for col in range(4):
            window = board[row:row+4, col:col+4]
            if np.count_nonzero(window == player) == 3 and np.count_nonzero(window == 0) == 1:
                score += 10
            elif np.count_nonzero(window == player) == 2 and np.count_nonzero(window == 0) == 2:
                score += 5

    # Check diagonal threats (bottom-left to top-right)
    for row in range(3, 6):
        for col in range(4):
            window = board[row-3:row+1, col:col+4]
            if np.count_nonzero(window == player) == 3 and np.count_nonzero(window == 0) == 1:
                score += 10
            elif np.count_nonzero(window == player) == 2 and np.count_nonzero(window == 0) == 2:
                score += 5

    return score

def check_immediate_wins(board: np.ndarray, player: int = 1) -> int:
    """
    Checks if the current player can win immediately or if the opponent can win next turn.
    Returns the column index if a winning move exists, otherwise None.
    """
    opponent = -1 if player == 1 else 1
    for col in range(7):
        if board[0][col] == 0:  # Column is not full
            new_board = drop_disc(board.copy(), player, col)
            if check_win(new_board, player):
                return col
            elif player == -1 and check_win(new_board, opponent):
                return col  # Opponent's move would win next turn
    return None

def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won (4-in-a-row horizontally, vertically, or diagonally).
    """
    # Check horizontal locations
    for row in range(6):
        for col in range(4):
            if board[row][col] == board[row][col+1] == board[row][col+2] == board[row][col+3] == player:
                return True

    # Check vertical locations
    for col in range(7):
        for row in range(3):
            if board[row][col] == board[row+1][col] == board[row+2][col] == board[row+3][col] == player:
                return True

    # Check diagonal (top-left to bottom-right) locations
    for row in range(3):
        for col in range(4):
            if board[row][col] == board[row+1][col+1] == board[row+2][col+2] == board[row+3][col+3] == player:
                return True

    # Check diagonal (bottom-left to top-right) locations
    for row in range(3, 6):
        for col in range(4):
            if board[row][col] == board[row-1][col+1] == board[row-2][col+2] == board[row-3][col+3] == player:
                return True

    return False

def drop_disc(board: np.ndarray, player: int, col: int) -> np.ndarray:
    """
    Simulates dropping a disc into the given column and returns the new board.
    """
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            return board
    return board  # Shouldn't happen if col is legal
