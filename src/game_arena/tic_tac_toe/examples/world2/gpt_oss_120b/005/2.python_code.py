
import functools
from typing import List, Tuple

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def winner(board: List[List[int]]) -> int:
    """Return 1 if player wins, -1 if opponent wins, 0 otherwise."""
    # rows and columns
    for i in range(4):
        row_sum = sum(board[i])
        col_sum = sum(board[r][i] for r in range(4))
        if row_sum == 4:
            return 1
        if row_sum == -4:
            return -1
        if col_sum == 4:
            return 1
        if col_sum == -4:
            return -1

    # main diagonal
    diag1 = sum(board[i][i] for i in range(4))
    if diag1 == 4:
        return 1
    if diag1 == -4:
        return -1

    # anti‑diagonal
    diag2 = sum(board[i][3 - i] for i in range(4))
    if diag2 == 4:
        return 1
    if diag2 == -4:
        return -1

    return 0


def board_to_key(board: List[List[int]]) -> Tuple[int, ...]:
    """Flatten the board to a hashable tuple."""
    return tuple(cell for row in board for cell in row)


# ----------------------------------------------------------------------
# Minimax with memoisation and alpha‑beta pruning
# ----------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def minimax_cached(key: Tuple[int, ...], player: int, alpha: int, beta: int) -> int:
    """
    Return the minimax value for the position described by `key`
    when `player` (1 or -1) is to move.
    """
    # reconstruct board for terminal check
    board = [list(key[i*4:(i+1)*4]) for i in range(4)]

    w = winner(board)
    if w != 0:
        # a win for player 1 is +1, win for -1 is -1
        return w

    if all(cell != 0 for cell in key):
        # draw
        return 0

    if player == 1:          # maximizing player
        max_eval = -2
        for idx, val in enumerate(key):
            if val == 0:
                new_key = list(key)
                new_key[idx] = 1
                eval = minimax_cached(tuple(new_key), -1, alpha, beta)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
        return max_eval
    else:                    # minimizing player (opponent)
        min_eval = 2
        for idx, val in enumerate(key):
            if val == 0:
                new_key = list(key)
                new_key[idx] = -1
                eval = minimax_cached(tuple(new_key), 1, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
        return min_eval


def minimax(board: List[List[int]], player: int) -> int:
    """Wrapper that starts the cached minimax with wide bounds."""
    key = board_to_key(board)
    return minimax_cached(key, player, -2, 2)


# ----------------------------------------------------------------------
# Public policy function
# ----------------------------------------------------------------------
def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the best legal move for player 1 on a 4x4 Tic‑Tac‑Toe board.
    Returns a (row, col) tuple.
    """
    best_score = -2
    best_move = None

    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1  # try move
                score = minimax(board, -1)  # opponent to move
                board[r][c] = 0  # undo

                if score > best_score:
                    best_score = score
                    best_move = (r, c)
                    # Immediate win can be returned at once
                    if best_score == 1:
                        return best_move

    # If no winning move, best_move is guaranteed to be set (board not full)
    return best_move
