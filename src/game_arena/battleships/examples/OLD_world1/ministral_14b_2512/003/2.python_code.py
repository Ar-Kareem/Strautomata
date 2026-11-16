
import numpy as np
import random
from collections import defaultdict

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert the board to a numpy array for easier manipulation
    board_np = np.array(board)
    n = board_np.shape[0]

    # Find all unknown cells (0)
    unknown_cells = np.argwhere(board_np == 0)

    # If there are no unknown cells, return None (shouldn't happen per problem statement)
    if len(unknown_cells) == 0:
        return (0, 0)  # fallback, though problem says we only fire at unknown cells

    # Get all hit cells (1)
    hit_cells = np.argwhere(board_np == 1)

    # If no hits yet, just pick a random unknown cell
    if len(hit_cells) == 0:
        return tuple(unknown_cells[random.randint(0, len(unknown_cells)-1)])

    # If we have hits, try to find potential ship continuations
    # We'll look for adjacent cells to hits that are unknown

    # Create a dictionary to track potential ship directions
    ship_directions = defaultdict(set)

    # For each hit, check its neighbors
    for hit in hit_cells:
        row, col = hit
        # Check all 8 possible directions
        for dr, dc in [(-1,-1), (-1,0), (-1,1),
                       (0,-1),          (0,1),
                       (1,-1),  (1,0), (1,1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < n and 0 <= nc < n and board_np[nr, nc] == 0:
                ship_directions[(row, col)].add((dr, dc))

    # If we found potential directions, prioritize those
    if ship_directions:
        # Find the hit with the most potential directions
        best_hit = max(ship_directions.items(), key=lambda x: len(x[1]))[0]
        row, col = best_hit
        # Try to find the most promising direction
        directions = ship_directions[(row, col)]
        # Sort directions by how many unknown cells they lead to
        direction_scores = []
        for dr, dc in directions:
            score = 0
            r, c = row + dr, col + dc
            while 0 <= r < n and 0 <= c < n and board_np[r, c] == 0:
                score += 1
                r += dr
                c += dc
            direction_scores.append((score, dr, dc))

        # Sort by score descending
        direction_scores.sort(reverse=True, key=lambda x: x[0])

        # Try the best direction
        for score, dr, dc in direction_scores:
            r, c = row + dr, col + dc
            if 0 <= r < n and 0 <= c < n and board_np[r, c] == 0:
                return (r, c)

    # If no clear direction, pick a random unknown cell
    return tuple(unknown_cells[random.randint(0, len(unknown_cells)-1)])
