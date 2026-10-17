
import random
from collections import deque

# Hexagonal grid neighbor directions (6 directions)
HEX_DIRECTIONS = [
    (-1, 0), (0, -1), (1, -1),
    (1, 0), (0, 1), (-1, 1)
]

def is_valid_position(row, col, size=15):
    return 0 <= row < size and 0 <= col < size

def get_neighbors(row, col, size=15):
    neighbors = []
    for dr, dc in HEX_DIRECTIONS:
        r, c = row + dr, col + dc
        if is_valid_position(r, c):
            neighbors.append((r, c))
    return neighbors

def is_connected(stones, target1, target2):
    if not stones:
        return False
    visited = set()
    queue = deque([stones[0]])
    visited.add(stones[0])

    while queue:
        current = queue.popleft()
        if current == target1 or current == target2:
            return True
        for neighbor in get_neighbors(current[0], current[1]):
            if neighbor in stones and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return False

def check_ring(stones, size=15):
    # Check if stones form a ring (enclosing empty space)
    # This is a simplified check - a full implementation would be more complex
    if len(stones) < 6:  # Minimum stones needed for a ring
        return False

    # Find all empty cells adjacent to our stones
    empty_cells = set()
    for stone in stones:
        for neighbor in get_neighbors(stone[0], stone[1]):
            if neighbor not in stones:
                empty_cells.add(neighbor)

    # For each empty cell, check if it's completely surrounded
    for cell in empty_cells:
        surrounded = True
        for neighbor in get_neighbors(cell[0], cell[1]):
            if neighbor not in stones:
                surrounded = False
                break
        if surrounded:
            return True
    return False

def check_bridge(stones, size=15):
    # Check if stones connect two corners
    corners = [(0, 0), (0, size-1), (size-1, 0), (size-1, size-1),
               (size//2, 0), (size//2, size-1)]

    connected_corners = 0
    for i, corner1 in enumerate(corners):
        for corner2 in corners[i+1:]:
            if is_connected(stones, corner1, corner2):
                connected_corners += 1
                if connected_corners >= 2:
                    return True
    return False

def check_fork(stones, size=15):
    # Check if stones connect three edges
    edges = {
        'top': [(0, c) for c in range(size)],
        'bottom': [(size-1, c) for c in range(size)],
        'left': [(r, 0) for r in range(size)],
        'right': [(r, size-1) for r in range(size)],
        'top_left': [(r, size-1-r) for r in range(size)],
        'bottom_right': [(size-1-r, r) for r in range(size)]
    }

    connected_edges = 0
    edge_names = list(edges.keys())

    for i in range(len(edge_names)):
        for j in range(i+1, len(edge_names)):
            for k in range(j+1, len(edge_names)):
                edge1 = edges[edge_names[i]]
                edge2 = edges[edge_names[j]]
                edge3 = edges[edge_names[k]]

                # Check if stones connect all three edges
                connected = False
                for stone in stones:
                    if stone in edge1:
                        connected = True
                        break
                if not connected:
                    continue

                connected = False
                for stone in stones:
                    if stone in edge2:
                        connected = True
                        break
                if not connected:
                    continue

                connected = False
                for stone in stones:
                    if stone in edge3:
                        connected = True
                        break
                if connected:
                    return True
    return False

def check_win(stones, size=15):
    return check_ring(stones, size) or check_bridge(stones, size) or check_fork(stones, size)

def evaluate_position(stones, opp_stones, size=15):
    # Simple evaluation function
    score = 0

    # Count potential connections
    for stone in stones:
        neighbors = get_neighbors(stone[0], stone[1])
        for neighbor in neighbors:
            if neighbor in stones:
                score += 1

    # Penalize opponent's potential connections
    for stone in opp_stones:
        neighbors = get_neighbors(stone[0], stone[1])
        for neighbor in neighbors:
            if neighbor in opp_stones:
                score -= 0.5

    # Bonus for center control
    center = size // 2
    for stone in stones:
        dist = abs(stone[0] - center) + abs(stone[1] - center)
        score += (center - dist) * 0.1

    return score

def policy(me, opp, valid_mask):
    size = len(valid_mask)
    all_stones = set(me) | set(opp)
    empty_cells = [(r, c) for r in range(size) for c in range(size)
                  if valid_mask[r][c] and (r, c) not in all_stones]

    # Check if we can win immediately
    for move in empty_cells:
        new_stones = me + [move]
        if check_win(new_stones, size):
            return move

    # Check if opponent can win and block them
    for move in empty_cells:
        new_opp = opp + [move]
        if check_win(new_opp, size):
            return move

    # Strategic positioning
    corners = [(0, 0), (0, size-1), (size-1, 0), (size-1, size-1),
               (size//2, 0), (size//2, size-1)]
    edges = [(0, c) for c in range(1, size-1)] + \
            [(size-1, c) for c in range(1, size-1)] + \
            [(r, 0) for r in range(1, size-1)] + \
            [(r, size-1) for r in range(1, size-1)]

    # Prioritize corners, then edges, then center
    candidates = []
    for cell in corners:
        if cell in empty_cells:
            candidates.append(cell)

    if not candidates:
        for cell in edges:
            if cell in empty_cells:
                candidates.append(cell)

    if not candidates:
        center = size // 2
        candidates = [(r, c) for r in range(size) for c in range(size)
                     if valid_mask[r][c] and (r, c) not in all_stones]

    # Evaluate candidates
    best_move = None
    best_score = -float('inf')

    for move in candidates:
        new_stones = me + [move]
        score = evaluate_position(new_stones, opp, size)
        if score > best_score:
            best_score = score
            best_move = move

    if best_move:
        return best_move

    # Fallback to random move
    return random.choice(empty_cells)
