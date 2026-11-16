
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    size = 10

    # Initialize probability map (higher values = more likely to contain a ship)
    prob_map = np.zeros((size, size))

    # Ship lengths to consider
    ship_lengths = [5, 4, 3, 3, 2]

    # If we have hits, focus on finding the rest of the ship
    hits = np.argwhere(board == 1)
    if len(hits) > 0:
        # Try to find adjacent cells to hits
        for hit in hits:
            row, col = hit
            # Check all four directions
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            for dr, dc in directions:
                # Check in both directions from the hit
                for step in [1, -1]:
                    r, c = row + dr*step, col + dc*step
                    if 0 <= r < size and 0 <= c < size and board[r][c] == 0:
                        # Prioritize cells adjacent to hits
                        prob_map[r][c] += 100

    # If no hits, use probability mapping
    if len(hits) == 0:
        # Create probability map based on ship placement constraints
        for length in ship_lengths:
            # Horizontal placement probability
            for row in range(size):
                for col in range(size - length + 1):
                    valid = True
                    for c in range(col, col + length):
                        if board[row][c] == -1:  # Can't place on misses
                            valid = False
                            break
                    if valid:
                        for c in range(col, col + length):
                            prob_map[row][c] += 1

            # Vertical placement probability
            for col in range(size):
                for row in range(size - length + 1):
                    valid = True
                    for r in range(row, row + length):
                        if board[r][col] == -1:
                            valid = False
                            break
                    if valid:
                        for r in range(row, row + length):
                            prob_map[r][col] += 1

        # Add parity pattern (checkerboard) to spread out initial shots
        for r in range(size):
            for c in range(size):
                if (r + c) % 2 == 0:
                    prob_map[r][c] += 0.1

        # Prioritize center cells
        for r in range(size):
            for c in range(size):
                dist_to_center = abs(r - 4.5) + abs(c - 4.5)
                prob_map[r][c] += (10 - dist_to_center) * 0.5

    # Get all available cells (not hit or missed)
    available = np.argwhere(board == 0)

    # If no available cells (shouldn't happen), return first cell
    if len(available) == 0:
        return (0, 0)

    # Find the cell with highest probability that's available
    max_prob = -1
    best_move = (0, 0)

    for r, c in available:
        if prob_map[r][c] > max_prob:
            max_prob = prob_map[r][c]
            best_move = (r, c)

    return best_move
