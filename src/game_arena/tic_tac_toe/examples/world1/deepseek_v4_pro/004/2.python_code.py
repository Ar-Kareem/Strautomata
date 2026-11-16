
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the optimal next move (row, col) for the AI player (represented by 1).
    Uses immediate win/block checks and minimax with alpha-beta pruning.
    """
    # 1. Check for immediate winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                if _check_win(board, 1):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # 2. Block opponent's immediate winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = -1
                if _check_win(board, -1):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # 3. Take center if available (optimal first move)
    if board[1][1] == 0:
        return (1, 1)

    # 4. Use minimax with alpha-beta pruning to find the best move
    best_score = -math.inf
    best_move = (0, 0)  # default fallback (will be updated)
    alpha = -math.inf
    beta = math.inf

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                score = _minimax(board, 0, False, alpha, beta)
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
                alpha = max(alpha, best_score)

    return best_move


def _check_win(board: list[list[int]], player: int) -> bool:
    """Returns True if the given player has three in a row."""
    # Rows and columns
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):
            return True
        if all(board[j][i] == player for j in range(3)):
            return True
    # Diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False


def _minimax(board: list[list[int]], depth: int, is_maximizing: bool,
             alpha: float, beta: float) -> float:
    """Minimax with alpha-beta pruning. Returns score from the perspective of the AI (player 1)."""
    # Terminal states
    if _check_win(board, 1):
        return 10 - depth  # Prefer quicker wins
    if _check_win(board, -1):
        return depth - 10  # Prefer slower losses
    if all(board[r][c] != 0 for r in range(3) for c in range(3)):
        return 0  # Draw

    if is_maximizing:
        max_eval = -math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1
                    eval = _minimax(board, depth + 1, False, alpha, beta)
                    board[r][c] = 0
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1
                    eval = _minimax(board, depth + 1, True, alpha, beta)
                    board[r][c] = 0
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return min_eval
