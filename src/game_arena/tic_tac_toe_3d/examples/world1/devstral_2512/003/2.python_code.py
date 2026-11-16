
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Returns the best move for the AI player (1) in a 3x3x3 Tic Tac Toe game.
    The board is represented as a 3x3x3 list where:
    - 0 = empty
    - 1 = AI player
    - -1 = opponent
    """

    # Convert to numpy array for easier manipulation
    board_array = np.array(board)

    # Get all possible winning lines (each line is a list of (x,y,z) coordinates)
    winning_lines = get_winning_lines()

    # First, check if AI can win immediately
    for move in get_empty_cells(board_array):
        x, y, z = move
        # Temporarily make the move
        board_array[x, y, z] = 1
        if is_winning_move(board_array, move, 1):
            return move
        # Undo the move
        board_array[x, y, z] = 0

    # Then, check if opponent can win and block them
    for move in get_empty_cells(board_array):
        x, y, z = move
        # Temporarily make the opponent's move
        board_array[x, y, z] = -1
        if is_winning_move(board_array, move, -1):
            return move
        # Undo the move
        board_array[x, y, z] = 0

    # If no immediate win or block, use heuristic to choose best move
    best_move = None
    best_score = -float('inf')

    for move in get_empty_cells(board_array):
        score = evaluate_move(board_array, move)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def get_winning_lines() -> List[List[Tuple[int, int, int]]]:
    """Returns all possible winning lines in 3D Tic Tac Toe."""
    lines = []

    # Add all rows in each layer (x fixed)
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, 0), (x, y, 1), (x, y, 2)])

    # Add all columns in each layer (y fixed)
    for y in range(3):
        for z in range(3):
            lines.append([(0, y, z), (1, y, z), (2, y, z)])

    # Add all depth lines (z fixed)
    for z in range(3):
        for x in range(3):
            lines.append([(x, 0, z), (x, 1, z), (x, 2, z)])

    # Add main space diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

    # Add face diagonals for each face
    # Front and back faces (z=0 and z=2)
    for z in [0, 2]:
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])

    # Left and right faces (x=0 and x=2)
    for x in [0, 2]:
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])

    # Top and bottom faces (y=0 and y=2)
    for y in [0, 2]:
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])

    return lines

def get_empty_cells(board_array: np.ndarray) -> List[Tuple[int, int, int]]:
    """Returns list of all empty cell coordinates."""
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board_array[x, y, z] == 0:
                    empty_cells.append((x, y, z))
    return empty_cells

def is_winning_move(board_array: np.ndarray, move: Tuple[int, int, int], player: int) -> bool:
    """Checks if placing player's mark at move position would win the game."""
    x, y, z = move
    winning_lines = get_winning_lines()

    for line in winning_lines:
        if move in line:
            # Check if all cells in this line are either player or the current move
            line_won = True
            for (lx, ly, lz) in line:
                if (lx, ly, lz) == move:
                    continue  # This is our hypothetical move
                if board_array[lx, ly, lz] != player:
                    line_won = False
                    break
            if line_won:
                return True
    return False

def evaluate_move(board_array: np.ndarray, move: Tuple[int, int, int]) -> float:
    """
    Evaluates how good a move is based on:
    - Center preference (center is (1,1,1))
    - Number of potential winning lines created
    - Opponent blocking potential
    """
    x, y, z = move
    score = 0.0

    # Center preference
    center_distance = abs(x - 1) + abs(y - 1) + abs(z - 1)
    score += (2 - center_distance) * 0.5  # Max 1.5 for center

    # Count how many potential winning lines this move creates
    winning_lines = get_winning_lines()
    potential_lines = 0

    for line in winning_lines:
        if move in line:
            # Count how many of player's marks are already in this line
            player_count = 0
            opponent_count = 0
            empty_count = 0

            for (lx, ly, lz) in line:
                cell = board_array[lx, ly, lz]
                if cell == 1:
                    player_count += 1
                elif cell == -1:
                    opponent_count += 1
                else:
                    empty_count += 1

            # If this line has 2 player marks and this move would make 3, it's a win (already handled)
            # If this line has 1 player mark and this move would make 2, it's good
            if player_count == 1 and empty_count == 2:
                potential_lines += 1
            # If this line has 0 player marks but opponent has 1, blocking is good
            elif player_count == 0 and opponent_count == 1 and empty_count == 2:
                potential_lines += 0.5

    score += potential_lines * 1.0

    return score
