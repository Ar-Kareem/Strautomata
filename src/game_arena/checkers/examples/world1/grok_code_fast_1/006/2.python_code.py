
import copy

def policy(my_men, my_kings, opp_men, opp_kings, color):
    all_my_men = copy.deepcopy(my_men)
    all_my_kings = copy.deepcopy(my_kings)
    all_opp_men = copy.deepcopy(opp_men)
    all_opp_kings = copy.deepcopy(opp_kings)
    
    occupied = set(tuple(p) for p in all_my_men + all_my_kings + all_opp_men + all_opp_kings)
    opp_positions = set(tuple(p) for p in all_opp_men + all_opp_kings)
    
    # Helper to check if position is valid and empty
    def is_valid(pos):
        r, c = pos
        return 0 <= r <= 7 and 0 <= c <= 7 and pos not in occupied
    
    def get_moves_for_piece(start, is_king, color, occupied, opp_positions):
        result = []
        r, c = start
        directions = [-1, 1] if is_king else ([-1] if color == 'b' else [1])
        all_dc = [-1, 1]
        for dr in directions:
            for dc in all_dc:
                # Simple move
                nr, nc = r + dr, c + dc
                if is_valid((nr, nc)):
                    result.append(((nr, nc), set()))
                # Jump
                nr, nc = r + 2 * dr, c + 2 * dc
                important = (r + dr, c + dc)
                if is_valid((nr, nc)) and tuple(important) in opp_positions:
                    jumped = {tuple(important)}
                    new_occupied = occupied.copy()
                    new_occupied.discard(tuple(start))
                    new_occupied.discard(tuple(important))
                    new_occupied.add((nr, nc))
                    new_opp = opp_positions - jumped
                    further = get_moves_for_piece((nr, nc), is_king, color, new_occupied, new_opp)
                    if further:
                        for end, fj in further:
                            result.append((end, jumped | fj))
                    else:
                        result.append(((nr, nc), jumped))
        return result
    
    all_pieces = [(p, False) for p in all_my_men] + [(p, True) for p in all_my_kings]
    all_possible_moves = []
    for p, is_k in all_pieces:
        moves = get_moves_for_piece(tuple(p), is_k, color, occupied, opp_positions)
        for end, jumped in moves:
            all_possible_moves.append((tuple(p), end, jumped))
    
    # Separate captures and non-captures
    captures = [(s, e, j) for s, e, j in all_possible_moves if j]
    non_captures = [(s, e, j) for s, e, j in all_possible_moves if not j]
    
    legal_moves = captures if captures else non_captures
    
    # Evaluate each legal move
    def simulate_state(start, end, jumped, my_men, my_kings, opp_men, opp_kings, color):
        new_my_men = copy.deepcopy(my_men)
        new_my_kings = copy.deepcopy(my_kings)
        new_opp_men = copy.deepcopy(opp_men)
        new_opp_kings = copy.deepcopy(opp_kings)
        
        # Determine piece type
        moved_icon_from_my_men = start in new_my_men
        moved_from_my_kings = start in new_my_kings
        if moved_from_my_men:
            new_my_men.remove(start)
            piece_type = 'man'
        else:
            new_my_kings.remove(start)
            piece_type = 'king'
        
        # Determine if promotion
        promote_row = 0 if color == 'b' else 7
        if piece_type == 'man' and end[0] == promote_row:
            new_my_kings.append(end)
        elif piece_type == 'king':
            new_my_kings.append(end)
        else:
            new_my_men.append(end)
        
        # Remove jumped
        for j in jumped:
            if j in new_opp_men:
                new_opp_men.remove(j)
            elif j in new_opp_kings:
                new_opp_kings.remove(j)
        
        return new_my_men, new_my_kings, new_opp_men, new_opp_kings
    
    def calculate_score(my_men, my_kings, opp_men, opp_kings, color):
        row_func = lambda p: p[0] if color == 'w' else 7 - p[0]
        my_score = len(my_men) + 5 * len(my_kings) + 0.2 * sum(row_func(p) for p in my_men + my_kings)
        opp_score = len(opp_men) + 5 * len(opp_kings) + 0.2 * sum(row_func(p) for p in opp_men + opp_kings)
        return my_score - opp_score
    
    best_move = None
    best_score = float('-inf')
    for s, e, j in legal_moves:
        sim_my_men, sim_my_kings, sim_opp_men, sim_opp_kings = simulate_state(s, e, j, all_my_men, all_my_kings, all_opp_men, all_opp_kings, color)
        score = calculate_score(sim_my_men, sim_my_kings, sim_opp_men, sim_opp_kings, color)
        if score > best_score:
            best_score = score
            best_move = (s, e)
    
    return best_move if best_move else [(s, e) for s, e, _ in legal_moves][0]  # Fallback
