
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    def find_group_and_liberties(stone_set, start_pos, opponent_set):
        visited = set()
        group = set()
        liberties = set()
        stack = [start_pos]
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        while stack:
            pos = stack.pop()
            if pos in visited:
                continue
            visited.add(pos)
            group.add(pos)
            for dr, dc in directions:
                nr, nc = pos[0] + dr, pos[1] + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    neighbor = (nr, nc)
                    if neighbor in stone_set:
                        if neighbor not in visited:
                            stack.append(neighbor)
                    elif neighbor in opponent_set:
                        pass  # Not a liberty.
                    else:
                        liberties.add(neighbor)
        return group, liberties

    def is_valid_and_get_captured(me_set, opp_set, r, c):
        if (r, c) in me_set or (r, c) in opp_set:
            return False, 0, 0
        captured_positions = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp_set:
                group, liberties = find_group_and_liberties(opp_set, (nr, nc), me_set)
                if (r, c) in liberties:
                    captured_positions.update(group)
        new_me_stones = me_set | {(r, c)}
        new_opp_stones = opp_set - captured_positions
        new_group, new_liberties = find_group_and_liberties(new_me_stones, (r, c), new_opp_stones)
        if len(new_liberties) == 0:
            return (True, len(captured_positions), len(new_liberties)) if captured_positions else (False, 0, 0)
        return True, len(captured_positions), len(new_liberties)

    me_set = set(me)
    opp_set = set(opponent)
    legal_moves = []
    
    for r in range(1, 20):
        for c in range(1, 20):
            is_valid, captured, liberties = is_valid_and_get_captured(me_set, opp_set, r, c)
            if is_valid and (r, c) not in me_set and (r, c) not in opp_set:
                legal_moves.append(((r, c), captured, liberties))
    
    if not legal_moves:
        return ((0, 0), memory)
    
    def move_key(move_info):
        pos, captured, liberties = move_info
        r, c = pos
        distance = (r - 10)**2 + (c - 10)**2
        return (-captured, -liberties, distance)
    
    sorted_moves = sorted(legal_moves, key=move_key)
    best_move = sorted_moves[0][0]
    return (best_move, memory)
