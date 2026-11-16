
import random

# Global state to track hunt positions, target probes, and sunk statuses.
# Since the function is called per turn, we use module-level vars for persistence.
_hunt_index = 0
_hunt_order = [(r, c) for r in range(10) for c in range(10) if (r + c) % 2 == 0]
_target_queue = []
_sink_lengths = {5: False, 4: False, 3: False, 2: False}  # Track sunk ships by size

def _get_adjacent_moves(row, col):
    """Get legal adjacent cells."""
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return [(row + dr, col + dc) for dr, dc in directions if 0 <= row + dr < 10 and 0 <= col + dc < 10]

def _is_ship_sunk(board, start_row, start_col, direction):
    """Check if a ship in a given direction is sunk (all cells hit)."""
    dr, dc = direction
    length = 0
    r, c = start_row, start_col
    while 0 <= r < 10 and 0 <= c < 10 and board[r][c] in [-1, 1]:
        if board[r][c] == 1:
            length += 1
        r += dr
        c += dc
    return length in [5, 4, 3, 2], length  # (is_sunk, length)

def policy(board):
    global _hunt_index, _target_queue, _sink_lengths
    
    # First, update target queue with hits and their neighbors.
    new_targets = []
    hit_positions = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]
    
    for hit_r, hit_c in hit_positions:
        adj = _get_adjacent_moves(hit_r, hit_c)
        for nr, nc in adj:
            if board[nr][nc] == 0 and (nr, nc) not in [pos for pos in _target_queue]:  # Avoid duplicates
                new_targets.append((nr, nc, hit_r, hit_c))  # Track source for sink checks
    # Prioritize new_targets at front of queue.
    _target_queue = new_targets + [pos for pos in _target_queue if pos not in [(nr, nc, sr, sc) for nr, nc, sr, sc in new_targets]]
    
    # Target mode: if we have probes, use them, but check for sinks.
    while _target_queue:
        nr, nc, source_r, source_c = _target_queue[0]
        _target_queue.pop(0)
        if board[nr][nc] == 0:  # Still unknown
            # Quick sink check: if the direction suggests a fully sunk ship, mark it.
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                if (nr - source_r, nc - source_c) == (dr, dc):
                    sunk, length = _is_ship_sunk(board, source_r, source_c, (dr, dc))
                    if sunk and not _sink_lengths[length]:
                        _sink_lengths[length] = True
                        # Remove pending probes on this line.
                        _target_queue = [pos for pos in _target_queue if not (abs(pos[0] - source_r) == abs(pos[1] - source_c) or pos[0] == source_r)]
                    break
            return (nr, nc)
    
    # Hunt mode: scan parity cells in order, skipping explored ones.
    while _hunt_index < len(_hunt_order):
        row, col = _hunt_order[_hunt_index]
        _hunt_index += 1
        if board[row][col] == 0:
            return (row, col)
    
    # Fallback: random unexplored cell (shouldn't happen with 50 even cells).
    unexplored = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    return random.choice(unexplored) if unexplored else (0, 0)  # Safety, though invalid
