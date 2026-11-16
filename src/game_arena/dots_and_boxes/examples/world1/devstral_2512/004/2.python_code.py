
import numpy as np
import random

def policy(horizontal, vertical, capture):
    # Directions for horizontal and vertical edges
    directions = ['H', 'V']

    # First, check for any immediate scoring moves (completing a box)
    for row in range(5):
        for col in range(5):
            # Check horizontal edges
            if horizontal[row, col] == 0:
                # Check if this move would complete any boxes
                boxes_completed = 0
                # Check box above (if exists)
                if row > 0 and col < 4:
                    if (vertical[row-1, col] != 0 and vertical[row-1, col+1] != 0 and
                        horizontal[row-1, col] != 0 and horizontal[row, col] == 0):
                        boxes_completed += 1
                # Check box below (if exists)
                if row < 4 and col < 4:
                    if (vertical[row, col] != 0 and vertical[row, col+1] != 0 and
                        horizontal[row+1, col] != 0 and horizontal[row, col] == 0):
                        boxes_completed += 1
                if boxes_completed > 0:
                    return f"{row},{col},H"

            # Check vertical edges
            if vertical[row, col] == 0:
                # Check if this move would complete any boxes
                boxes_completed = 0
                # Check box to the left (if exists)
                if col > 0 and row < 4:
                    if (horizontal[row, col-1] != 0 and horizontal[row+1, col-1] != 0 and
                        vertical[row, col-1] != 0 and vertical[row, col] == 0):
                        boxes_completed += 1
                # Check box to the right (if exists)
                if col < 4 and row < 4:
                    if (horizontal[row, col] != 0 and horizontal[row+1, col] != 0 and
                        vertical[row, col+1] != 0 and vertical[row, col] == 0):
                        boxes_completed += 1
                if boxes_completed > 0:
                    return f"{row},{col},V"

    # If no immediate scoring moves, look for strategic moves
    # Prioritize center moves first
    center_moves = []
    for row in range(1, 4):
        for col in range(1, 4):
            if horizontal[row, col] == 0:
                center_moves.append(f"{row},{col},H")
            if vertical[row, col] == 0:
                center_moves.append(f"{row},{col},V")

    if center_moves:
        # Randomly select from center moves to avoid predictability
        return random.choice(center_moves)

    # If no center moves, look for edge moves that don't create double crosses
    safe_moves = []
    for row in range(5):
        for col in range(5):
            # Check horizontal edges
            if horizontal[row, col] == 0:
                # Check if this move would create a double cross opportunity for opponent
                double_cross = False
                # Check potential boxes this move affects
                if row > 0 and col < 4:
                    if (vertical[row-1, col] != 0 and vertical[row-1, col+1] != 0 and
                        horizontal[row-1, col] != 0):
                        # This would complete a box, but we already checked for scoring moves
                        pass
                if row < 4 and col < 4:
                    if (vertical[row, col] != 0 and vertical[row, col+1] != 0 and
                        horizontal[row+1, col] != 0):
                        # This would complete a box, but we already checked for scoring moves
                        pass
                safe_moves.append(f"{row},{col},H")

            # Check vertical edges
            if vertical[row, col] == 0:
                # Check if this move would create a double cross opportunity for opponent
                double_cross = False
                # Check potential boxes this move affects
                if col > 0 and row < 4:
                    if (horizontal[row, col-1] != 0 and horizontal[row+1, col-1] != 0 and
                        vertical[row, col-1] != 0):
                        # This would complete a box, but we already checked for scoring moves
                        pass
                if col < 4 and row < 4:
                    if (horizontal[row, col] != 0 and horizontal[row+1, col] != 0 and
                        vertical[row, col+1] != 0):
                        # This would complete a box, but we already checked for scoring moves
                        pass
                safe_moves.append(f"{row},{col},V")

    if safe_moves:
        # Randomly select from safe moves
        return random.choice(safe_moves)

    # If no safe moves found (shouldn't happen as we should always have legal moves)
    # Fallback to any legal move
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                return f"{row},{col},H"
            if vertical[row, col] == 0:
                return f"{row},{col},V"

    # This should never be reached as there should always be legal moves
    return "0,0,H"
