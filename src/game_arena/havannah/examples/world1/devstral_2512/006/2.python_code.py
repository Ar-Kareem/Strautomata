
import numpy as np
from collections import deque

# Directions for hexagonal neighbors (even-r offset)
HEX_DIRECTIONS = [
    (-1, 0), (-1, 1),  # up-left, up-right
    (0, -1), (0, 1),   # left, right
    (1, 0), (1, 1)     # down-left, down-right
]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    board_size = len(valid_mask)
    me_set = set(me)
    opp_set = set(opp)
    empty_cells = [(r, c) for r in range(board_size) for c in range(board_size)
                  if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]

    # Check for immediate winning moves
    for move in empty_cells:
        if is_winning_move(move, me_set | {move}, opp_set, board_size):
            return move

    # Check for opponent winning moves to block
    for move in empty_cells:
        if is_winning_move(move, opp_set | {move}, me_set, board_size):
            return move

    # Evaluate all possible moves with heuristic
    best_move = None
    best_score = -float('inf')

    for move in empty_cells:
        score = evaluate_move(move, me_set, opp_set, board_size)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def is_winning_move(move, player_stones, opponent_stones, board_size):
    # Check if adding this move creates a winning condition
    new_stones = player_stones | {move}

    # Check for ring
    if has_ring(new_stones, opponent_stones, board_size):
        return True

    # Check for bridge
    if has_bridge(new_stones, board_size):
        return True

    # Check for fork
    if has_fork(new_stones, board_size):
        return True

    return False

def has_ring(stones, opponent_stones, board_size):
    # Check if stones form a ring (loop)
    visited = set()
    for stone in stones:
        if stone not in visited:
            if _dfs_ring(stone, None, stones, opponent_stones, visited, board_size):
                return True
    return False

def _dfs_ring(current, parent, stones, opponent_stones, visited, board_size):
    visited.add(current)
    neighbors = get_hex_neighbors(current, board_size)

    for neighbor in neighbors:
        if neighbor in opponent_stones:
            continue
        if neighbor not in stones:
            continue
        if neighbor == parent:
            continue
        if neighbor in visited:
            return True
        if _dfs_ring(neighbor, current, stones, opponent_stones, visited, board_size):
            return True
    return False

def has_bridge(stones, board_size):
    # Check if stones connect two corners
    corners = [(0, 0), (0, board_size-1), (board_size-1, 0), (board_size-1, board_size-1)]
    connected_corners = set()

    for corner in corners:
        if corner in stones:
            connected_corners.add(corner)

    if len(connected_corners) < 2:
        return False

    # Check connectivity between corners
    for i, corner1 in enumerate(connected_corners):
        for corner2 in list(connected_corners)[i+1:]:
            if is_connected(corner1, corner2, stones, board_size):
                return True
    return False

def has_fork(stones, board_size):
    # Check if stones connect three edges (not corners)
    edges = {
        'top': [(0, c) for c in range(1, board_size-1)],
        'bottom': [(board_size-1, c) for c in range(1, board_size-1)],
        'left': [(r, 0) for r in range(1, board_size-1)],
        'right': [(r, board_size-1) for r in range(1, board_size-1)],
        'top_left': [(0, 0)],  # corners are not considered edges
        'top_right': [(0, board_size-1)],
        'bottom_left': [(board_size-1, 0)],
        'bottom_right': [(board_size-1, board_size-1)]
    }

    connected_edges = set()
    for edge_name, edge_cells in edges.items():
        if edge_name in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
            continue
        for cell in edge_cells:
            if cell in stones:
                connected_edges.add(edge_name)
                break

    if len(connected_edges) < 3:
        return False

    # Check if any three edges are connected
    edge_list = list(connected_edges)
    for i in range(len(edge_list)):
        for j in range(i+1, len(edge_list)):
            for k in range(j+1, len(edge_list)):
                e1, e2, e3 = edge_list[i], edge_list[j], edge_list[k]
                if (is_edge_connected(e1, e2, stones, board_size) and
                    is_edge_connected(e2, e3, stones, board_size) and
                    is_edge_connected(e1, e3, stones, board_size)):
                    return True
    return False

