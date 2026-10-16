
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = len(board)
    board = np.array(board)
    
    # If first move, start near the center
    if np.all(board == 0):
        return (n // 2, n // 2)
    
    # Find all hits that haven't been sunk yet (adjacent cells not all cleared)
    hit_positions = list(zip(*np.where(board == 1)))
    
    if hit_positions:
        # Try to find the orientation of the ship
        for (r, c) in hit_positions:
            # Check adjacent cells
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n:
                    # If we have a hit next to another hit, check in that direction
                    if board[nr][nc] == 1:
                        # Check further in this direction
                        for step in [2, -1, -2, 1]:  # Try both directions
                            tr, tc = r + dr * step, c + dc * step
                            if 0 <= tr < n and 0 <= tc < n and board[tr][tc] == 0:
                                return (tr, tc)
                        # If not found in primary direction, try perpendicular
                        for sdr, sdc in [(dc, dr), (-dc, -dr)]:
                            tr, tc = r + sdr, c + sdc
                            if 0 <= tr < n and 0 <= tc < n and board[tr][tc] == 0:
                                return (tr, tc)
                    elif board[nr][nc] == 0:
                        return (nr, nc)
    
    # If no hits to follow up on, use probability density
    # Initialize probabilities
    prob = np.zeros((n, n))
    
    # Calculate probabilities for all possible ship placements
    for ship_len in [2, 3, 3, 4, 5]:
        # Horizontal placements
        for r in range(n):
            for c in range(n - ship_len + 1):
                if np.all(board[r, c:c+ship_len] <= 0):  # No misses in this segment
                    prob[r, c:c+ship_len] += 1
        
        # Vertical placements
        for r in range(n - ship_len + 1):
            for c in range(n):
                if np.all(board[r:r+ship_len, c] <= 0):  # No misses in this segment
                    prob[r:r+ship_len, c] += 1
    
    # Zero out already tried positions
    prob[board != 0] = 0
    
    # If all probabilities are zero (shouldn't happen), pick random unknown cell
    if np.sum(prob) == 0:
        unknown = np.argwhere(board == 0)
        return tuple(unknown[np.random.choice(len(unknown))])
    
    # Find the maximum probability position
    max_prob_pos = np.unravel_index(np.argmax(prob), prob.shape)
    return (max_prob_pos[0], max_prob_pos[1])
