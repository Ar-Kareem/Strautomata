
import numpy as np

# Initialize a probability map for the grid
def initialize_probability_map():
    grid_size = 10
    prob_map = np.zeros((grid_size, grid_size))

    # Calculate the probability for each cell
    for i in range(grid_size):
        for j in range(grid_size):
            # The probability is higher for cells that can be covered by more ship placements
            # For simplicity, we'll use a heuristic that favors central cells
            prob_map[i, j] = (min(i, grid_size - 1 - i) + 1) * (min(j, grid_size - 1 - j) + 1)

    # Normalize the probability map
    prob_map = prob_map / np.sum(prob_map)
    return prob_map

# Global probability map
prob_map = initialize_probability_map()

def policy(board: list[list[int]]) -> tuple[int, int]:
    global prob_map

    board = np.array(board)
    grid_size = 10

    # Find all hits on the board
    hits = np.argwhere(board == 1)

    # If there are hits, enter hunt mode
    if len(hits) > 0:
        # For each hit, check adjacent cells
        for hit in hits:
            row, col = hit
            # Check adjacent cells (up, down, left, right)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                r, c = row + dr, col + dc
                if 0 <= r < grid_size and 0 <= c < grid_size and board[r, c] == 0:
                    return (r, c)

    # If no hits or no adjacent cells available, use the probability map
    # Create a mask for cells that have not been targeted yet (board == 0)
    mask = (board == 0)
    if np.sum(mask) == 0:
        # All cells have been targeted, return a random cell (should not happen in practice)
        return (np.random.randint(0, grid_size), np.random.randint(0, grid_size))

    # Apply the mask to the probability map
    masked_prob = prob_map * mask

    # Normalize the masked probability map
    if np.sum(masked_prob) > 0:
        masked_prob = masked_prob / np.sum(masked_prob)
    else:
        # If all probabilities are zero (unlikely), return a random cell
        return (np.random.randint(0, grid_size), np.random.randint(0, grid_size))

    # Flatten the probability map and choose a cell based on the probability
    flat_prob = masked_prob.flatten()
    chosen_index = np.random.choice(grid_size * grid_size, p=flat_prob)
    row, col = np.unravel_index(chosen_index, (grid_size, grid_size))

    return (row, col)
