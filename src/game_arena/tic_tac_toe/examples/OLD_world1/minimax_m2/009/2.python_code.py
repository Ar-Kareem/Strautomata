
"""
Tic‑Tac‑Toe (3×3) policy for player 1.

The board is a 3×3 list‑of‑lists containing:
    0 – empty cell
    1 – player 1 (our piece)
   -1 – player ‑1 (opponent)

The function ``policy(board)`` must return a tuple (row, col) with 0‑based
indices indicating the cell where player 1 should move.

The implementation uses a complete minimax search with alpha‑beta pruning
(implicit because the game tree is tiny) and memoisation, guaranteeing
optimal play – the move never loses and wins whenever it is possible.
"""

from functools import lru_cache
from typing import List, Tuple, Iterable, Dict

# ----------------------------------------------------------------------
# Helper utilities that work on a flattened 9‑element tuple representation
# ----------------------------------------------------------------------
def _board_to_tuple(board: List[List[int]]) -> Tuple[int, ...]:
    """Convert a 3×3 list of lists to a 9‑element tuple for hashing."""
    return tuple(cell for row in board for cell in row)


def _empty_positions(state: Tuple[int, ...]) -> Iterable[Tuple[int, int]]:
    """Yield the (row, col) coordinates of empty cells in a flattened board."""
    for idx, val in enumerate(state):
        if val == 0:
            yield (idx // 3, idx % 3)


def _place(state: Tuple[int, ...], i: int, j: int, player: int) -> Tuple[int, ...]:
    """Return a new state with ``player`` placed at (i, j)."""
    idx = i * 3 + j
    lst = list(state)
    lst[idx] = player
    return tuple(lst)


def _check_winner(state: Tuple[int, ...]) -> None:
    """
    Determine the game result for a given board state.

    Returns:
        1  – player 1 has three in a row
       -1  – player ‑1 has three in a row
        0  – draw (board full, no winner)
        None – game still in progress
    """
    # rows
    for i in range(3):
        start = i * 3
        row = state[start:start + 3]
        if row[0] != 0 and row[0] == row[1] == row[2]:
            return row[0]
        col = (state[i], state[i + 3], state[i + 6])
        if col[0] != 0 and col[0] == col[1] == col[2]:
            return col[0]

    # diagonals
    diag1 = (state[0], state[4], state[8])
    if diag1[0] != 0 and diag1[0] == diag1[1] == diag1[2]:
        return diag1[0]
    diag2 = (state[2], state[4], state[6])
    if diag2[0] != 0 and diag2[0] == diag2[1] == diag2[2]:
        return diag2[0]

    # draw?
    if 0 not in state:
        return 0
    return None


# ----------------------------------------------------------------------
# Minimax with memoisation (returns 1 = win, 0 = draw, -1 = loss)
# ----------------------------------------------------------------------
@lru_cache(maxsize=None)
def _minimax(state: Tuple[int, ...], player: int) -> int:
    """
    Minimax evaluation from the perspective of ``player``.

    ``player`` is either 1 (maximiser) or -1 (minimiser).
    The function returns:
        1 – the player to move can force a win
        0 – forced draw
       -1 – loss against optimal play
    """
    result = _check_winner(state)
    if result is not None:
        # Terminal state: just map the winner to a numeric value.
        if result == 1:
            return 1
        if result == -1:
            return -1
        return 0  # draw

    if player == 1:
        best = -2  # lower than the worst possible score
        for i, j in _empty_positions(state):
            new_state = _place(state, i, j, player)
            score = _minimax(new_state, -player)
            if score > best:
                best = score
                if best == 1:          # cannot do better than a win
                    break
        return best
    else:
        best = 2   # higher than the worst possible score for the maximiser
        for i, j in _empty_positions(state):
            new_state = _place(state, i, j, player)
            score = _minimax(new_state, -player)
            if score < best:
                best = score
                if best == -1:         # opponent cannot avoid losing
                    break
        return best


# ----------------------------------------------------------------------
# Main public API
# ----------------------------------------------------------------------
def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return the best move for player 1 on the given 3×3 Tic‑Tac‑Toe board.

    Parameters
    ----------
    board : List[List[int]]
        3×3 grid containing 0 (empty), 1 (our piece) and -1 (opponent).

    Returns
    -------
    (row, col) : tuple[int, int]
        0‑based coordinates of the cell where player 1 should move.
    """
    # Basic validation – not strictly required but guards against misuse.
    if (
        not isinstance(board, list)
        or len(board) != 3
        or any(not isinstance(row, list) or len(row) != 3 for row in board)
    ):
        raise ValueError("Board must be a 3×3 list of lists containing 0, 1, -1.")

    state = _board_to_tuple(board)

    # Search order – centre first, then corners, then edges.
    # This also yields a deterministic move when several equally good options exist.
    move_priority: List[Tuple[int, int]] = [
        (1, 1),
        (0, 0), (0, 2), (2, 0), (2, 2),
        (0, 1), (1, 0), (1, 2), (2, 1),
    ]

    best_score = -2
    best_move: Tuple[int, int] | None = None

    for i, j in move_priority:
        if board[i][j] != 0:
            continue
        # Simulate our move and evaluate the resulting state.
        new_state = _place(state, i, j, player=1)
        score = _minimax(new_state, player=-1)  # opponent to move next
        if score > best_score:
            best_score = score
            best_move = (i, j)
            # Winning move found – we can stop early.
            if best_score == 1:
                break

    # If the board is already full (should not happen during normal play)
    # we return a dummy coordinate.
    if best_move is None:
        best_move = (0, 0)

    return best_move
