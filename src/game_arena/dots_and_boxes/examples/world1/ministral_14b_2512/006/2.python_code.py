
import numpy as np
from typing import List, Tuple

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes AI policy for a 4x4 grid.
    Strategy: Aggressive box completion, opponent threat blocking, and center control.
    """
    # Directions: H (horizontal), V (vertical)
    # Find all legal moves (edges with value 0)
    legal_moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))

    if not legal_moves:
        return ""  # No legal moves (game should be over)

    # Check if any move completes a box for me (aggressive)
    aggressive_moves = []
    for row, col, dir in legal_moves:
        if dir == 'H':
            # Check if the box to the left or right is completable
            if col > 0:
                # Box at (row, col-1)
                box_edges = [
                    horizontal[row, col-1],  # Left edge
                    vertical[row, col-1],    # Top edge
                    vertical[row+1, col-1], # Bottom edge
                    horizontal[row, col]     # Current edge (right edge of box)
                ]
                if np.sum(box_edges == 1) == 3 and box_edges[3] == 0:
                    aggressive_moves.append((row, col-1, 'H'))
            if col < 4:
                # Box at (row, col)
                box_edges = [
                    horizontal[row, col],     # Current edge (left edge of box)
                    vertical[row, col],       # Top edge
                    vertical[row+1, col],    # Bottom edge
                    horizontal[row, col+1]   # Right edge
                ]
                if np.sum(box_edges == 1) == 3 and box_edges[0] == 0:
                    aggressive_moves.append((row, col, 'H'))
        elif dir == 'V':
            # Check if the box above or below is completable
            if row > 0:
                # Box at (row-1, col)
                box_edges = [
                    vertical[row-1, col],    # Current edge (top edge of box)
                    horizontal[row-1, col],  # Left edge
                    horizontal[row, col],    # Right edge
                    vertical[row, col]       # Bottom edge
                ]
                if np.sum(box_edges == 1) == 3 and box_edges[0] == 0:
                    aggressive_moves.append((row-1, col, 'V'))
            if row < 4:
                # Box at (row, col)
                box_edges = [
                    vertical[row, col],       # Current edge (top edge of box)
                    horizontal[row, col],     # Left edge
                    horizontal[row+1, col],  # Right edge
                    vertical[row+1, col]    # Bottom edge
                ]
                if np.sum(box_edges == 1) == 3 and box_edges[0] == 0:
                    aggressive_moves.append((row, col, 'V'))

    # If aggressive moves exist, pick the one that completes the most boxes
    if aggressive_moves:
        # Evaluate each aggressive move to see how many boxes it completes
        best_move = None
        max_boxes_completed = -1
        for move in aggressive_moves:
            row, col, dir = move
            boxes_completed = 0
            if dir == 'H':
                if col > 0:
                    # Check box (row, col-1)
                    box_edges = [
                        horizontal[row, col-1],
                        vertical[row, col-1],
                        vertical[row+1, col-1],
                        horizontal[row, col]
                    ]
                    if np.sum(box_edges == 1) == 3:
                        boxes_completed += 1
                if col < 4:
                    # Check box (row, col)
                    box_edges = [
                        horizontal[row, col],
                        vertical[row, col],
                        vertical[row+1, col],
                        horizontal[row, col+1]
                    ]
                    if np.sum(box_edges == 1) == 3:
                        boxes_completed += 1
            elif dir == 'V':
                if row > 0:
                    # Check box (row-1, col)
                    box_edges = [
                        vertical[row-1, col],
                        horizontal[row-1, col],
                        horizontal[row, col],
                        vertical[row, col]
                    ]
                    if np.sum(box_edges == 1) == 3:
                        boxes_completed += 1
                if row < 4:
                    # Check box (row, col)
                    box_edges = [
                        vertical[row, col],
                        horizontal[row, col],
                        horizontal[row+1, col],
                        vertical[row+1, col]
                    ]
                    if np.sum(box_edges == 1) == 3:
                        boxes_completed += 1
            if boxes_completed > max_boxes_completed:
                max_boxes_completed = boxes_completed
                best_move = move
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Check for opponent threats (edges that complete 3 sides of their box)
    opponent_threats = []
    for row, col, dir in legal_moves:
        if dir == 'H':
            if col > 0:
                # Box at (row, col-1)
                box_edges = [
                    horizontal[row, col-1],  # Left edge
                    vertical[row, col-1],    # Top edge
                    vertical[row+1, col-1], # Bottom edge
                    horizontal[row, col]     # Current edge (right edge of box)
                ]
                if np.sum(box_edges == -1) == 3 and box_edges[3] == 0:
                    opponent_threats.append((row, col-1, 'H'))
            if col < 4:
                # Box at (row, col)
                box_edges = [
                    horizontal[row, col],     # Current edge (left edge of box)
                    vertical[row, col],       # Top edge
                    vertical[row+1, col],    # Bottom edge
                    horizontal[row, col+1]   # Right edge
                ]
                if np.sum(box_edges == -1) == 3 and box_edges[0] == 0:
                    opponent_threats.append((row, col, 'H'))
        elif dir == 'V':
            if row > 0:
                # Box at (row-1, col)
                box_edges = [
                    vertical[row-1, col],    # Current edge (top edge of box)
                    horizontal[row-1, col],  # Left edge
                    horizontal[row, col],    # Right edge
                    vertical[row, col]       # Bottom edge
                ]
                if np.sum(box_edges == -1) == 3 and box_edges[0] == 0:
                    opponent_threats.append((row-1, col, 'V'))
            if row < 4:
                # Box at (row, col)
                box_edges = [
                    vertical[row, col],       # Current edge (top edge of box)
                    horizontal[row, col],     # Left edge
                    horizontal[row+1, col],  # Right edge
                    vertical[row+1, col]    # Bottom edge
                ]
                if np.sum(box_edges == -1) == 3 and box_edges[0] == 0:
                    opponent_threats.append((row, col, 'V'))

    # If opponent threats exist, block them (defensive)
    if opponent_threats:
        # Evaluate each threat to see how many boxes it would complete for opponent
        best_move = None
        max_boxes_blocked = -1
        for move in opponent_threats:
            row, col, dir = move
            boxes_blocked = 0
            if dir == 'H':
                if col > 0:
                    # Check box (row, col-1)
                    box_edges = [
                        horizontal[row, col-1],
                        vertical[row, col-1],
                        vertical[row+1, col-1],
                        horizontal[row, col]
                    ]
                    if np.sum(box_edges == -1) == 3:
                        boxes_blocked += 1
                if col < 4:
                    # Check box (row, col)
                    box_edges = [
                        horizontal[row, col],
                        vertical[row, col],
                        vertical[row+1, col],
                        horizontal[row, col+1]
                    ]
                    if np.sum(box_edges == -1) == 3:
                        boxes_blocked += 1
            elif dir == 'V':
                if row > 0:
                    # Check box (row-1, col)
                    box_edges = [
                        vertical[row-1, col],
                        horizontal[row-1, col],
                        horizontal[row, col],
                        vertical[row, col]
                    ]
                    if np.sum(box_edges == -1) == 3:
                        boxes_blocked += 1
                if row < 4:
                    # Check box (row, col)
                    box_edges = [
                        vertical[row, col],
                        horizontal[row, col],
                        horizontal[row+1, col],
                        vertical[row+1, col]
                    ]
                    if np.sum(box_edges == -1) == 3:
                        boxes_blocked += 1
            if boxes_blocked > max_boxes_blocked:
                max_boxes_blocked = boxes_blocked
                best_move = move
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # If no aggressive or defensive moves, prioritize edges that are part of multiple boxes
    # (e.g., center edges are part of 2 boxes, edges are part of 1 box, corners are part of 0 boxes)
    best_move = None
    max_boxes_affected = -1
    for row, col, dir in legal_moves:
        boxes_affected = 0
        if dir == 'H':
            if col > 0:
                # Box (row, col-1)
                box_edges = [
                    horizontal[row, col-1],
                    vertical[row, col-1],
                    vertical[row+1, col-1],
                    horizontal[row, col]
                ]
                if np.sum(box_edges == 1) + np.sum(box_edges == -1) < 4:
                    boxes_affected += 1
            if col < 4:
                # Box (row, col)
                box_edges = [
                    horizontal[row, col],
                    vertical[row, col],
                    vertical[row+1, col],
                    horizontal[row, col+1]
                ]
                if np.sum(box_edges == 1) + np.sum(box_edges == -1) < 4:
                    boxes_affected += 1
        elif dir == 'V':
            if row > 0:
                # Box (row-1, col)
                box_edges = [
                    vertical[row-1, col],
                    horizontal[row-1, col],
                    horizontal[row, col],
                    vertical[row, col]
                ]
                if np.sum(box_edges == 1) + np.sum(box_edges == -1) < 4:
                    boxes_affected += 1
            if row < 4:
                # Box (row, col)
                box_edges = [
                    vertical[row, col],
                    horizontal[row, col],
                    horizontal[row+1, col],
                    vertical[row+1, col]
                ]
                if np.sum(box_edges == 1) + np.sum(box_edges == -1) < 4:
                    boxes_affected += 1
        if boxes_affected > max_boxes_affected:
            max_boxes_affected = boxes_affected
            best_move = move

    # If still no move, pick a random legal move (fallback)
    if not best_move:
        best_move = np.random.choice(legal_moves)

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
