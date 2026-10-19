
import numpy as np
from typing import Optional

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Policy for 3x3x3 3D Tic Tac Toe.
    Returns the next move as (z, y, x) coordinates.
    """
    n = 3
    b = np.array(board)
    
    # First, try to win
    move = find_winning_move(b, 1)
    if move is not None:
        return move
    
    # Second, block opponent from winning
    move = find_winning_move(b, -1)
    if move is not None:
        return move
    
    # Third, try to create two-in-a-row with strategic positioning
    move = find_strategic_move(b)
    if move is not None:
        return move
    
    # Fourth, take center if available
    if b[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Fifth, take corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for corner in corners:
        if b[corner] == 0:
            return corner
    
    # Finally, take any available position
    empty = np.argwhere(b == 0)
    if len(empty) > 0:
        return tuple(empty[0])
    
    return (0, 0, 0)  # Fallback (shouldn't happen)


def find_winning_move(b: np.ndarray, player: int) -> Optional[tuple[int, int, int]]:
    """Find a move that wins for the given player, or None if no such move exists."""
    n = 3
    empty_cells = np.argwhere(b == 0)
    
    for cell in empty_cells:
        z, y, x = cell
        b[z, y, x] = player
        if check_win(b, player):
            b[z, y, x] = 0
            return (int(z), int(y), int(x))
        b[z, y, x] = 0
    
    return None


def check_win(b: np.ndarray, player: int) -> bool:
    """Check if the given player has won."""
    n = 3
    
    # Check rows (along x-axis)
    for z in range(n):
        for y in range(n):
            if np.all(b[z, y, :] == player):
                return True
    
    # Check columns (along y-axis)
    for z in range(n):
        for x in range(n):
            if np.all(b[z, :, x] == player):
                return True
    
    # Check pillars (along z-axis)
    for y in range(n):
        for x in range(n):
            if np.all(b[:, y, x] == player):
                return True
    
    # Check diagonals in xy planes
    for z in range(n):
        if np.all([b[z, i, i] == player for i in range(n)]):
            return True
        if np.all([b[z, i, n-1-i] == player for i in range(n)]):
            return True
    
    # Check diagonals in xz planes
    for y in range(n):
        if np.all([b[i, y, i] == player for i in range(n)]):
            return True
        if np.all([b[i, y, n-1-i] == player for i in range(n)]):
            return True
    
    # Check diagonals in yz planes
    for x in range(n):
        if np.all([b[i, i, x] == player for i in range(n)]):
            return True
        if np.all([b[i, n-1-i, x] == player for i in range(n)]):
            return True
    
    # Check 4 main space diagonals
    if np.all([b[i, i, i] == player for i in range(n)]):
        return True
    if np.all([b[i, i, n-1-i] == player for i in range(n)]):
        return True
    if np.all([b[i, n-1-i, i] == player for i in range(n)]):
        return True
    if np.all([b[i, n-1-i, n-1-i] == player for i in range(n)]):
        return True
    
    return False


def find_strategic_move(b: np.ndarray) -> Optional[tuple[int, int, int]]:
    """Find a strategic move that creates threats."""
    n = 3
    empty_cells = np.argwhere(b == 0)
    
    best_move = None
    best_score = -1
    
    for cell in empty_cells:
        z, y, x = cell
        score = evaluate_position(b, (z, y, x), 1)
        if score > best_score:
            best_score = score
            best_move = (int(z), int(y), int(x))
    
    return best_move if best_score > 0 else None


def evaluate_position(b: np.ndarray, pos: tuple, player: int) -> int:
    """Evaluate how good a position is based on potential lines."""
    z, y, x = pos
    score = 0
    
    # Count how many lines this position contributes to where we have pieces
    # and opponent doesn't block
    b[z, y, x] = player
    
    # Simple heuristic: count two-in-a-rows we create
    score += count_threats(b, player)
    
    b[z, y, x] = 0
    return score


def count_threats(b: np.ndarray, player: int) -> int:
    """Count number of lines with 2 of player and 1 empty."""
    threats = 0
    n = 3
    
    # Just check a few key lines for efficiency
    for z in range(n):
        for y in range(n):
            line = b[z, y, :]
            if np.sum(line == player) == 2 and np.sum(line == 0) == 1:
                threats += 1
    
    return threats
