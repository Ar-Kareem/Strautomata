
import math
from copy import deepcopy
from typing import List, Tuple

# Winning lines
WIN_LINES = [
    [(0, 0), (0, 1), (0, 2)],  # rows
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],  # columns
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],  # main diagonal
    [(0, 2), (1, 1), (2, 0)],  # anti diagonal
]

def evaluate(board: List[List[int]]) -> int:
    """Return +10 for our win, -10 for opponent win, 0 otherwise."""
    # Check rows, columns, diagonals for three 1s
    for line in WIN_LINES:
        if all(board[r][c] == 1 for (r, c) in line):
            return 10
        # Check for opponent's three -1s
        if all(board[r][c] == -1 for (r, c) in line):
            return -10
    return 0

def move_priority(pos: Tuple[int, int]) -> int:
    """Heuristic priority: center (0,0), corners (1), edges (2)."""
    if pos == (1, 1):
        return 0
    elif pos in {(0, 0), (0, 2), (2, 0), (2, 2)}:
        return 1
    else:  # edges
        return 2

def minimax(board: List[List[int]], depth: int, maximizing: bool,
           alpha: float, beta: float) -> int:
    """Recursive minimax with alpha‑beta pruning."""
    score = evaluate(board)
    if score != 0:
        return score

    # No more moves (draw)
    if not any(cell == 0 for row in board for cell in row):
        return 0

    best_score = -math.inf if maximizing else math.inf
    # Generate moves in heuristic order
    empty_moves = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    sorted_moves = sorted(empty_moves, key=move_priority)

    for move in sorted_moves:
        new_board = deepcopy(board)
        new_board[move[0]][move[1]] = 1 if maximizing else -1
        score = minimax(new_board, depth + 1, not maximizing, alpha, beta)
        if maximizing:
            if score > best_score:
                best_score = score
            alpha = max(alpha, score)
        else:
            if score < best_score:
                best_score = score
            beta = min(beta, score)

        if beta <= alpha:
            break  # prune

    return best_score

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """Return the best legal (row, col) move for the current player."""
    best_move = None
    best_score = -math.inf
    for move in minimax_moves(board):
        new_board = deepcopy(board)
        new_board[move[0]][move[1]] = 1
        score = minimax(new_board, 0, False, -math.inf, math.inf)
        if score > best_score:
            best_score = score
            best_move = move
        # We continue exploring only if the ordering gives us a chance
        # to improve; ties are broken by earlier moves.

    # The board is guaranteed to have at least one empty cell in the arena.
    return best_move

def minimax_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    """Utility to generate and sort legal moves using the move priority."""
    moves = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    return sorted(moves, key=move_priority)

# Export the required function
__all__ = ["policy"]
