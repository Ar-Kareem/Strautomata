
import itertools
from functools import lru_cache
from typing import List, Tuple

# ----- Pre‑compute all winning lines (49 of them) -----
def generate_winning_lines() -> List[List[Tuple[int, int, int]]]:
    lines = []

    # Straight lines along each axis
    for i in range(3):
        for j in range(3):
            # along k
            lines.append([(i, j, k) for k in range(3)])
            # along j
            lines.append([(i, k, j) for k in range(3)])
            # along i
            lines.append([(k, i, j) for k in range(3)])

    # Face diagonals on each constant‑plane
    for i in range(3):
        # plane i = const (yz‑plane)
        lines.append([(i, t, t) for t in range(3)])
        lines.append([(i, t, 2 - t) for t in range(3)])
    for j in range(3):
        # plane j = const (xz‑plane)
        lines.append([(t, j, t) for t in range(3)])
        lines.append([(t, j, 2 - t) for t in range(3)])
    for k in range(3):
        # plane k = const (xy‑plane)
        lines.append([(t, t, k) for t in range(3)])
        lines.append([(t, 2 - t, k) for t in range(3)])

    # Space diagonals (4)
    lines.append([(t, t, t) for t in range(3)])
    lines.append([(t, t, 2 - t) for t in range(3)])
    lines.append([(t, 2 - t, t) for t in range(3)])
    lines.append([(2 - t, t, t) for t in range(3)])

    # Remove duplicates (some were added twice)
    unique = []
    seen = set()
    for line in lines:
        key = tuple(sorted(line))
        if key not in seen:
            seen.add(key)
            unique.append(line)
    return unique

WINNING_LINES = generate_winning_lines()


# ----- Helper functions -----
def check_win(board: List[List[List[int]]], player: int) -> bool:
    """Return True if 'player' occupies any winning line."""
    for line in WINNING_LINES:
        if all(board[i][j][k] == player for (i, j, k) in line):
            return True
    return False


def board_to_tuple(board: List[List[List[int]]]) -> Tuple[int, ...]:
    """Flatten the 3×3×3 board to a single immutable tuple."""
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))


def empty_cells(board: List[List[List[int]]]) -> List[Tuple[int, int, int]]:
    """Return a list of coordinates of all empty squares."""
    cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    cells.append((i, j, k))
    return cells


# ----- Minimax with memoisation and alpha‑beta pruning -----
def minimax(board: List[List[List[int]]], player: int,
            alpha: int = -2, beta: int = 2) -> int:
    """
    Return the minimax value from the viewpoint of the player 'player'
    (1 = our policy, -1 = opponent).
    """
    board_key = board_to_tuple(board)
    if board_key in _cache:
        return _cache[board_key]

    # Terminal positions
    if check_win(board, 1):
        _cache[board_key] = 1
        return 1
    if check_win(board, -1):
        _cache[board_key] = -1
        return -1

    empties = empty_cells(board)
    if not empties:                # Draw
        _cache[board_key] = 0
        return 0

    # Maximiser / Minimiser choice
    if player == 1:
        best = -2
        for (i, j, k) in empties:
            board[i][j][k] = 1
            val = minimax(board, -1, alpha, beta)
            board[i][j][k] = 0
            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break          # β‑cutoff
        _cache[board_key] = best
        return best
    else:   # player == -1
        best = 2
        for (i, j, k) in empties:
            board[i][j][k] = -1
            val = minimax(board, 1, alpha, beta)
            board[i][j][k] = 0
            if val < best:
                best = val
            beta = min(beta, best)
            if beta <= alpha:
                break          # α‑cutoff
        _cache[board_key] = best
        return best


# Cache dictionary used by minimax
_cache: dict = {}


# ----- Public policy function -----
def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Return the optimal (i, j, k) move for the current player (represented by 1)
    on the given board. The move is guaranteed to be legal.
    """
    # If board is already terminal, just return a dummy move (should never be called)
    empties = empty_cells(board)
    if not empties:
        raise ValueError("No legal moves left.")

    best_score = -2
    best_move = None

    for move in empties:
        i, j, k = move
        board[i][j][k] = 1                     # try our move
        score = minimax(board, -1, -2, 2)       # opponent to move
        board[i][j][k] = 0                     # undo

        if score > best_score:
            best_score = score
            best_move = move
            if best_score == 1:                # cannot do better than winning
                break

    # Fallback safety (should never happen)
    if best_move is None:
        best_move = empties[0]

    return best_move
