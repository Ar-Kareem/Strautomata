
import random
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Convert to sets for faster lookups
    me_set = set(me)
    opp_set = set(opp)
    board_size = 11

    # Directions for hexagonal neighbors (excluding the two diagonal directions)
    directions = [(-1, 0), (-1, 1), (0, 1), (1, 0), (1, -1), (0, -1)]

    def is_valid_move(r, c):
        return 0 <= r < board_size and 0 <= c < board_size and (r, c) not in me_set and (r, c) not in opp_set

    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size:
                neighbors.append((nr, nc))
        return neighbors

    def has_path(stones, target_edges):
        if not stones:
            return False

        visited = set()
        queue = deque()

        # Find all stones on the target edges
        for r, c in stones:
            if (color == 'b' and (r == 0 or r == board_size - 1)) or \
               (color == 'w' and (c == 0 or c == board_size - 1)):
                queue.append((r, c))
                visited.add((r, c))

        while queue:
            r, c = queue.popleft()

            # Check if we've reached the opposite edge
            if (color == 'b' and (r == board_size - 1 - (0 if r == 0 else board_size - 1))) or \
               (color == 'w' and (c == board_size - 1 - (0 if c == 0 else board_size - 1))):
                return True

            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))

        return False

    def get_distance_map(stones, target_edges):
        distance = np.full((board_size, board_size), -1)
        queue = deque()

        # Initialize with target edges
        for r in range(board_size):
            for c in range(board_size):
                if (color == 'b' and (r == 0 or r == board_size - 1)) or \
                   (color == 'w' and (c == 0 or c == board_size - 1)):
                    if (r, c) in stones:
                        distance[r, c] = 0
                        queue.append((r, c))

        # BFS to calculate distances
        while queue:
            r, c = queue.popleft()
            for nr, nc in get_neighbors(r, c):
                if distance[nr, nc] == -1 and (nr, nc) in stones:
                    distance[nr, nc] = distance[r, c] + 1
                    queue.append((nr, nc))

        return distance

    def evaluate_move(r, c):
        # Create temporary board state
        temp_me = me_set | {(r, c)}
        temp_opp = opp_set

        # Check if this move wins
        if has_path(temp_me, color):
            return float('inf')

        # Check if opponent can win after this move
        if has_path(temp_opp, 'w' if color == 'b' else 'b'):
            return -float('inf')

        # Calculate distance maps
        my_distance = get_distance_map(temp_me, color)
        opp_distance = get_distance_map(temp_opp, 'w' if color == 'b' else 'b')

        # Calculate scores
        my_score = np.sum(my_distance[my_distance != -1])
        opp_score = np.sum(opp_distance[opp_distance != -1])

        # Prefer moves that improve our position relative to opponent
        return my_score - opp_score

    # Check for immediate win
    for r in range(board_size):
        for c in range(board_size):
            if is_valid_move(r, c):
                temp_me = me_set | {(r, c)}
                if has_path(temp_me, color):
                    return (r, c)

    # Check for immediate block
    for r in range(board_size):
        for c in range(board_size):
            if is_valid_move(r, c):
                temp_opp = opp_set | {(r, c)}
                if has_path(temp_opp, 'w' if color == 'b' else 'b'):
                    return (r, c)

    # Generate candidate moves
    candidates = []
    for r in range(board_size):
        for c in range(board_size):
            if is_valid_move(r, c):
                candidates.append((r, c))

    if not candidates:
        # Shouldn't happen as board isn't full
        return random.choice([(r, c) for r in range(board_size) for c in range(board_size) if (r, c) not in me_set and (r, c) not in opp_set])

    # Evaluate candidates
    evaluated = []
    for r, c in candidates:
        score = evaluate_move(r, c)
        evaluated.append((score, r, c))

    # Sort by score
    evaluated.sort(reverse=True, key=lambda x: x[0])

    # Take top 5 candidates and choose randomly among them with bias
    top_candidates = evaluated[:min(5, len(evaluated))]
    if not top_candidates:
        return random.choice(candidates)

    # Weighted random selection
    scores = [x[0] for x in top_candidates]
    if all(s == -float('inf') for s in scores):
        return random.choice(candidates)

    # Normalize scores to positive values
    min_score = min(scores)
    if min_score < 0:
        scores = [s - min_score + 1 for s in scores]

    total = sum(scores)
    if total == 0:
        return random.choice(candidates)

    probs = [s/total for s in scores]
    chosen = random.choices(top_candidates, weights=probs, k=1)[0]

    return (chosen[1], chosen[2])
