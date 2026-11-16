
import numpy as np
from typing import List, Tuple

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Policy for Dots and Boxes on a 4x4 grid.
    Returns the best move as a string 'row,col,dir' (e.g., '1,2,H').
    """
    # Generate all legal moves (edges not yet drawn)
    legal_moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))

    if not legal_moves:
        raise ValueError("No legal moves available. Game is over.")

    # Evaluate each legal move using greedy heuristics
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        row, col, dir = move
        score = evaluate_move(horizontal, vertical, capture, row, col, dir)
        if score > best_score:
            best_score = score
            best_move = move

    # If no move is clearly better (e.g., all scores are equal), pick randomly among top moves
    if best_move is None:
        best_move = legal_moves[0]

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

def evaluate_move(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, row: int, col: int, dir: str) -> int:
    """
    Evaluates a move by simulating its effect and scoring based on:
    - Completing a box for me (highest priority).
    - Blocking opponent's potential boxes.
    - Creating threats for the opponent.
    - Randomness for neutral moves.
    """
    score = 0
    temp_horizontal = horizontal.copy()
    temp_vertical = vertical.copy()
    temp_capture = capture.copy()

    # Simulate the move
    if dir == 'H':
        temp_horizontal[row, col] = 1
    else:  # dir == 'V'
        temp_vertical[row, col] = 1

    # Check if the move completes any boxes for me
    boxes_completed = check_box_completion(temp_horizontal, temp_vertical, temp_capture, 1)
    if boxes_completed > 0:
        score += 100 * boxes_completed  # High priority for completing boxes

    # Check if the move blocks opponent's potential boxes
    opponent_boxes_blocked = check_box_completion(temp_horizontal, temp_vertical, temp_capture, -1)
    if opponent_boxes_blocked > 0:
        score += 50 * opponent_boxes_blocked  # Block opponent's boxes

    # Check if the move creates a threat (opponent has 3 edges in a box)
    threats_created = check_threats(temp_horizontal, temp_vertical, 1)
    if threats_created > 0:
        score += 20 * threats_created  # Create threats for opponent

    # Prefer moves that are part of fewer potential boxes (e.g., perimeter edges)
    potential_boxes = count_potential_boxes(temp_horizontal, temp_vertical, row, col, dir)
    score -= 10 * potential_boxes  # Lower score for moves that open more boxes

    # Prefer center moves (rows/cols 1-3) to limit opponent's opportunities
    if 1 <= row <= 3 and 1 <= col <= 3:
        score += 5  # Small bonus for center moves

    return score

def check_box_completion(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, player: int) -> int:
    """
    Checks if a move completes any boxes for the given player.
    Returns the number of boxes completed.
    """
    completed_boxes = 0
    # Iterate over all boxes (rows 0-3, cols 0-3)
    for row in range(4):
        for col in range(4):
            if capture[row, col] == 0:  # Box is unclaimed
                # Check if the player has all 4 edges of the box
                edges = [
                    horizontal[row, col],    # Top edge
                    horizontal[row, col + 1], # Bottom edge
                    vertical[row, col],     # Left edge
                    vertical[row + 1, col]   # Right edge
                ]
                if all(edge == player for edge in edges):
                    completed_boxes += 1
    return completed_boxes

def check_threats(horizontal: np.ndarray, vertical: np.ndarray, player: int) -> int:
    """
    Checks if a move creates a threat (opponent has 3 edges in a box).
    Returns the number of threats created.
    """
    threats = 0
    # Iterate over all boxes (rows 0-3, cols 0-3)
    for row in range(4):
        for col in range(4):
            # Check if the opponent has exactly 3 edges of the box
            edges = [
                horizontal[row, col],    # Top edge
                horizontal[row, col + 1], # Bottom edge
                vertical[row, col],     # Left edge
                vertical[row + 1, col]   # Right edge
            ]
            opponent_edges = sum(1 for edge in edges if edge == -player)
            if opponent_edges == 3:
                threats += 1
    return threats

def count_potential_boxes(horizontal: np.ndarray, vertical: np.ndarray, row: int, col: int, dir: str) -> int:
    """
    Counts how many boxes could be completed by drawing the given edge.
    Returns the count of potential boxes.
    """
    potential = 0
    if dir == 'H':
        # This edge is part of two boxes: (row, col) and (row-1, col)
        if row > 0 and col > 0 and col < 4 and row < 4:
            potential += 2
        elif row == 0 or row == 4 or col == 0 or col == 4:
            potential += 1
    else:  # dir == 'V'
        # This edge is part of two boxes: (row, col) and (row, col-1)
        if row > 0 and row < 4 and col > 0 and col < 4:
            potential += 2
        elif row == 0 or row == 4 or col == 0 or col == 4:
            potential += 1
    return potential
