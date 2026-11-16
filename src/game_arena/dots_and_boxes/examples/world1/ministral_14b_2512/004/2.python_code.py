
import numpy as np
from typing import List, Tuple

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes policy for a 4x4 grid (5x5 arrays).
    Strategy: Prioritize moves that complete boxes, avoid giving opponent 3-sided boxes,
    and otherwise play greedily to maximize future box completions.
    """
    # Directions: H (horizontal), V (vertical)
    dirs = ['H', 'V']
    # Possible moves: all legal edges (0 in horizontal or vertical)
    legal_moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))

    if not legal_moves:
        # Should not happen in a valid game, but return a dummy move if no legal moves exist
        return "0,0,H"

    # Step 1: Find moves that complete at least one box for the current player
    box_completing_moves = []
    for move in legal_moves:
        row, col, dir = move
        if dir == 'H':
            # Check if this horizontal edge completes a box
            if (vertical[row, col] != 0 and vertical[row, col + 1] != 0 and
                horizontal[row, col - 1] != 0 if col > 0 else True and
                horizontal[row, col + 1] != 0 if col < 4 else True):
                box_completing_moves.append(move)
        elif dir == 'V':
            # Check if this vertical edge completes a box
            if (horizontal[row, col] != 0 and horizontal[row + 1, col] != 0 and
                vertical[row, col - 1] != 0 if col > 0 else True and
                vertical[row + 1, col] != 0 if row < 4 else True):
                box_completing_moves.append(move)

    # Step 2: Among box-completing moves, prefer those that complete more than one box
    multi_box_moves = []
    for move in box_completing_moves:
        row, col, dir = move
        boxes_completed = 0
        # Check if this move completes any boxes
        if dir == 'H':
            # Check left box (if exists)
            if col > 0 and vertical[row, col] != 0 and vertical[row, col - 1] != 0 and horizontal[row, col - 1] != 0:
                boxes_completed += 1
            # Check right box (if exists)
            if col < 4 and vertical[row, col + 1] != 0 and vertical[row, col] != 0 and horizontal[row, col + 1] != 0:
                boxes_completed += 1
        elif dir == 'V':
            # Check top box (if exists)
            if row > 0 and horizontal[row, col] != 0 and horizontal[row - 1, col] != 0 and vertical[row - 1, col] != 0:
                boxes_completed += 1
            # Check bottom box (if exists)
            if row < 4 and horizontal[row + 1, col] != 0 and horizontal[row, col] != 0 and vertical[row + 1, col] != 0:
                boxes_completed += 1
        if boxes_completed > 1:
            multi_box_moves.append(move)

    if multi_box_moves:
        # Prefer moves that complete multiple boxes
        return _select_move_by_potential(multi_box_moves, horizontal, vertical, capture)
    elif box_completing_moves:
        # Otherwise, prefer moves that complete at least one box
        return _select_move_by_potential(box_completing_moves, horizontal, vertical, capture)
    else:
        # Step 3: Avoid moves that give opponent exactly 3 sides of a box
        opponent_three_sided_moves = []
        for move in legal_moves:
            row, col, dir = move
            if dir == 'H':
                # Check if this move leaves opponent with exactly 3 sides in any box
                if col > 0 and vertical[row, col] == 0 and vertical[row, col - 1] == 0 and horizontal[row, col - 1] == 0:
                    opponent_three_sided_moves.append(move)
                if col < 4 and vertical[row, col] == 0 and vertical[row, col + 1] == 0 and horizontal[row, col + 1] == 0:
                    opponent_three_sided_moves.append(move)
            elif dir == 'V':
                # Check if this move leaves opponent with exactly 3 sides in any box
                if row > 0 and horizontal[row, col] == 0 and horizontal[row - 1, col] == 0 and vertical[row - 1, col] == 0:
                    opponent_three_sided_moves.append(move)
                if row < 4 and horizontal[row + 1, col] == 0 and horizontal[row, col] == 0 and vertical[row + 1, col] == 0:
                    opponent_three_sided_moves.append(move)

        if opponent_three_sided_moves:
            # Avoid these moves
            remaining_moves = [move for move in legal_moves if move not in opponent_three_sided_moves]
            return _select_move_by_potential(remaining_moves, horizontal, vertical, capture)
        else:
            # Step 4: Greedy move selection (maximize potential boxes)
            return _select_move_by_potential(legal_moves, horizontal, vertical, capture)

def _select_move_by_potential(moves: List[Tuple[int, int, str]], horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Selects a move from the given list by evaluating the potential number of boxes it can help complete.
    """
    # Evaluate each move's potential (number of boxes it can contribute to)
    best_move = None
    best_potential = -1
    for move in moves:
        row, col, dir = move
        potential = 0
        # Count potential boxes for this move
        if dir == 'H':
            # Left box potential
            if col > 0 and vertical[row, col] == 0 and vertical[row, col - 1] == 0 and horizontal[row, col - 1] == 0:
                potential += 1
            # Right box potential
            if col < 4 and vertical[row, col] == 0 and vertical[row, col + 1] == 0 and horizontal[row, col + 1] == 0:
                potential += 1
        elif dir == 'V':
            # Top box potential
            if row > 0 and horizontal[row, col] == 0 and horizontal[row - 1, col] == 0 and vertical[row - 1, col] == 0:
                potential += 1
            # Bottom box potential
            if row < 4 and horizontal[row + 1, col] == 0 and horizontal[row, col] == 0 and vertical[row + 1, col] == 0:
                potential += 1
        # Also count boxes that would be completed by this move (for tie-breaking)
        boxes_completed = 0
        if dir == 'H':
            if col > 0 and vertical[row, col] != 0 and vertical[row, col - 1] != 0 and horizontal[row, col - 1] != 0:
                boxes_completed += 1
            if col < 4 and vertical[row, col + 1] != 0 and vertical[row, col] != 0 and horizontal[row, col + 1] != 0:
                boxes_completed += 1
        elif dir == 'V':
            if row > 0 and horizontal[row, col] != 0 and horizontal[row - 1, col] != 0 and vertical[row - 1, col] != 0:
                boxes_completed += 1
            if row < 4 and horizontal[row + 1, col] != 0 and horizontal[row, col] != 0 and vertical[row + 1, col] != 0:
                boxes_completed += 1
        # Prefer moves that complete boxes over those that just have potential
        if boxes_completed > 0:
            potential += 10  # High priority for box-completing moves
        if potential > best_potential:
            best_potential = potential
            best_move = move
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
