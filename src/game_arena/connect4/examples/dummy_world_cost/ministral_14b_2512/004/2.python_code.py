
import numpy as np
import time

def policy(board: list[list[int]]) -> int:
    """
    Hybrid Connect 4 policy combining immediate win/block checks, minimax with alpha-beta pruning,
    and heuristic-based evaluation for smart moves.
    """
    start_time = time.time()
    max_depth = 4  # Default depth for minimax
    time_left = 1.0 - (time.time() - start_time)

    # Convert board to numpy array for easier manipulation
    np_board = np.array(board, dtype=int)

    # Check for immediate win or block opponent
    for col in range(7):
        if is_legal(np_board, col):
            new_board = drop_disc(np_board.copy(), col, 1)
            if evaluate_board(new_board, 1) >= 4:  # Immediate win
                return col
            new_board = drop_disc(np_board.copy(), col, -1)
            if evaluate_board(new_board, -1) >= 4:  # Block opponent
                return col

    # If no immediate win/block, use minimax with alpha-beta pruning
    if time_left > 0.5:  # Adjust depth if time allows
        max_depth = min(6, int(time_left * 2))  # Cap at 6 for safety
    best_col = -1
    best_score = -float('inf')

    for col in range(7):
        if is_legal(np_board, col):
            new_board = drop_disc(np_board.copy(), col, 1)
            score = minimax(new_board, max_depth, -float('inf'), float('inf'), -1)
            if score > best_score:
                best_score = score
                best_col = col

    if best_col != -1:
        return best_col

    # Fallback: Heuristic-based evaluation if minimax is too slow
    heuristic_scores = []
    for col in range(7):
        if is_legal(np_board, col):
            new_board = drop_disc(np_board.copy(), col, 1)
            score = heuristic_evaluation(new_board, 1)
            heuristic_scores.append(score)
        else:
            heuristic_scores.append(-float('inf'))

    # Prefer center columns and avoid opponent's threats
    center_bias = np.array([0, 1, 2, 3, 2, 1, 0])  # Heuristic: center columns are more valuable
    weighted_scores = np.array(heuristic_scores) * center_bias
    best_heuristic_col = np.argmax(weighted_scores)

    # Ensure the move is legal (should always be true due to earlier checks)
    if is_legal(np_board, best_heuristic_col):
        return best_heuristic_col

    # Final fallback: random move among top 3 heuristic columns
    top_cols = np.argsort(weighted_scores)[-3:][::-1]  # Top 3 columns
    return np.random.choice(top_cols)

def is_legal(board: np.ndarray, col: int) -> bool:
    """Check if a column is legal (not full)."""
    return board[0, col] == 0

def drop_disc(board: np.ndarray, col: int, player: int) -> np.ndarray:
    """Drop a disc into a column and return the new board."""
    for row in range(6):
        if board[row, col] == 0:
            board[row, col] = player
            return board
    return board  # Should not happen if is_legal is correct

def evaluate_board(board: np.ndarray, player: int) -> int:
    """Evaluate the board for the given player (1 or -1). Returns the length of the longest line."""
    directions = [
        (0, 1),  # Horizontal
        (1, 0),   # Vertical
        (1, 1),   # Diagonal down-right
        (1, -1)   # Diagonal down-left
    ]

    max_line = 0
    for row in range(6):
        for col in range(7):
            if board[row, col] == player:
                for dr, dc in directions:
                    line_length = 1
                    # Check in positive direction
                    r, c = row + dr, col + dc
                    while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == player:
                        line_length += 1
                        r, c = r + dr, c + dc
                    # Check in negative direction
                    r, c = row - dr, col - dc
                    while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == player:
                        line_length += 1
                        r, c = r - dr, c - dc
                    max_line = max(max_line, line_length)
    return max_line

def heuristic_evaluation(board: np.ndarray, player: int) -> int:
    """Heuristic evaluation of the board (prioritizes lines of 3, 2, and center control)."""
    directions = [
        (0, 1),  # Horizontal
        (1, 0),   # Vertical
        (1, 1),   # Diagonal down-right
        (1, -1)   # Diagonal down-left
    ]

    score = 0
    for row in range(6):
        for col in range(7):
            if board[row, col] == player:
                for dr, dc in directions:
                    line_length = 1
                    # Check in positive direction
                    r, c = row + dr, col + dc
                    while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == player:
                        line_length += 1
                        r, c = r + dr, c + dc
                    # Check in negative direction
                    r, c = row - dr, col - dc
                    while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == player:
                        line_length += 1
                        r, c = r - dr, c - dc
                    # Score based on line length (3 > 2, etc.)
                    if line_length == 3:
                        score += 10
                    elif line_length == 2:
                        score += 2
    # Bonus for center columns (3 or 4)
    center_cols = [3, 4]
    for col in center_cols:
        if board[0, col] == 0:  # Column is not full
            for row in range(6):
                if board[row, col] == player:
                    score += 5
    return score

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, player: int) -> int:
    """Minimax with alpha-beta pruning to evaluate future moves."""
    if depth == 0 or evaluate_board(board, player) >= 4:
        return heuristic_evaluation(board, player)

    if player == 1:  # Current player's turn
        max_eval = -float('inf')
        for col in range(7):
            if is_legal(board, col):
                new_board = drop_disc(board.copy(), col, player)
                eval = minimax(new_board, depth - 1, alpha, beta, -1)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
        return max_eval
    else:  # Opponent's turn
        min_eval = float('inf')
        for col in range(7):
            if is_legal(board, col):
                new_board = drop_disc(board.copy(), col, player)
                eval = minimax(new_board, depth - 1, alpha, beta, 1)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
        return min_eval
