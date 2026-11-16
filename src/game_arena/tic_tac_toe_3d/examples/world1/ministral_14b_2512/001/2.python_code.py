
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Determines the next move for a 3D Tic Tac Toe game (3x3x3).

    Args:
        board: A 3x3x3 list of lists containing 0 (empty), 1 (me), and -1 (opponent).

    Returns:
        A tuple (x, y, z) representing the coordinates of the best empty cell to place my next move.
    """
    # Convert the board to a numpy array for easier manipulation
    np_board = np.array(board)

    # Check for immediate winning moves
    winning_move = find_immediate_winning_move(np_board, 1)
    if winning_move is not None:
        return winning_move

    # Check for opponent's immediate winning moves and block them
    opponent_winning_move = find_immediate_winning_move(np_board, -1)
    if opponent_winning_move is not None:
        return opponent_winning_move

    # If no immediate win or block, choose a move based on heuristics
    best_move = choose_heuristic_move(np_board)
    return best_move

def find_immediate_winning_move(board: np.ndarray, player: int) -> Tuple[int, int, int]:
    """
    Finds if placing `player` in any empty cell would complete a winning line.

    Args:
        board: The current board state.
        player: The player (1 or -1) to check for winning moves.

    Returns:
        A tuple (x, y, z) of the first winning move found, or None if no winning move exists.
    """
    # Get all empty cells
    empty_cells = np.argwhere(board == 0)

    # Check all possible lines
    for x, y, z in empty_cells:
        # Check if placing player here would complete any line
        if is_winning_move(board, x, y, z, player):
            return (x, y, z)
    return None

def is_winning_move(board: np.ndarray, x: int, y: int, z: int, player: int) -> bool:
    """
    Checks if placing `player` at (x, y, z) completes any winning line.

    Args:
        board: The current board state.
        x, y, z: Coordinates of the cell to check.
        player: The player (1 or -1) to check for winning moves.

    Returns:
        True if placing `player` at (x, y, z) completes any line, False otherwise.
    """
    # Copy the board and place the player's move
    temp_board = board.copy()
    temp_board[x, y, z] = player

    # Check rows (fixed x, fixed z, vary y)
    for i in range(3):
        for j in range(3):
            if temp_board[i, :, j].sum() == 3 * player:
                return True

    # Check columns (fixed x, fixed y, vary z)
    for i in range(3):
        for j in range(3):
            if temp_board[i, j, :].sum() == 3 * player:
                return True

    # Check pillars (fixed y, fixed z, vary x)
    for j in range(3):
        for k in range(3):
            if temp_board[:, j, k].sum() == 3 * player:
                return True

    # Check space diagonals (4 main diagonals)
    # Diagonal 1: (0,0,0) to (2,2,2)
    if (temp_board[0, 0, 0] == player and temp_board[1, 1, 1] == player and temp_board[2, 2, 2] == player) or \
       (temp_board[0, 0, 0] == player and temp_board[1, 1, 1] == player and temp_board[2, 2, 2] == player) or \
       (temp_board[0, 0, 0] == player and temp_board[1, 1, 1] == player and temp_board[2, 2, 2] == player):
        pass  # Already checked in rows, columns, pillars
    # Diagonal 2: (0,0,2) to (2,2,0)
    if (temp_board[0, 0, 2] == player and temp_board[1, 1, 1] == player and temp_board[2, 2, 0] == player) or \
       (temp_board[0, 0, 2] == player and temp_board[1, 1, 1] == player and temp_board[2, 2, 0] == player) or \
       (temp_board[0, 0, 2] == player and temp_board[1, 1, 1] == player and temp_board[2, 2, 0] == player):
        pass
    # Diagonal 3: (0,2,0) to (2,0,2)
    if (temp_board[0, 2, 0] == player and temp_board[1, 1, 1] == player and temp_board[2, 0, 2] == player) or \
       (temp_board[0, 2, 0] == player and temp_board[1, 1, 1] == player and temp_board[2, 0, 2] == player) or \
       (temp_board[0, 2, 0] == player and temp_board[1, 1, 1] == player and temp_board[2, 0, 2] == player):
        pass
    # Diagonal 4: (0,2,2) to (2,0,0)
    if (temp_board[0, 2, 2] == player and temp_board[1, 1, 1] == player and temp_board[2, 0, 0] == player) or \
       (temp_board[0, 2, 2] == player and temp_board[1, 1, 1] == player and temp_board[2, 0, 0] == player) or \
       (temp_board[0, 2, 2] == player and temp_board[1, 1, 1] == player and temp_board[2, 0, 0] == player):
        pass

    # Check all space diagonals (4 total)
    space_diagonals = [
        [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
        [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
        [(0, 2, 2), (1, 1, 1), (2, 0, 0)]
    ]
    for diagonal in space_diagonals:
        count = 0
        for (i, j, k) in diagonal:
            if temp_board[i, j, k] == player:
                count += 1
        if count == 3:
            return True

    # Check face diagonals (12 total)
    face_diagonals = [
        # Front face (x=0)
        [(0, 0, 0), (0, 1, 1), (0, 2, 2)],
        [(0, 0, 2), (0, 1, 1), (0, 2, 0)],
        [(0, 0, 1), (0, 1, 0), (0, 2, 1)],
        [(0, 0, 1), (0, 1, 2), (0, 2, 1)],
        # Back face (x=2)
        [(2, 0, 0), (2, 1, 1), (2, 2, 2)],
        [(2, 0, 2), (2, 1, 1), (2, 2, 0)],
        [(2, 0, 1), (2, 1, 0), (2, 2, 1)],
        [(2, 0, 1), (2, 1, 2), (2, 2, 1)],
        # Left face (y=0)
        [(0, 0, 0), (1, 0, 1), (2, 0, 2)],
        [(0, 0, 2), (1, 0, 1), (2, 0, 0)],
        [(1, 0, 0), (1, 0, 1), (1, 0, 2)],
        [(1, 0, 2), (1, 0, 1), (1, 0, 0)],
        # Right face (y=2)
        [(0, 2, 0), (1, 2, 1), (2, 2, 2)],
        [(0, 2, 2), (1, 2, 1), (2, 2, 0)],
        [(1, 2, 0), (1, 2, 1), (1, 2, 2)],
        [(1, 2, 2), (1, 2, 1), (1, 2, 0)],
        # Top face (z=0)
        [(0, 0, 0), (1, 1, 0), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 0), (2, 0, 0)],
        [(0, 1, 0), (1, 0, 0), (2, 1, 0)],
        [(0, 1, 0), (1, 2, 0), (2, 1, 0)],
        # Bottom face (z=2)
        [(0, 0, 2), (1, 1, 2), (2, 2, 2)],
        [(0, 2, 2), (1, 1, 2), (2, 0, 2)],
        [(0, 1, 2), (1, 0, 2), (2, 1, 2)],
        [(0, 1, 2), (1, 2, 2), (2, 1, 2)]
    ]
    for diagonal in face_diagonals:
        count = 0
        for (i, j, k) in diagonal:
            if temp_board[i, j, k] == player:
                count += 1
        if count == 3:
            return True

    # Check rows, columns, pillars again (since diagonals might have been missed in the initial checks)
    for i in range(3):
        for j in range(3):
            if temp_board[i, :, j].sum() == 3 * player:
                return True
            if temp_board[i, j, :].sum() == 3 * player:
                return True
    for j in range(3):
        for k in range(3):
            if temp_board[:, j, k].sum() == 3 * player:
                return True

    return False

def choose_heuristic_move(board: np.ndarray) -> Tuple[int, int, int]:
    """
    Chooses a move based on heuristics if no immediate win or block is found.

    Args:
        board: The current board state.

    Returns:
        A tuple (x, y, z) of the best move according to heuristics.
    """
    # Get all empty cells
    empty_cells = np.argwhere(board == 0)

    # Heuristic 1: Prefer the center (1,1,1)
    if (1, 1, 1) in empty_cells:
        return (1, 1, 1)

    # Heuristic 2: Choose the move that is part of the most potential lines
    best_move = None
    best_score = -1

    for x, y, z in empty_cells:
        score = get_potential_lines(board, x, y, z)
        if score > best_score:
            best_score = score
            best_move = (x, y, z)

    return best_move

def get_potential_lines(board: np.ndarray, x: int, y: int, z: int) -> int:
    """
    Calculates the number of potential lines (rows, columns, pillars, diagonals) that a move at (x, y, z) is part of.

    Args:
        board: The current board state.
        x, y, z: Coordinates of the cell to evaluate.

    Returns:
        An integer representing the number of potential lines the move is part of.
    """
    score = 0

    # Check rows (fixed x, fixed z, vary y)
    for i in range(3):
        if board[x, i, z] == 0:
            score += 1

    # Check columns (fixed x, fixed y, vary z)
    for j in range(3):
        if board[x, y, j] == 0:
            score += 1

    # Check pillars (fixed y, fixed z, vary x)
    for k in range(3):
        if board[k, y, z] == 0:
            score += 1

    # Check space diagonals (4 total)
    space_diagonals = [
        [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
        [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
        [(0, 2, 2), (1, 1, 1), (2, 0, 0)]
    ]
    for diagonal in space_diagonals:
        count = 0
        for (i, j, k) in diagonal:
            if board[i, j, k] == 0:
                count += 1
        if (x, y, z) in diagonal:
            score += count

    # Check face diagonals (12 total)
    face_diagonals = [
        # Front face (x=0)
        [(0, 0, 0), (0, 1, 1), (0, 2, 2)],
        [(0, 0, 2), (0, 1, 1), (0, 2, 0)],
        [(0, 0, 1), (0, 1, 0), (0, 2, 1)],
        [(0, 0, 1), (0, 1, 2), (0, 2, 1)],
        # Back face (x=2)
        [(2, 0, 0), (2, 1, 1), (2, 2, 2)],
        [(2, 0, 2), (2, 1, 1), (2, 2, 0)],
        [(2, 0, 1), (2, 1, 0), (2, 2, 1)],
        [(2, 0, 1), (2, 1, 2), (2, 2, 1)],
        # Left face (y=0)
        [(0, 0, 0), (1, 0, 1), (2, 0, 2)],
        [(0, 0, 2), (1, 0, 1), (2, 0, 0)],
        [(1, 0, 0), (1, 0, 1), (1, 0, 2)],
        [(1, 0, 2), (1, 0, 1), (1, 0, 0)],
        # Right face (y=2)
        [(0, 2, 0), (1, 2, 1), (2, 2, 2)],
        [(0, 2, 2), (1, 2, 1), (2, 2, 0)],
        [(1, 2, 0), (1, 2, 1), (1, 2, 2)],
        [(1, 2, 2), (1, 2, 1), (1, 2, 0)],
        # Top face (z=0)
        [(0, 0, 0), (1, 1, 0), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 0), (2, 0, 0)],
        [(0, 1, 0), (1, 0, 0), (2, 1, 0)],
        [(0, 1, 0), (1, 2, 0), (2, 1, 0)],
        # Bottom face (z=2)
        [(0, 0, 2), (1, 1, 2), (2, 2, 2)],
        [(0, 2, 2), (1, 1, 2), (2, 0, 2)],
        [(0, 1, 2), (1, 0, 2), (2, 1, 2)],
        [(0, 1, 2), (1, 2, 2), (2, 1, 2)]
    ]
    for diagonal in face_diagonals:
        count = 0
        for (i, j, k) in diagonal:
            if board[i, j, k] == 0:
                count += 1
        if (x, y, z) in diagonal:
            score += count

    return score
