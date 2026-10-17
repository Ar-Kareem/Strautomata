
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Convert to sets for faster lookups
    me_set = set(me)
    opp_set = set(opp)
    board_size = len(valid_mask)

    # Hexagonal directions (6 neighbors)
    directions = [
        (0, 1), (1, 0), (1, -1),
        (0, -1), (-1, 0), (-1, 1)
    ]

    # Check if a move completes a win condition
    def is_winning_move(r, c, player_stones):
        new_stones = player_stones | {(r, c)}
        return (check_ring(new_stones) or
                check_bridge(new_stones, board_size) or
                check_fork(new_stones, board_size))

    # Check for ring formation (using BFS to detect cycles)
    def check_ring(stones):
        if len(stones) < 6:  # Minimum stones needed for a ring
            return False

        visited = set()
        for stone in stones:
            if stone not in visited:
                parent = {stone: None}
                queue = deque([stone])
                visited.add(stone)

                while queue:
                    current = queue.popleft()
                    for dr, dc in directions:
                        neighbor = (current[0] + dr, current[1] + dc)
                        if neighbor in stones:
                            if neighbor not in visited:
                                visited.add(neighbor)
                                parent[neighbor] = current
                                queue.append(neighbor)
                            elif neighbor != parent.get(current, None):
                                # Found a cycle
                                return True
        return False

    # Check for bridge (connects two corners)
    def check_bridge(stones, size):
        corners = [
            (0, 0), (0, size-1),
            (size-1, 0), (size-1, size-1),
            (size//2, 0), (size//2, size-1)
        ]

        # Check if any two corners are connected
        for i in range(len(corners)):
            for j in range(i+1, len(corners)):
                if are_connected(corners[i], corners[j], stones):
                    return True
        return False

    # Check for fork (connects three edges)
    def check_fork(stones, size):
        # Define edge groups (excluding corners)
        edges = {
            'top': [(0, c) for c in range(1, size-1)],
            'bottom': [(size-1, c) for c in range(1, size-1)],
            'left': [(r, 0) for r in range(1, size-1)],
            'right': [(r, size-1) for r in range(1, size-1)],
            'top-left': [(r, size-1-r) for r in range(1, size-1)],
            'bottom-right': [(size-1-r, size-1-r) for r in range(1, size-1)]
        }

        # Check if any three edges are connected
        for edge1 in edges.values():
            for edge2 in edges.values():
                if edge1 == edge2:
                    continue
                for edge3 in edges.values():
                    if edge3 == edge1 or edge3 == edge2:
                        continue

                    # Check if any stone from each edge is connected
                    for s1 in edge1:
                        if s1 in stones:
                            for s2 in edge2:
                                if s2 in stones and are_connected(s1, s2, stones):
                                    for s3 in edge3:
                                        if s3 in stones and (are_connected(s1, s3, stones) or are_connected(s2, s3, stones)):
                                            return True
        return False

    # BFS to check if two stones are connected
    def are_connected(start, end, stones):
        if start not in stones or end not in stones:
            return False
        if start == end:
            return True

        visited = set()
        queue = deque([start])
        visited.add(start)

        while queue:
            current = queue.popleft()
            for dr, dc in directions:
                neighbor = (current[0] + dr, current[1] + dc)
                if neighbor == end:
                    return True
                if neighbor in stones and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    # Evaluate move score
    def evaluate_move(r, c):
        score = 0

        # Proximity to my stones
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if (nr, nc) in me_set:
                score += 2

        # Proximity to opponent stones (blocking potential)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp_set:
                score += 1

        # Center control
        center = board_size // 2
        distance = abs(r - center) + abs(c - center)
        score += (center - distance) / center

        # Edge control (for bridges/forks)
        if r == 0 or r == board_size-1 or c == 0 or c == board_size-1:
            score += 0.5

        return score

    # Generate all valid moves
    valid_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))

    # First check for immediate winning moves
    for move in valid_moves:
        if is_winning_move(move[0], move[1], me_set):
            return move

    # Then check for blocking opponent's winning moves
    for move in valid_moves:
        if is_winning_move(move[0], move[1], opp_set):
            return move

    # If no immediate win/block, evaluate all moves
    best_move = None
    best_score = -float('inf')

    for move in valid_moves:
        score = evaluate_move(move[0], move[1])
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
