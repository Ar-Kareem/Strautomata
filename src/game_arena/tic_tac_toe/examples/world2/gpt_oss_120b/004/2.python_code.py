
import functools
from typing import List, Tuple

# ---------- Helper functions ----------

def check_winner(board: List[List[int]]) -> None:
    """Return 1 if we win, -1 if opponent wins, None otherwise."""
    # rows and columns
    for i in range(4):
        row_sum = sum(board[i][j] for j in range(4))
        if row_sum == 4:
            return 1
        if row_sum == -4:
            return -1
        col_sum = sum(board[j][i] for j in range(4))
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

    return None


def board_to_key(board: List[List[int]]) -> Tuple[int, ...]:
    """Flatten the 4×4 board into a hashable tuple."""
    return tuple(cell for row in board for cell in row)


def key_to_board(key: Tuple[int, ...]) -> List[List[int]]:
    """Restore a 4×4 board from the flattened tuple."""
    return [list(key[i * 4:(i + 1) * 4]) for i in range(4)]


# ---------- Minimax with memoisation ----------

@functools.lru_cache(maxsize=None)
def minimax(key: Tuple[int, ...], player: int) -> int:
    """
    Return the game value from the viewpoint of player 1.
    player == 1  → our turn in the simulated node
    player == -1 → opponent's turn
    """
    board = key_to_board(key)

    winner = check_winner(board)
    if winner is not None:          # a player has already won
        return winner
    if all(cell != 0 for cell in key):  # board full → draw
        return 0

    # Alpha‑beta style pruning via simple bounds
    if player == 1:
        best = -2  # worse than the worst possible score
        for idx, cell in enumerate(key):
            if cell == 0:
                new_key = list(key)
                new_key[idx] = 1
                score = minimax(tuple(new_key), -1)
                if score > best:
                    best = score
                    if best == 1:          # cannot do better
                        break
        return best
    else:
        best = 2   # better than the best possible opponent score
        for idx, cell in enumerate(key):
            if cell == 0:
                new_key = list(key)
                new_key[idx] = -1
                score = minimax(tuple(new_key), 1)
                if score < best:
                    best = score
                    if best == -1:         # opponent cannot do worse
                        break
        return best


# ---------- Public policy function ----------

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the optimal move for player 1 on a 4×4 Tic‑Tac‑Toe board.
    The returned (row, col) is guaranteed to be empty.
    """
    key = board_to_key(board)

    best_score = -2
    best_move = None

    for idx, cell in enumerate(key):
        if cell == 0:
            new_key = list(key)
            new_key[idx] = 1
            score = minimax(tuple(new_key), -1)   # opponent to move next
            if score > best_score:
                best_score = score
                best_move = idx
                if best_score == 1:               # winning move found
                    break

    # Fallback – should never happen because at least one empty cell exists
    if best_move is None:
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return (i, j)

    row, col = divmod(best_move, 4)
    return (row, col)
