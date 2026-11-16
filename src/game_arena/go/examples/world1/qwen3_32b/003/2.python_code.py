
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    opponent_set = set(opponent)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def get_connected_group(start_pos, current_set, other_set):
        if start_pos not in current_set:
            return set()
        visited = set()
        stack = [start_pos]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for dr, dc in directions:
                nr, nc = current[0] + dr, current[1] + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    neighbor = (nr, nc)
                    if neighbor in current_set and neighbor not in visited:
                        stack.append(neighbor)
        return visited
    
    def get_group_liberties(group, current_set, other_set):
        liberties = set()
        for (r, c) in group:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                pos = (nr, nc)
                if 1 <= nr <= 19 and 1 <= nc <= 19 and pos not in current_set and pos not in other_set:
                    liberties.add(pos)
        return liberties
    
    def is_candidate_legal(pos):
        if pos in me_set or pos in opponent_set:
            return False
        new_me_set = me_set.copy()
        new_me_set.add(pos)
        # Check if the new group has any liberties
        group = get_connected_group(pos, new_me_set, opponent_set)
        liberties = get_group_liberties(group, new_me_set, opponent_set)
        if len(liberties) > 0:
            return True
        # Else, check if it captures any opponent groups
        for dr, dc in directions:
            nr, nc = pos[0] + dr, pos[1] + dc
            if (nr, nc) in opponent_set:
                opp_group = get_connected_group((nr, nc), opponent_set, new_me_set)
                opp_libs = get_group_liberties(opp_group, opponent_set, new_me_set)
                if len(opp_libs) == 0:
                    return True
        return False
    
    empty_positions = [(r, c) for r in range(1, 20) for c in range(1, 20) if (r, c) not in me_set and (r, c) not in opponent_set]
    
    legal_candidates = []
    for pos in empty_positions:
        if is_candidate_legal(pos):
            legal_candidates.append(pos)
    
    if not legal_candidates:
        return (0, 0)
    
    def compute_heuristic(pos):
        r, c = pos
        center = 10
        distance = abs(r - center) + abs(c - center)
        heuristic = 1.0 / (distance + 1)
        adjacent_me = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if (nr, nc) in me_set:
                adjacent_me += 1
        heuristic += adjacent_me * 0.5
        return heuristic
    
    best_move = None
    best_value = -1
    for pos in legal_candidates:
        new_me_set = me_set.copy()
        new_me_set.add(pos)
        captured_count = 0
        for dr, dc in directions:
            nr, nc = pos[0] + dr, pos[1] + dc
            if (nr, nc) in opponent_set:
                opp_group = get_connected_group((nr, nc), opponent_set, new_me_set)
                opp_libs = get_group_liberties(opp_group, opponent_set, new_me_set)
                if len(opp_libs) == 0:
                    captured_count += len(opp_group)
        if captured_count > 0:
            value = captured_count * 10
        else:
            value = compute_heuristic(pos)
        if value > best_value:
            best_value = value
            best_move = pos
    return best_move
