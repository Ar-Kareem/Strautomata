
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opponent)
    
    # Generate list of all empty positions
    empty_positions = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me_set and (r, c) not in opp_set:
                empty_positions.append((r, c))
    
    if not empty_positions:
        return (0, 0)
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Check for capture moves and prioritize those capturing most stones
    capture_candidates = []
    for pos in empty_positions:
        r, c = pos
        stones_captured = 0
        visited_groups = set()
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp_set and (nr, nc) not in visited_groups:
                # Find entire group of opponent stone
                group = []
                queue = [(nr, nc)]
                group_set = set(queue)
                visited = set()
                while queue:
                    curr = queue.pop(0)
                    if curr in visited:
                        continue
                    visited.add(curr)
                    group.append(curr)
                    for ddr, ddc in directions:
                        nrr, ncc = curr[0] + ddr, curr[1] + ddc
                        if (nrr, ncc) in opp_set and (nrr, ncc) not in visited:
                            queue.append((nrr, ncc))
                            group_set.add((nrr, ncc))
                # Calculate liberties
                liberties = set()
                for (gr, gc) in group:
                    for ddr, ddc in directions:
                        lr, lc = gr + ddr, gc + ddc
                        if (lr, lc) not in me_set and (lr, lc) not in opp_set:
                            liberties.add((lr, lc))
                # Check if the move captures this group
                if len(liberties) == 1 and (r, c) in liberties:
                    stones_captured += len(group)
                    visited_groups.update(group_set)
        if stones_captured > 0:
            capture_candidates.append((pos, stones_captured))
    
    if capture_candidates:
        # Sort by number of stones captured, descending
        capture_candidates.sort(key=lambda x: x[1], reverse=True)
        return capture_candidates[0][0]
    
    # If no capture moves, choose based on heuristic
    best_score = -1
    best_move = None
    for r, c in empty_positions:
        adjacent_me = 0
        adjacent_opp = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if (nr, nc) in me_set:
                adjacent_me += 1
            elif (nr, nc) in opp_set:
                adjacent_opp += 1
        score = adjacent_opp * 3 + adjacent_me
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
