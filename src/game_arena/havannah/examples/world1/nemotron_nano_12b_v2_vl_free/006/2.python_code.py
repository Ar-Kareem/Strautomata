
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    directions = [
        (-1, 0),   # up
        (-1, -1),  # up-left
        (0, -1),   # left
        (1, -1),   # down-left
        (1, 0),     # down
        (0, 1)      # right
    ]

    corners = {(0, 0), (0, 14), (14, 0), (14, 14)}
    candidates = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp:
                candidates.append((r, c))
    
    # Check for immediate bridge formation
    for move in candidates:
        new_me = me + [move]
        ai_set = set(new_me)
        ai_corners = ai_set & corners
        if len(ai_corners) < 2:
            continue
        visited = set()
        queue = deque()
        connected_corners = 0
        for corner in ai_corners:
            if corner in visited:
                continue
            queue.append(corner)
            visited.add(corner)
            found_other = False
            while queue and not found_other:
                current = queue.popleft()
                for dr, dc in directions:
                    nr, nc = current[0] + dr, current[1] + dc
                    if 0 <= nr < 15 and 0 <= nc < 15:
                        neighbor = (nr, nc)
                        if neighbor in ai_set and neighbor not in visited:
                            visited.add(neighbor)
                            if neighbor in ai_corners and neighbor != corner:
                                found_other = True
                                break
                            queue.append(neighbor)
            if found_other:
                return move
    
    best_score = float('-inf')
    best_move = None
    for move in candidates:
        ai_adj = 0
        opp_adj = 0
        r, c = move
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15:
                if (nr, nc) in me:
                    ai_adj += 1
                if (nr, nc) in opp:
                    opp_adj += 1
        
        strategic_score = 0
        if (r, c) in corners:
            strategic_score = 50
        elif r == 0 or r == 14 or c == 0 or c == 14:
            strategic_score = 30
        
        distance = (r - 7) ** 2 + (c - 7) ** 2
        score = ai_adj * 3 - opp_adj * 2 + strategic_score - distance
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move else candidates[0]
