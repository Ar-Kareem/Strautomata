
def policy(my_men, my_kings, opp_men, opp_kings, color):
    from collections import deque
    
    my_men = set(my_men)
    my_kings = set(my_kings)
    opp_men = set(opp_men)
    opp_kings = set(opp_kings)
    all_opp = opp_men.union(opp_kings)
    all_my = my_men.union(my_kings)
    
    max_captures = 0
    best_capture = None
    
    # Check all pieces for captures
    for piece in list(my_men) + list(my_kings):
        r, c = piece
        is_king = piece in my_kings
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else \
                     [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]
        
        for dr, dc in directions:
            adj_r, adj_c = r + dr, c + dc
            land_r, land_c = r + 2*dr, c + 2*dc
            if (adj_r, adj_c) in all_opp and (land_r, land_c) not in all_my and (land_r, land_c) not in all_opp and 0 <= land_r < 8 and 0 <= land_c < 8:
                current_captures = 1
                new_opp = all_opp - {(adj_r, adj_c)}
                queue = deque()
                queue.append((land_r, land_c, current_captures, new_opp, [(r, c, land_r, land_c)]))
                local_max = 0
                local_best = None
                
                while queue:
                    curr_r, curr_c, captures, curr_opp, path = queue.popleft()
                    if captures > local_max:
                        local_max = captures
                        local_best = path
                    for ddr, ddc in [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else \
                                    [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]:
                        adj_r2 = curr_r + ddr
                        adj_c2 = curr_c + ddc
                        land_r2 = curr_r + 2*ddr
                        land_c2 = curr_c + 2*ddc
                        if (adj_r2, adj_c2) in curr_opp and (land_r2, land_c2) not in all_my and (land_r2, land_c2) not in curr_opp and 0 <= land_r2 < 8 and 0 <= land_c2 < 8:
                            new_captures = captures + 1
                            new_opp_set = curr_opp - {(adj_r2, adj_c2)}
                            new_path = path + [(curr_r, curr_c, land_r2, land_c2)]
                            queue.append((land_r2, land_c2, new_captures, new_opp_set, new_path))
                
                if local_max > max_captures or (local_max == max_captures and not best_capture):
                    max_captures = local_max
                    best_capture = ((r, c), (land_r, land_c))
    
    if best_capture:
        return best_capture
    
    # Evaluate non-capture moves
    best_score = -float('inf')
    best_move = None
    for piece in list(my_men) + list(my_kings):
        r, c = piece
        is_king = piece in my_kings
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else \
                     [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]
        
        for dr, dc in directions:
            new_r, new_c = r + dr, c + dc
            if 0 <= new_r < 8 and 0 <= new_c < 8 and (new_r, new_c) not in all_my and (new_r, new_c) not in all_opp:
                score = 0
                # Promotion bonus
                if not is_king:
                    if (color == 'b' and new_r == 0) or (color == 'w' and new_r == 7):
                        score += 1000
                    else:
                        # Forward movement bonus
                        score += (r - new_r) * 10 if color == 'b' else (new_r - r) * 10
                # Centrality bonus
                center_score = (3.5 - abs(new_r - 3.5)) + (3.5 - abs(new_c - 3.5))
                score += center_score * 2
                # Vulnerability penalty
                for vdr, vdc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    v_r = new_r + vdr
                    v_c = new_c + vdc
                    if (v_r, v_c) in all_opp:
                        land_r_v = new_r - vdr
                        land_c_v = new_c - vdc
                        if 0 <= land_r_v < 8 and 0 <= land_c_v < 8 and (land_r_v, land_c_v) not in all_my and (land_r_v, land_c_v) not in all_opp:
                            score -= 50
                # Update best move
                if score > best_score or (score == best_score and not best_move):
                    best_score = score
                    best_move = ((r, c), (new_r, new_c))
    
    return best_move if best_move else None
