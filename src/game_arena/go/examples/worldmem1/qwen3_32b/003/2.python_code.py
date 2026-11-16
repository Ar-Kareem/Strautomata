
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    me_set = set(me)
    opponent_set = set(opponent)
    
    def get_group(stones, start):
        visited = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nx, ny = current[0] + dx, current[1] + dy
                    neighbor = (nx, ny)
                    if neighbor in stones and neighbor not in visited:
                        stack.append(neighbor)
        return visited
    
    def is_legal(move):
        r, c = move
        if not (1 <= r <= 19 and 1 <= c <= 19):
            return False
        if (r, c) in me_set or (r, c) in opponent_set:
            return False
            
        captured_groups = []
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opponent_set:
                group = get_group(opponent_set, (nr, nc))
                has_liberty = False
                for (gx, gy) in group:
                    for dx_op, dy_op in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nx_op, ny_op = gx + dx_op, gy + dy_op
                        if (nx_op, ny_op) not in opponent_set and (nx_op, ny_op) not in me_set and (nx_op, ny_op) != (r, c):
                            has_liberty = True
                            break
                    if has_liberty:
                        break
                if not has_liberty:
                    captured_groups.append(group)
        
        remaining_opponent = set(opponent_set)
        for group in captured_groups:
            for (x, y) in group:
                if (x, y) in remaining_opponent:
                    remaining_opponent.remove((x, y))
        
        new_me = me_set | {(r, c)}
        group = get_group(new_me, (r, c))
        has_liberty = False
        for (gx, gy) in group:
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = gx + dx, gy + dy
                if (nx, ny) not in new_me and (nx, ny) not in remaining_opponent:
                    has_liberty = True
                    break
            if has_liberty:
                break
        
        return has_liberty or len(captured_groups) > 0
    
    empty_positions = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me_set and (r, c) not in opponent_set:
                empty_positions.append((r, c))
    
    legal_moves = [move for move in empty_positions if is_legal(move)]
    
    if not legal_moves:
        return ((0, 0), memory)
    
    best_score = -1
    best_moves = []
    for move in legal_moves:
        r, c = move
        
        captured_groups = []
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opponent_set:
                group = get_group(opponent_set, (nr, nc))
                has_liberty = False
                for (gx, gy) in group:
                    for dx_op, dy_op in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nx_op, ny_op = gx + dx_op, gy + dy_op
                        if (nx_op, ny_op) not in opponent_set and (nx_op, ny_op) not in me_set and (nx_op, ny_op) != (r, c):
                            has_liberty = True
                            break
                    if has_liberty:
                        break
                if not has_liberty:
                    captured_groups.append(group)
        
        captured_count = sum(len(g) for g in captured_groups)
        if captured_count > 0:
            score = 1000 + captured_count * 10
        else:
            adjacent_own = 0
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in me_set:
                    adjacent_own += 1
            if adjacent_own > 0:
                score = adjacent_own * 100
            else:
                center_r, center_c = 10, 10
                distance = abs(r - center_r) + abs(c - center_c)
                score = 100 / (distance + 1)
        
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    return (best_moves[0], memory)
