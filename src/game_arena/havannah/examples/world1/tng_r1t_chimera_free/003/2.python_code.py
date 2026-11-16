
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    valid_moves = [(r, c) for r in range(15) for c in range(15) if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp]
    if not valid_moves:
        return (0, 0)  # Fallback if no valid moves (shouldn't occur)

    corners = {(0, 0), (0, 14), (7, 14), (14, 7), (14, 0), (7, 0)}

    # Check for immediate winning move (bridge)
    for r, c in valid_moves:
        new_me = me + [(r, c)]
        if has_bridge(new_me, corners):
            return (r, c)

    # Block opponent's potential bridge wins
    opponent_win_moves = []
    for r, c in valid_moves:
        new_opp = opp + [(r, c)]
        if has_bridge(new_opp, corners):
            opponent_win_moves.append((r, c))
    if opponent_win_moves:
        return opponent_win_moves[0]

    # Heuristic: maximize adjacency and centrality
    best_score = -1
    best_move = valid_moves[0]
    center = (7, 7)
    for r, c in valid_moves:
        score = 0
        # Adjacency to own stones
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15 and (nr, nc) in me:
                score += 2
        # Centrality (Manhattan distance from center)
        distance = abs(r - 7) + abs(c - 7)
        score += (14 - distance)
        if score > best_score:
            best_score = score
            best_move = (r, c)
    return best_move

def has_bridge(stones, corners):
    stone_set = set(stones)
    my_corners = [s for s in stones if s in corners]
    if len(my_corners) < 2:
        return False
    # Build adjacency graph
    graph = {s: [] for s in stones}
    for r, c in stones:
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1)]:
            neighbor = (r + dr, c + dc)
            if neighbor in stone_set:
                graph[(r, c)].append(neighbor)
    # BFS to check connectivity between any two corners
    from collections import deque
    for i in range(len(my_corners)):
        for j in range(i+1, len(my_corners)):
            start, end = my_corners[i], my_corners[j]
            visited = set()
            queue = deque([start])
            while queue:
                current = queue.popleft()
                if current == end:
                    return True
                if current in visited:
                    continue
                visited.add(current)
                queue.extend([n for n in graph[current] if n not in visited])
    return False