def is_edge_connected(edge1, edge2, stones, board_size):
    # Get representative cells for each edge
    edge_cells = {
        'top': [(0, c) for c in range(1, board_size-1)],
        'bottom': [(board_size-1, c) for c in range(1, board_size-1)],
        'left': [(r, 0) for r in range(1, board_size-1)],
        'right': [(r, board_size-1) for r in range(1, board_size-1)]
    }

    cells1 = [c for c in edge_cells[edge1] if c in stones]
    cells2 = [c for c in edge_cells[edge2] if c in stones]

    if not cells1 or not cells2:
        return False

    # Check if any cell from edge1 is connected to any cell from edge2
    for c1 in cells1:
        for c2 in cells2:
            if is_connected(c1, c2, stones, board_size):
                return True
    return False

def is_connected(start, end, stones, board_size):
    if start == end:
        return True
    visited = set()
    queue = deque([start])
    visited.add(start)

    while queue:
        current = queue.popleft()
        for neighbor in get_hex_neighbors(current, board_size):
            if neighbor == end:
                return True
            if neighbor in stones and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return False

def get_hex_neighbors(pos, board_size):
    r, c = pos
    neighbors = []
    for dr, dc in HEX_DIRECTIONS:
        nr, nc = r + dr, c + dc
        # Adjust for even-r offset coordinates
        if r % 2 == 0 and dc == 1:
            nc = c
        if 0 <= nr < board_size and 0 <= nc < board_size:
            neighbors.append((nr, nc))
    return neighbors

def evaluate_move(move, me_stones, opp_stones, board_size):
    score = 0
    r, c = move

    # Center control bonus
    center_dist = max(abs(r - board_size/2), abs(c - board_size/2))
    score += (board_size/2 - center_dist) * 0.5

    # Corner proximity bonus (for bridge potential)
    corners = [(0, 0), (0, board_size-1), (board_size-1, 0), (board_size-1, board_size-1)]
    min_corner_dist = min(abs(r - cr) + abs(c - cc) for cr, cc in corners)
    score += (5 - min_corner_dist) * 0.3

    # Edge proximity bonus (for fork potential)
    if r == 0 or r == board_size-1 or c == 0 or c == board_size-1:
        score += 1.0
    elif r == 1 or r == board_size-2 or c == 1 or c == board_size-2:
        score += 0.5

    # Connectivity bonus
    neighbors = get_hex_neighbors(move, board_size)
    my_neighbors = sum(1 for n in neighbors if n in me_stones)
    opp_neighbors = sum(1 for n in neighbors if n in opp_stones)

    score += my_neighbors * 2.0
    score -= opp_neighbors * 1.5

    # Potential bridge/fork/ring formation bonus
    new_stones = me_stones | {move}

    # Check for potential bridges
    corners_connected = 0
    corner_pairs = [((0,0),(0,board_size-1)), ((0,0),(board_size-1,0)),
                    ((0,board_size-1),(board_size-1,board_size-1)),
                    ((board_size-1,0),(board_size-1,board_size-1))]
    for c1, c2 in corner_pairs:
        if (c1 in new_stones or c2 in new_stones) and is_connected(c1, c2, new_stones, board_size):
            corners_connected += 1
    score += corners_connected * 3.0

    # Check for potential forks
    edges_touched = 0
    if any(c in new_stones for c in [(0, c) for c in range(1, board_size-1)]):
        edges_touched += 1
    if any(c in new_stones for c in [(board_size-1, c) for c in range(1, board_size-1)]):
        edges_touched += 1
    if any(c in new_stones for c in [(r, 0) for r in range(1, board_size-1)]):
        edges_touched += 1
    if any(c in new_stones for c in [(r, board_size-1) for r in range(1, board_size-1)]):
        edges_touched += 1
    score += edges_touched * 1.5

    # Check for potential rings
    # Simplified check - count how many of my stones would be in a potential ring
    ring_potential = 0
    for stone in new_stones:
        if _has_potential_ring(stone, new_stones, opp_stones, board_size):
            ring_potential += 1
    score += ring_potential * 2.0

    return score

def _has_potential_ring(stone, stones, opponent_stones, board_size):
    # Check if this stone could be part of a ring
    visited = set()
    queue = deque([stone])
    visited.add(stone)
    ring_size = 0

    while queue:
        current = queue.popleft()
        ring_size += 1
        for neighbor in get_hex_neighbors(current, board_size):
            if neighbor in opponent_stones:
                continue
            if neighbor in stones and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    # A potential ring needs at least 6 stones to enclose something
    return ring_size >= 6
