
from collections import deque

def extract_group(opponent_pos, cell, visited):
    queue = deque([cell])
    group = [cell]
    visited.add(cell)
    while queue:
        x, y = queue.popleft()
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 1 <= nx <= 19 and 1 <= ny <= 19:
                if (nx, ny) not in visited and (nx, ny) in opponent_pos:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
                    group.append((nx, ny))
    return group, visited

def policy(me, opponent):
    my_pos = set(me)
    opp_pos = set(opponent)
    
    # Generate all legal moves
    legal_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in my_pos and (r, c) not in opp_pos:
                legal_moves.append((r, c))
    
    if not legal_moves:
        return (0, 0)
    
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    
    # Check each move for capture potential
    capture_moves = []
    best_capture = -1
    
    for move in legal_moves:
        r, c = move
        captured = 0
        visited = set()
        for dx, dy in dirs:
            x, y = r + dx, c + dy
            if (x, y) in opp_pos:
                group, new_visited = extract_group(opp_pos, (x, y), set())
                liberties = set()
                for (gx, gy) in group:
                    for gdx, gdy in dirs:
                        ax, ay = gx + gdx, gy + gdy
                        if 1 <= ax <= 19 and 1 <= ay <= 19:
                            if (ax, ay) == (r, c):
                                continue
                            if (ax, ay) not in my_pos and (ax, ay) not in opp_pos:
                                liberties.add((ax, ay))
                if len(liberties) == 0:
                    captured += len(group)
                    visited.update(new_visited)
        move_captures = captured
        if move_captures > 0:
            if move_captures > best_capture:
                best_capture = move_captures
            capture_moves.append((move_captures, move))
    
    # Check if there are any capturing moves
    if best_capture > 0:
        # Select the move with the maximum captures, tie-breaker by distance to center
        def sort_key(tuple_entry):
            capture_count, move = tuple_entry
            return (-capture_count, (move[0]-10)**2 + (move[1]-10)**2)
        capture_moves.sort(key=sort_key)
        return capture_moves[0][1]
    
    # If no captures available, use strategic positioning heuristic
    # Evaluate each move based on proximity to existing stones and center
    best_strategic = -float('inf')
    best_strategic_move = None
    
    for move in legal_moves:
        r, c = move
        adjacent_my = 0
        edge_distance = min(r-1, 19-r, c-1, 19-c)
        
        for dx, dy in dirs:
            if (r + dx, c + dy) in my_pos:
                adjacent_my += 1
        
        distance_to_center = (3.16) ** 2 - ((r - 10) ** 2 + (c - 10) ** 2)  # Simulating inverse distance
        strategic_score = adjacent_my * 3 + distance_to_center
        
        if strategic_score > best_strategic or (strategic_score == best_strategic and (best_strategic_move is None)):
            best_strategic = strategic_score
            best_strategic_move = move
    
    return best_strategic_move
