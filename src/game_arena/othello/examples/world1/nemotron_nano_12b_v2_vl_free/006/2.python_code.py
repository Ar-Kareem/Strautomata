

import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Define all possible directions to check for flips
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1), (1, 0), (1, 1)
    ]

    # Create weights matrix for strategic evaluation
    weights = np.full((8,8), 1.0, dtype=np.float64)
    # Corners are assigned the highest value
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    for r, c in corners:
        weights[r, c] = 100.0
    # Edges (excluding corners) have higher value
    edges = []
    # Top and bottom rows, excluding corners
    edges.extend([(0, c) for c in range(1,7)])
    edges.extend([(7, c) for c in range(1,7)])
    # Left and right columns, excluding corners
    edges.extend([(r, 0) for r in range(1,7)])
    edges.extend([(r, 7) for r in range(1,7)])
    # Convert edges set (to avoid duplicates)
    edges = list(set(edges))
    # Assign higher weights to edge cells
    for r, c in edges:
        weights[r, c] = 50.0

    # Find all valid moves for current player
    valid_moves = []
    for r in range(8):
        for c in range(8):
            # Skip occupied cells
            if you[r, c] != 0:
                continue
            # Check if current cell is empty for both players
            if opponent[r, c] != 0:
                continue
            # Check each direction for possible flips
            for dr, dc in directions:
                x, y = r + dr, c + dc
                found_opponent = False
                flipped = []
                while 0 <= x < 8 and 0 <= y < 8:
                    if opponent[x, y] == 1:
                        flipped.append((x, y))
                        found_opponent = True
                        x += dr
                        y += dc
                    elif you[x, y] == 1:
                        if found_opponent:
                            valid_moves.append((r, c))
                            break  # Found valid direction, move on to next cell
                        else:
                            break  # No flip possible in this direction
                    else:
                        break  # Empty cell, no flip possible
                else:
                    # Out of bounds reached, check flipped
                    if found_opponent and flipped:
                        # Cannot reach own stone, invalid direction
                        pass
    # Remove duplicates and sort in row-major order
    valid_moves = list(set(valid_moves))
    valid_moves.sort()

    # Return pass if no valid moves
    if not valid_moves:
        return "pass"

    # Evaluate each valid move
    scored_moves = []
    for r, c in valid_moves:
        score = weights[r, c]
        sum_flips = 0
        for dr, dc in directions:
            x, y = r + dr, c + dc
            flipped = []
            found_opponent = False
            while 0 <= x < 8 and 0 <= y < 8:
                if opponent[x, y] == 1:
                    flipped.append((x, y))
                    found_opponent = True
                    x += dr
                    y += dc
                elif you[x, y] == 1:
                    if found_opponent:
                        # Add the weight of flipped squares
                        sum_flips += sum(weights[i][j] for i, j in flipped)
                        break
                    else:
                        break  # No flip in this direction
                else:
                    break  # Empty cell, stop
                # Move further in direction
                x += dr
                y += dc
        # Total score includes current position weight and flipped sum
        total_score = score + sum_flips
        scored_moves.append((total_score, r, c))

    # Sort moves by score descending and pick top move
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    best_move = scored_moves[0]

    # Convert to algebraic notation
    col = chr(ord('a') + best_move[2])
    row = str(best_move[1] + 1)
    return f"{col}{row}"

