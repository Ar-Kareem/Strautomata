
import numpy as np

# Constants
BOARD_SIZE = 10
SHIP_LENGTHS = [5, 4, 3, 3, 2]
TOTAL_SHIP_CELLS = sum(SHIP_LENGTHS)

# Global state to track mode and target queue
_hunt_mode = True
_target_queue = []
_hit_cells = []
_visited = set()
_shots_fired = 0
_hits_gotten = 0

def policy(board: list[list[int]]) -> tuple[int, int]:
    global _hunt_mode, _target_queue, _hit_cells, _visited, _shots_fired, _hits_gotten

    board_np = np.array(board)

    # Calculate hits so far to determine if we should reset state
    current_hits = np.sum(board_np == 1)
    current_shots = np.sum(board_np != 0)
    
    # If the number of hits changed, we might have hit something
    if current_hits > _hits_gotten:
        # We just got a hit - add to hit cells if not already there
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_np[r, c] == 1 and (r, c) not in _hit_cells:
                    _hit_cells.append((r, c))
                    # Switch to target mode if we were hunting
                    if _hunt_mode:
                        _hunt_mode = False
                        # Generate target queue from this new hit
                        _target_queue = []
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                                if board_np[nr, nc] == 0 and (nr, nc) not in _visited:
                                    _target_queue.append((nr, nc))
        _hits_gotten = current_hits

    # If we are in target mode but queue is empty, check if there are still unsunk ships from hit cells
    if not _hunt_mode and not _target_queue:
        # Try to regenerate target queue from existing hit cells that might not be fully sunk
        for hit_r, hit_c in _hit_cells:
            # Check if this hit cell still has unknown neighbors
            has_unknown = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = hit_r + dr, hit_c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board_np[nr, nc] == 0 and (nr, nc) not in _visited:
                        has_unknown = True
                        break
            if has_unknown:
                # This ship might not be sunk - regenerate target queue from it
                # Determine direction of ship
                directions = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = hit_r + dr, hit_c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        if board_np[nr, nc] == 1:
                            directions.append((dr, dc))
                
                if len(directions) == 0:
                    # Single hit - search all four directions
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = hit_r + dr, hit_c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            if board_np[nr, nc] == 0 and (nr, nc) not in _visited:
                                _target_queue.append((nr, nc))
                else:
                    # Ship direction known - extend in both directions along that axis
                    dr, dc = directions[0]
                    # Go both ways from the hit cell
                    for sign in [1, -1]:
                        for step in range(1, 5):
                            nr = hit_r + sign * dr * step
                            nc = hit_c + sign * dc * step
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                                if board_np[nr, nc] == 0 and (nr, nc) not in _visited:
                                    _target_queue.append((nr, nc))
                                    break
                                elif board_np[nr, nc] == -1 or board_np[nr, nc] == 1:
                                    continue
                                else:
                                    break
                            else:
                                break
                break  # Only process one unsunk ship at a time

        # If still no targets, go back to hunt mode
        if not _target_queue:
            _hunt_mode = True

    # If we are in hunt mode, use parity-based search
    if _hunt_mode:
        # Get all odd-parity cells (row+col is odd) that are unknown
        odd_cells = []
        even_cells = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board_np[r, c] == 0 and (r, c) not in _visited:
                    if (r + c) % 2 == 1:
                        odd_cells.append((r, c))
                    else:
                        even_cells.append((r, c))

        # First, try all odd-parity cells
        if odd_cells:
            # Pick the odd cell with best heat map score (center-weighted)
            best_score = -1
            best_cell = None
            for r, c in odd_cells:
                # Center-weighting: cells closer to center get higher priority
                center_dist = abs(r - 4.5) + abs(c - 4.5)
                score = 20 - center_dist  # Higher score for center cells
                if score > best_score:
                    best_score = score
                    best_cell = (r, c)
            chosen = best_cell
        elif even_cells:
            # If no odd cells left, try even cells
            best_score = -1
            best_cell = None
            for r, c in even_cells:
                center_dist = abs(r - 4.5) + abs(c - 4.5)
                score = 20 - center_dist
                if score > best_score:
                    best_score = score
                    best_cell = (r, c)
            chosen = best_cell
        else:
            # Fallback - should not happen in normal play
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if board_np[r, c] == 0 and (r, c) not in _visited:
                        chosen = (r, c)
                        break
                else:
                    continue
                break
    else:
        # Target mode - pick from queue
        if _target_queue:
            chosen = _target_queue.pop(0)
        else:
            # Fallback to hunt
            _hunt_mode = True
            return policy(board)

    # Mark as visited and increment shots
    _visited.add(chosen)
    _shots_fired += 1

    return chosen
