
import numpy as np
from collections import deque

# Hexagonal neighbor directions for Havannah board (row, col)
# For a hex grid, neighbors are computed in 6 directions based on the parity of the row.
# However, since we work on a 2D array mask and don't wrap around, we specify neighbors directly.
# Directions are defined relative to (row, col) with adjustments for hex grid.
# For even row (e.g., row = 4): [(-1,-1), (-1,0), (0,-1), (0,1), (1,-1), (1,0)]
# For odd row (e.g., row = 5): [(-1,0), (-1,1), (0,-1), (0,1), (1,0), (1,1)]

def get_neighbors(r, c):
    if r % 2 == 0:
        return [(r-1, c-1), (r-1, c), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)]
    else:
        return [(r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c), (r+1, c+1)]

def is_valid(pos, size=15):
    r, c = pos
    return 0 <= r < size and 0 <= c < size

def get_valid_neighbors(r, c, valid_mask, size=15):
    neighbors = get_neighbors(r, c)
    return [(nr, nc) for nr, nc in neighbors if is_valid((nr, nc), size) and valid_mask[nr][nc]]

# Helper function to check if a move completes a win (simple path-based heuristic for ring, fork, bridge)
# In practice, full win-checking is complex. For now, use a simplified path traversal.
# This is a heuristic for immediate and strong threats.

# A simplified BFS-based path tracing to see if a move helps toward a win
def bfs_path_length(board, start_r, start_c, player_id, target_length=4):
    visited = set()
    queue = deque([(start_r, start_c, 1)])  # (row, col, path_length)
    visited.add((start_r, start_c))
    max_len = 1

    while queue:
        r, c, l = queue.popleft()
        if l > max_len:
            max_len = l
        if l >= target_length:
            return l
        for nr, nc in get_neighbors(r, c):
            if is_valid((nr, nc)) and (nr, nc) not in visited and board[nr][nc] == player_id:
                visited.add((nr, nc))
                queue.append((nr, nc, l + 1))
    return max_len

# Estimate future connectivity (for scoring)
def evaluate_position(board, r, c, player_id, opp_id, valid_mask):
    score = 0
    board[r][c] = player_id
    # Evaluate extension of existing paths
    my_len = bfs_path_length(board, r, c, player_id)
    score += my_len * 2

    # Evaluate blocking opponent
    board[r][c] = opp_id
    opp_len = bfs_path_length(board, r, c, opp_id)
    score += opp_len * 3  # blocking is more valuable
    board[r][c] = 0  # reset

    # Prefer moves near center
    center_r, center_c = 7, 7
    dist = abs(r - center_r) + abs(c - center_c)
    score += max(0, 10 - dist)

    return score

def build_board(me, opp, size=15):
    board = np.zeros((size, size), dtype=int)
    for r, c in me:
        board[r][c] = 1
    for r, c in opp:
        board[r][c] = 2
    return board

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    board = build_board(me, opp)

    # Collect all valid moves
    valid_moves = [(r, c) for r in range(15) for c in range(15) if valid_mask[r][c]]

    # Immediate win check
    for r, c in valid_moves:
        board[r][c] = 1
        # Simplified win check: if placing here creates a significant path
        if bfs_path_length(board, r, c, 1, 6) >= 6:  # ring/fork approximation
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Block opponent win
    for r, c in valid_moves:
        board[r][c] = 2
        if bfs_path_length(board, r, c, 2, 6) >= 6:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Evaluate all valid moves and pick the best
    best_move = valid_moves[0]
    best_score = -1
    for r, c in valid_moves:
        score = evaluate_position(board, r, c, 1, 2, valid_mask)
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
