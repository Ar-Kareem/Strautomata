
import numpy as np

def policy(horizontal, vertical, capture):
    # First check for immediate winning moves (completing a box)
    for row in range(4):
        for col in range(4):
            # Check if this box can be completed with one move
            h1 = horizontal[row, col]
            h2 = horizontal[row+1, col]
            v1 = vertical[row, col]
            v2 = vertical[row, col+1]

            # Count how many edges are already drawn
            edges = [h1, h2, v1, v2]
            zeros = edges.count(0)

            if zeros == 1:
                # Find which edge is missing
                if h1 == 0:
                    return f"{row},{col},H"
                elif h2 == 0:
                    return f"{row+1},{col},H"
                elif v1 == 0:
                    return f"{row},{col},V"
                elif v2 == 0:
                    return f"{row},{col+1},V"

    # Check for potential double-crosses to block
    for row in range(4):
        for col in range(4):
            # Check if opponent has 3 edges of a box
            h1 = horizontal[row, col]
            h2 = horizontal[row+1, col]
            v1 = vertical[row, col]
            v2 = vertical[row, col+1]

            # Count opponent's edges (negative values)
            opponent_edges = sum(1 for edge in [h1, h2, v1, v2] if edge == -1)

            if opponent_edges == 3:
                # Find the missing edge and block it
                if h1 == 0:
                    return f"{row},{col},H"
                elif h2 == 0:
                    return f"{row+1},{col},H"
                elif v1 == 0:
                    return f"{row},{col},V"
                elif v2 == 0:
                    return f"{row},{col+1},V"

    # If no immediate moves, implement a control strategy
    # Prefer center moves and moves that create balanced positions
    center_priority = [
        (2, 2, 'H'), (2, 2, 'V'),  # Center
        (1, 1, 'H'), (1, 1, 'V'),  # Near center
        (1, 2, 'H'), (1, 2, 'V'),
        (2, 1, 'H'), (2, 1, 'V'),
        (2, 3, 'H'), (2, 3, 'V'),
        (3, 2, 'H'), (3, 2, 'V'),
    ]

    for row, col, direction in center_priority:
        if direction == 'H' and horizontal[row, col] == 0:
            return f"{row},{col},H"
        elif direction == 'V' and vertical[row, col] == 0:
            return f"{row},{col},V"

    # If all else fails, make any legal move
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                return f"{row},{col},H"
            if vertical[row, col] == 0:
                return f"{row},{col},V"

    # This should never happen as there should always be legal moves
    return "0,0,H"
