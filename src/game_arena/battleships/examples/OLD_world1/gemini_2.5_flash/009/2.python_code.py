
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board_np = np.array(board)
    rows, cols = board_np.shape

    # 1. Hunt Mode: If no active ship is being targeted, look for new ships

    # If there are hit cells that are not yet sunk (i.e., surrounded by misses or edge)
    hit_cells = np.argwhere(board_np == 1)
    if len(hit_cells) > 0:
        # Prioritize extending an existing hit
        for r, c in hit_cells:
            # Check adjacent cells for potential extension
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board_np[nr, nc] == 0:
                    return int(nr), int(nc)

    # 2. Advanced Hunt Mode / Probabilistic Shot
    # Calculate probabilities for each unshot cell
    probabilities = np.zeros_like(board_np, dtype=float)

    # Weights for checkerboard pattern to help find smaller ships
    # This also naturally biases away from recently shot areas
    checkerboard_weights = np.zeros_like(board_np, dtype=float)
    for r in range(rows):
        for c in range(cols):
            if (r + c) % 2 == 0:
                checkerboard_weights[r, c] = 1.0  # Prefer black squares

    # Ship lengths: 5, 4, 3, 3, 2
    ship_lengths = [5, 4, 3, 3, 2]

    for r in range(rows):
        for c in range(cols):
            if board_np[r, c] == 0:  # Only consider unshot cells
                current_prob = 0.0
                for length in ship_lengths:
                    # Check horizontal placement
                    for start_c in range(max(0, c - length + 1), min(cols - length + 1, c + 1)):
                        if all(board_np[r, sc] != -1 for sc in range(start_c, start_c + length)):
                            if all(board_np[r, sc] != 1 for sc in range(start_c, start_c + length)): # Avoid placing over confirmed hits for probability
                                current_prob += 1.0 / (length * 2) # Penalize longer ships slightly less

                    # Check vertical placement
                    for start_r in range(max(0, r - length + 1), min(rows - length + 1, r + 1)):
                        if all(board_np[sr, c] != -1 for sr in range(start_r, start_r + length)):
                            if all(board_np[sr, c] != 1 for sr in range(start_r, start_r + length)):
                                current_prob += 1.0 / (length * 2)

                probabilities[r, c] = current_prob * checkerboard_weights[r, c] # Apply checkerboard bias


    # Ensure we don't shoot where we've already shot
    probabilities[board_np != 0] = 0

    # If there are any valid moves based on probability, choose the highest
    if np.any(probabilities > 0):
        max_prob = np.max(probabilities)
        potential_targets = np.argwhere(probabilities == max_prob)

        # If there are multiple cells with the same max probability, pick one randomly
        if len(potential_targets) > 0:
            target_r, target_c = random.choice(potential_targets)
            return int(target_r), int(target_c)

    # Fallback: If no ships are hit, and probabilistic fails (shouldn't happen often)
    # Just shoot randomly at an unshot cell
    available_cells = np.argwhere(board_np == 0)
    if len(available_cells) > 0:
        r, c = random.choice(available_cells)
        return int(r), int(c)

    # Should ideally never reach here if game is ongoing and board is not full
    # But as a failsafe, return a random unshot cell if all else fails
    for r in range(rows):
        for c in range(cols):
            if board_np[r, c] == 0:
                return r, c

    # If somehow all cells are shot (game over), return -1, -1 or handle appropriately
    return -1, -1 # Indicates an error state or game naturally ended
