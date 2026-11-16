
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # First, check for any immediate captures (moves that complete a box)
    for row in range(5):
        for col in range(5):
            # Check horizontal edges
            if horizontal[row, col] == 0:
                # Check if this move would complete any boxes
                # For horizontal edge at (row, col), it can complete boxes above and below
                boxes_completed = 0
                # Check box above (if exists)
                if row > 0:
                    if (vertical[row-1, col] != 0 and vertical[row-1, col+1] != 0 and
                        horizontal[row-1, col] != 0 and horizontal[row, col] == 0):
                        boxes_completed += 1
                # Check box below (if exists)
                if row < 4:
                    if (vertical[row, col] != 0 and vertical[row, col+1] != 0 and
                        horizontal[row+1, col] != 0 and horizontal[row, col] == 0):
                        boxes_completed += 1
                if boxes_completed > 0:
                    return f"{row},{col},H"

            # Check vertical edges
            if vertical[row, col] == 0:
                # Check if this move would complete any boxes
                # For vertical edge at (row, col), it can complete boxes left and right
                boxes_completed = 0
                # Check box to the left (if exists)
                if col > 0:
                    if (horizontal[row, col-1] != 0 and horizontal[row+1, col-1] != 0 and
                        vertical[row, col-1] != 0 and vertical[row, col] == 0):
                        boxes_completed += 1
                # Check box to the right (if exists)
                if col < 4:
                    if (horizontal[row, col] != 0 and horizontal[row+1, col] != 0 and
                        vertical[row, col+1] != 0 and vertical[row, col] == 0):
                        boxes_completed += 1
                if boxes_completed > 0:
                    return f"{row},{col},V"

    # If no immediate captures, look for strategic moves
    # Prioritize center moves and avoid giving opponent easy captures
    strategic_moves = []

    # Evaluate all possible moves
    for row in range(5):
        for col in range(5):
            # Check horizontal edges
            if horizontal[row, col] == 0:
                # Calculate how many boxes this move would complete for opponent
                opponent_captures = 0
                # Check box above
                if row > 0:
                    if (vertical[row-1, col] != 0 and vertical[row-1, col+1] != 0 and
                        horizontal[row-1, col] != 0 and horizontal[row, col] == 0):
                        # Check if opponent would get this box
                        if capture[row-1, col] == 0:
                            opponent_captures += 1
                # Check box below
                if row < 4:
                    if (vertical[row, col] != 0 and vertical[row, col+1] != 0 and
                        horizontal[row+1, col] != 0 and horizontal[row, col] == 0):
                        if capture[row, col] == 0:
                            opponent_captures += 1

                # Calculate strategic value (higher for center, lower if gives opponent captures)
                # Center distance (lower is better)
                center_dist = abs(row - 2) + abs(col - 2)
                # Avoid moves that give opponent captures
                if opponent_captures == 0:
                    strategic_value = 10 - center_dist
                else:
                    strategic_value = 1 - opponent_captures

                strategic_moves.append((strategic_value, f"{row},{col},H"))

            # Check vertical edges
            if vertical[row, col] == 0:
                # Calculate how many boxes this move would complete for opponent
                opponent_captures = 0
                # Check box to the left
                if col > 0:
                    if (horizontal[row, col-1] != 0 and horizontal[row+1, col-1] != 0 and
                        vertical[row, col-1] != 0 and vertical[row, col] == 0):
                        if capture[row, col-1] == 0:
                            opponent_captures += 1
                # Check box to the right
                if col < 4:
                    if (horizontal[row, col] != 0 and horizontal[row+1, col] != 0 and
                        vertical[row, col+1] != 0 and vertical[row, col] == 0):
                        if capture[row, col] == 0:
                            opponent_captures += 1

                # Calculate strategic value
                center_dist = abs(row - 2) + abs(col - 2)
                if opponent_captures == 0:
                    strategic_value = 10 - center_dist
                else:
                    strategic_value = 1 - opponent_captures

                strategic_moves.append((strategic_value, f"{row},{col},V"))

    # Sort moves by strategic value (highest first)
    strategic_moves.sort(reverse=True, key=lambda x: x[0])

    # Return the best strategic move if available
    if strategic_moves:
        return strategic_moves[0][1]

    # If no strategic moves found (shouldn't happen as we checked all edges)
    # Fallback to random legal move
    legal_moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append(f"{row},{col},H")
            if vertical[row, col] == 0:
                legal_moves.append(f"{row},{col},V")

    return random.choice(legal_moves)
