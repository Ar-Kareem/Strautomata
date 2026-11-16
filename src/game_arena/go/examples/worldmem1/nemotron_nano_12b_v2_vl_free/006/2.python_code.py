
def policy(me, opponent, memory):
    adjacent_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    me_set = set(me)
    opponent_set = set(opponent)
    legal_moves = []
    empty_cells = [(r, c) for r in range(1, 20) for c in range(1, 20) 
                   if (r, c) not in me_set and (r, c) not in opponent_set]
    
    # Generate all legal moves
    for x, y in empty_cells:
        visited = set([(x, y)])
        stack = [(x, y)]
        while stack:
            a, b = stack.pop()
            for dx, dy in adjacent_directions:
                nx, ny = a + dx, b + dy
                if 1 <= nx <= 19 and 1 <= ny <= 19 and (nx, ny) in me_set and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    stack.append((nx, ny))
        liberties = set()
        for a, b in visited:
            for dx, dy in adjacent_directions:
                cx, cy = a + dx, b + dy
                if 1 <= cx <= 19 and 1 <= cy <= 19:
                    if (cx, cy) not in me_set and (cx, cy) not in opponent_set and (cx, cy) != (x, y):
                        liberties.add((cx, cy))
        if liberties:
            legal_moves.append((x, y))
    
    if not legal_moves:
        return ((0, 0), memory)
    
    best_move = None
    best_score = -float('inf')
    for (x, y) in legal_moves:
        captured = 0
        visited_groups = set()
        for dx, dy in adjacent_directions:
            cx, cy = x + dx, y + dy
            if (cx, cy) in opponent_set and (cx, cy) not in visited_groups:
                group = set()
                stack = [(cx, cy)]
                visited_group = {(cx, cy)}
                while stack:
                    a, b = stack.pop()
                    for edx, edy in adjacent_directions:
                        nx, ny = a + edx, b + edy
                        if 1 <= nx <= 19 and 1 <= ny <= 19 and (nx, ny) in opponent_set and (nx, ny) not in visited_group:
                            visited_group.add((nx, ny))
                            stack.append((nx, ny))
                liberties = set()
                for stone in visited_group:
                    a, b = stone
                    for edx, edy in adjacent_directions:
                        cx, cy = a + edx, b + edy
                        if (cx, cy) not in me_set and (cx, cy) not in opponent_set and (cx, cy) != (x, y):
                            liberties.add((cx, cy))
                if not liberties:
                    captured += len(visited_group)
                    visited_groups.update(visited_group)
        
        distance = abs(x - 10) + abs(y - 10)
        distance_score = 100 // (distance + 1) if distance else 1000
        adj_me = sum(1 for dx, dy in adjacent_directions if (x + dx, y + dy) in me_set)
        score = captured * 100 + distance_score + adj_me * 10
        
        if score > best_score or (score == best_score and (best_move is None or (x*19 + y) < (best_move[0]*19 + best_move[1]))):
            best_score = score
            best_move = (x, y)
    
    return (best_move, memory)
