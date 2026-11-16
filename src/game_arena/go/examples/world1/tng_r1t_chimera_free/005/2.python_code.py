
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opponent)
    all_moves = []
    
    # Generate all empty positions and their capture counts
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me_set and (r, c) not in opp_set:
                captures = 0
                # Check each adjacent opponent stone for capture potential
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in opp_set:
                        # Check if all other adjacent to (nr,nc) are filled
                        all_filled = True
                        for ndr, ndc in [(-1,0), (1,0), (0,-1), (0,1)]:
                            adj_r, adj_c = nr + ndr, nc + ndc
                            if (adj_r, adj_c) == (r, c):
                                continue
                            if 1 <= adj_r <= 19 and 1 <= adj_c <= 19:
                                if (adj_r, adj_c) not in me_set and (adj_r, adj_c) not in opp_set:
                                    all_filled = False
                                    break
                        if all_filled:
                            captures += 1
                all_moves.append((r, c, captures))
    
    # Prioritize capturing moves
    capture_moves = [m for m in all_moves if m[2] > 0]
    if capture_moves:
        max_cap = max(m[2] for m in capture_moves)
        candidates = [m[:2] for m in capture_moves if m[2] == max_cap]
        # Prefer center-most capture to maintain influence
        return min(candidates, key=lambda pos: (abs(pos[0]-10) + abs(pos[1]-10)))
    
    # Heuristic-based move selection
    valid_moves = []
    for r, c, _ in all_moves:
        # Ensure at least one adjacent liberty
        if any(1 <= r + dr <= 19 and 1 <= c + dc <= 19 and 
               (r+dr, c+dc) not in me_set and (r+dr, c+dc) not in opp_set
               for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]):
            # Calculate heuristic score
            my_adj = sum(1 for dr in [-1,0,1] for dc in [-1,0,1] 
                        if (r+dr, c+dc) in me_set and (dr,dc) != (0,0))
            opp_adj = sum(1 for dr in [-1,0,1] for dc in [-1,0,1] 
                         if (r+dr, c+dc) in opp_set and (dr,dc) != (0,0))
            center_score = 14 - (abs(r-10) + abs(c-10))
            score = 2 * my_adj - opp_adj + center_score
            valid_moves.append((r, c, score))
    
    if valid_moves:
        max_score = max(m[2] for m in valid_moves)
        candidates = [m[:2] for m in valid_moves if m[2] == max_score]
        # Prefer more central positions among top candidates
        return min(candidates, key=lambda pos: (abs(pos[0]-10) + abs(pos[1]-10)))
    
    # Fallback to passing if no valid moves (shouldn't occur in normal play)
    return (0, 0)
