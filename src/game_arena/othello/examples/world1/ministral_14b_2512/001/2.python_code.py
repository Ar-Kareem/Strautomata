
import numpy as np
from typing import List, Tuple

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello policy that prioritizes corners, edges, and high-flip moves.
    Returns a legal move in algebraic notation (e.g., "d3") or "pass" if no moves are available.
    """
    # Directions: 8 possible (horizontal, vertical, diagonal)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]

    # Get all empty cells (0,0)
    empty_cells = np.argwhere(you == 0 & opponent == 0)

    # If no moves available, pass
    if len(empty_cells) == 0:
        return "pass"

    # Evaluate all possible moves
    best_moves = []
    best_score = -1
    best_flips = -1

    for cell in empty_cells:
        r, c = cell
        flips = 0
        flipped = []

        # Check all 8 directions for flips
        for dr, dc in directions:
            # Count flips in this direction
            flip_count = 0
            temp_flipped = []

            # Move outward until we hit a boundary or your disc
            for step in range(1, 8):
                nr, nc = r + dr * step, c + dc * step
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if opponent[nr, nc] == 1:
                        temp_flipped.append((nr, nc))
                        flip_count += 1
                    elif you[nr, nc] == 1:
                        flips += flip_count
                        break
                else:
                    break  # Out of bounds

        # Score = (flips * 10) + (corner bonus) + (edge bonus)
        corner_bonus = 0
        edge_bonus = 0

        # Corner priority (a1, a8, h1, h8, etc.)
        if (r == 0 or r == 7) and (c == 0 or c == 7):
            corner_bonus = 100

        # Edge priority (not corners, but on perimeter)
        elif r == 0 or r == 7 or c == 0 or c == 7:
            edge_bonus = 50

        # Total score for this move
        score = flips * 10 + corner_bonus + edge_bonus

        # Update best moves
        if score > best_score:
            best_moves = [(c, r, flips, score)]  # (col, row, flips, score)
            best_score = score
            best_flips = flips
        elif score == best_score:
            best_moves.append((c, r, flips, score))

    # If multiple moves have the same score, pick the one with the most flips
    if len(best_moves) > 1:
        best_moves = sorted(best_moves, key=lambda x: -x[2])  # Sort by flips descending
        best_moves = [(c, r) for c, r, flips, score in best_moves if flips == best_moves[0][2]]

    # If still multiple, pick the first one (arbitrary but deterministic)
    if len(best_moves) > 0:
        c, r = best_moves[0]
        return f"{chr(ord('a') + c)}{r + 1}"
    else:
        return "pass"  # Should never happen due to constraints
