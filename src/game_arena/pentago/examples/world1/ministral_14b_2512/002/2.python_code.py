
import numpy as np
from typing import List, Tuple

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    """
    Pentago policy that prioritizes:
    1. Immediate win (if possible).
    2. Blocking opponent's immediate win.
    3. Placing in center quadrants (0 or 3) to maximize connectivity.
    4. Rotating to align player's marbles for future threats.
    5. Fallback to random if no threats/blocks are found.
    """
    you_board = np.array(you, dtype=int)
    opp_board = np.array(opponent, dtype=int)
    empty_cells = np.argwhere(you_board == 0)

    # Check if current player can win immediately
    for row, col in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                new_you = _apply_move(you_board, opp_board, row, col, quad, dir)
                if _check_win(new_you, 5):
                    return f"{row+1},{col+1},{quad},{dir}"

    # Check if opponent can win next turn (blocking)
    for row, col in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                new_you = _apply_move(you_board, opp_board, row, col, quad, dir)
                if _check_win(new_you, 4):  # Opponent has 4+ (can win next turn)
                    # Place in the opponent's potential winning line to block
                    return f"{row+1},{col+1},{quad},{dir}"

    # Prefer center quadrants (0 or 3) for placement
    center_quads = [0, 3]
    best_quad = None
    best_row, best_col = -1, -1

    # Find the best quadrant to place in (based on existing player marbles)
    for quad in center_quads:
        if _has_marbles_in_quad(you_board, quad):
            best_quad = quad
            break

    if best_quad is None:
        # If no center preference, pick a random empty cell
        best_row, best_col = np.random.choice(empty_cells, 1)[0]

    # Place in the best quadrant (or random if none)
    for row, col in empty_cells:
        if best_quad is not None and _is_in_quad(row, col, best_quad):
            break

    # Now choose the best rotation direction
    for quad in range(4):
        if _is_in_quad(row, col, quad):
            for dir in ['L', 'R']:
                new_you = _apply_move(you_board, opp_board, row, col, quad, dir)
                if _check_win(new_you, 4):  # Player has 4+ (can win next turn)
                    return f"{row+1},{col+1},{quad},{dir}"

    # If no immediate threats, rotate randomly
    dir = np.random.choice(['L', 'R'])
    return f"{row+1},{col+1},{quad},{dir}"

def _apply_move(you_board: np.ndarray, opp_board: np.ndarray, row: int, col: int, quad: int, dir: str) -> np.ndarray:
    """Applies a move (place + rotate) and returns the new board state."""
    new_you = you_board.copy()
    new_you[row, col] = 1  # Place marble

    # Rotate the specified quadrant
    if dir == 'L':
        new_you = _rotate_quadrant_left(new_you, quad)
    else:
        new_you = _rotate_quadrant_right(new_you, quad)

    return new_you

def _rotate_quadrant_left(board: np.ndarray, quad: int) -> np.ndarray:
    """Rotates a 3x3 quadrant 90° anticlockwise."""
    if quad == 0:
        sub = board[0:3, 0:3]
        rotated = np.rot90(sub, k=1)
        board[0:3, 0:3] = rotated
    elif quad == 1:
        sub = board[0:3, 3:6]
        rotated = np.rot90(sub, k=1)
        board[0:3, 3:6] = rotated
    elif quad == 2:
        sub = board[3:6, 0:3]
        rotated = np.rot90(sub, k=1)
        board[3:6, 0:3] = rotated
    elif quad == 3:
        sub = board[3:6, 3:6]
        rotated = np.rot90(sub, k=1)
        board[3:6, 3:6] = rotated
    return board

def _rotate_quadrant_right(board: np.ndarray, quad: int) -> np.ndarray:
    """Rotates a 3x3 quadrant 90° clockwise."""
    if quad == 0:
        sub = board[0:3, 0:3]
        rotated = np.rot90(sub, k=3)
        board[0:3, 0:3] = rotated
    elif quad == 1:
        sub = board[0:3, 3:6]
        rotated = np.rot90(sub, k=3)
        board[0:3, 3:6] = rotated
    elif quad == 2:
        sub = board[3:6, 0:3]
        rotated = np.rot90(sub, k=3)
        board[3:6, 0:3] = rotated
    elif quad == 3:
        sub = board[3:6, 3:6]
        rotated = np.rot90(sub, k=3)
        board[3:6, 3:6] = rotated
    return board

def _is_in_quad(row: int, col: int, quad: int) -> bool:
    """Checks if (row, col) is in the specified quadrant (0-3)."""
    if quad == 0:
        return 0 <= row < 3 and 0 <= col < 3
    elif quad == 1:
        return 0 <= row < 3 and 3 <= col < 6
    elif quad == 2:
        return 3 <= row < 6 and 0 <= col < 3
    elif quad == 3:
        return 3 <= row < 6 and 3 <= col < 6
    return False

def _has_marbles_in_quad(board: np.ndarray, quad: int) -> bool:
    """Checks if the player has marbles in the specified quadrant."""
    if quad == 0:
        return np.any(board[0:3, 0:3] == 1)
    elif quad == 1:
        return np.any(board[0:3, 3:6] == 1)
    elif quad == 2:
        return np.any(board[3:6, 0:3] == 1)
    elif quad == 3:
        return np.any(board[3:6, 3:6] == 1)
    return False

def _check_win(board: np.ndarray, count: int) -> bool:
    """Checks if the player has 'count' marbles in a row (horizontally, vertically, or diagonally)."""
    # Check rows
    for r in range(6):
        for c in range(3):
            if np.sum(board[r, c:c+count]) >= count:
                return True

    # Check columns
    for c in range(6):
        for r in range(3):
            if np.sum(board[r:r+count, c]) >= count:
                return True

    # Check diagonals (top-left to bottom-right)
    for r in range(3):
        for c in range(3):
            if r + count <= 6 and c + count <= 6:
                if np.sum(np.diag(board[r:r+count, c:c+count])) >= count:
                    return True

    # Check diagonals (bottom-left to top-right)
    for r in range(3, 6):
        for c in range(3):
            if r - count >= 0 and c + count <= 6:
                if np.sum(np.diag(board[r-count:r+1, c:c+count])) >= count:
                    return True

    return False
