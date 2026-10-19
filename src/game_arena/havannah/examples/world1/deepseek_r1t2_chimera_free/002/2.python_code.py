
import numpy as np
from collections import deque

# Define global constants for the board and winning structures
CORNERS = {(0, 0), (0, 14), (14, 0), (14, 14), (7, 0), (7, 14)}
NEIGHBOR_OFFSETS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]
TOP_EDGE = {(0, c) for c in range(1, 14)}
BOTTOM_EDGE = {(14, c) for c in range(1, 14)}
LEFT_EDGE = {(r, 0) for r in range(1, 14)}
RIGHT_EDGE = {(r, 14) for r in range(1, 14)}
EDGES = [TOP_EDGE, BOTTOM_EDGE, LEFT_EDGE, RIGHT_EDGE]

def policy(me, opp, valid_mask):
    valid_moves = [
        (r, c) for r in range(15) for c in range(15) 
        if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp
    ]

    # Check immediate win
    for move in valid_moves:
        new_me = me + [move]
        if check_win(new_me):
            return move

    # Block opponent's immediate win
    block_move = find_block_move(valid_moves, opp, me)
    if block_move is not None:
        return block_move

    # Select best move based on heuristic
    best_score = -float('inf')
    best_moves = []
    for move in valid_moves:
        score = evaluate_move(move, me, opp)
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    return best_moves[np.random.randint(len(best_moves))] if best_moves else valid_moves[0]

def check_win(stones):
    return has_bridge(stones) or has_fork(stones) or has_ring(stones)

def has_bridge(stones):
    stone_set = set(stones)
    present_corners = [c for c in CORNERS if c in stone_set]
    for i in range(len(present_corners)):
        for j in range(i+1, len(present_corners)):
            if is_connected(stone_set, present_corners[i], present_corners[j]):
                return True
    return False

def is_connected(stones, start, end):
    if start == end:
        return True
    visited = set()
    queue = deque([start])
    while queue:
        cell = queue.pop()
        if cell == end:
            return True
        visited.add(cell)
        for dr, dc in NEIGHBOR_OFFSETS:
            nr, nc = cell[0] + dr, cell[1] + dc
            neighbor = (nr, nc)
            if 0 <= nr < 15 and 0 <= nc < 15 and neighbor in stones and neighbor not in visited:
                queue.append(neighbor)
    return False

def has_fork(stones):
    stone_set = set(stones)
    visited = set()
    for stone in stone_set:
        if stone in visited:
            continue
        cluster = get_cluster(stone, stone_set)
        visited.update(cluster)
        edge_count = 0
        for edge in EDGES:
            if any(s in edge for s in cluster):
                edge_count += 1
        if edge_count >= 3:
            return True
    return False

def get_cluster(start, stones):
    cluster = set()
    queue = deque([start])
    while queue:
        cell = queue.pop()
        cluster.add(cell)
        for dr, dc in NEIGHBOR_OFFSETS:
            nr, nc = cell[0] + dr, cell[1] + dc
            neighbor = (nr, nc)
            if neighbor in stones and neighbor not in cluster:
                queue.append(neighbor)
    return cluster

def has_ring(stones):
    stone_set = set(stones)
    if len(stone_set) < 6:
        return False
    visited = set()
    for stone in stone_set:
        if stone in visited:
            continue
        stack = [stone]
        parent = {stone: None}
        while stack:
            cell = stack.pop()
            if cell in visited:
                continue
            visited.add(cell)
            for dr, dc in NEIGHBOR_OFFSETS:
                nr, nc = cell[0] + dr, cell[1] + dc
                neighbor = (nr, nc)
                if neighbor in stone_set:
                    if neighbor not in parent or parent[cell] != neighbor:
                        if neighbor in visited:
                            return True
                        parent[neighbor] = cell
                        stack.append(neighbor)
    return False

def find_block_move(valid_moves, opp, me):
    for move in valid_moves:
        new_opp = opp + [move]
        if check_win(new_opp):
            return move
    return None

def evaluate_move(move, me, opp):
    score = 0
    # Connectivity to own stones
    for dr, dc in NEIGHBOR_OFFSETS:
        nr, nc = move[0] + dr, move[1] + dc
        if (nr, nc) in me:
            score += 15
    # Blocking opponent
    for dr, dc in NEIGHBOR_OFFSETS:
        nr, nc = move[0] + dr, move[1] + dc
        if (nr, nc) in opp:
            score += 10
    # Proximity to unused corners
    unused_corners = CORNERS - set(me)
    if unused_corners:
        min_dist = min(abs(move[0]-c[0]) + abs(move[1]-c[1]) for c in unused_corners)
        score += max(0, 14 - min_dist)
    # Edge importance
    if move[0] == 0 or move[0] == 14 or move[1] == 0 or move[1] == 14:
        score += 5
    # Central area for ring potential
    dist_center = abs(move[0]-7) + abs(move[1]-7)
    score += max(0, 14 - dist_center)
    return score
