
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    width, height = 10, 10
    potential_targets = []
    
    # Collect all unshot cells
    for r in range(height):
        for c in range(width):
            if board[r][c] == 0:  # Only consider unshot cells
                potential_targets.append((r, c))
    
    if not potential_targets:
        raise RuntimeError("No more cells to target!")

    # Look for hits to target around
    targets_with_hits = []
    for r in range(height):
        for c in range(width):
            if board[r][c] == 1:  # Found a hit
                # Check the neighbors in a 3x3 area around the hit
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        new_r, new_c = r + dr, c + dc
                        if 0 <= new_r < height and 0 <= new_c < width and board[new_r][new_c] == 0:
                            targets_with_hits.append((new_r, new_c))
    
    # We prefer targets around hits if any
    if targets_with_hits:
        return random.choice(targets_with_hits)
    
    # Fallback to random unshot target
    return random.choice(potential_targets)
