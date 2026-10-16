
def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Checkers Policy AI using Immediate Forced Captures and Heuristic Evaluation.
    """
    
    # --- Configuration & Constants ---
    BOARD_SIZE = 8
    # Directions: (row_change, col_change)
    # Black ('b') moves UP: row - 1
    # White ('w') moves DOWN: row + 1
    if color == 'b':
        MOVE_DIRS = [(-1, -1), (-1, 1)]
        KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        PROMOTION_ROW = 0
    else:
        MOVE_DIRS = [(1, -1), (1, 1)]
        KING_DIRS = [(1, -1), (1, 1), (-1, -1), (-1, 1)]
        PROMOTION_ROW = 7

    # Helper sets for O(1) lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    all_opp_pieces = opp_men_set.union(opp_kings_set)
    all_my_pieces = my_men_set.union(my_kings_set)

    # --- Move Generation ---
    
    def is_valid(r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def get_basic_moves():
        moves = []
        # Men Moves
        for r, c in my_men:
            for dr, dc in MOVE_DIRS:
                nr, nc = r + dr, c + dc
                if is_valid(nr, nc) and (nr, nc) not in all_my_pieces and (nr, nc) not in all_opp_pieces:
                    moves.append(((r, c), (nr, nc)))
        # King Moves
        for r, c in my_kings:
            for dr, dc in KING_DIRS:
                nr, nc = r + dr, c + dc
                if is_valid(nr, nc) and (nr, nc) not in all_my_pieces and (nr, nc) not in all_opp_pieces:
                    moves.append(((r, c), (nr, nc)))
        return moves

    def get_captures():
        captures = [] # List of (path, score, final_piece_type)
        
        # DFS for multi-jumps
        def dfs(r, c, is_king, current_path, current_score, visited, is_promoted):
            # Determine available directions
            dirs = KING_DIRS if is_king else MOVE_DIRS
            
            found_jump = False
            
            for dr, dc in dirs:
                mid_r, mid_c = r + dr, c + dc
                land_r, land_c = r + 2*dr, c + 2*dc
                
                # Check if jump is valid (inside board, land empty, mid has enemy)
                if not is_valid(land_r, land_c):
                    continue
                if (land_r, land_c) in all_my_pieces or (land_r, land_c) in all_opp_pieces:
                    continue
                
                # Check middle piece
                mid_piece = (mid_r, mid_c)
                if mid_piece in all_opp_pieces:
                    # Calculate potential score (Kings worth more)
                    capture_val = 5 if mid_piece in opp_kings_set else 3
                    new_score = current_score + capture_val
                    
                    # Add move to the path
                    new_path = current_path + [(r, c), (land_r, land_c)]
                    
                    # Mark visited (prevents immediate back-and-forth loops, though rules often prevent this)
                    # Standard Checkers rules forbid visiting a square twice in one turn.
                    if (land_r, land_c) in visited:
                        continue
                        
                    new_visited = visited.copy()
                    new_visited.add((land_r, land_c))
                    
                    found_jump = True
                    
                    # Check for promotion during the jump (standard rules: capture onto last row promotes)
                    promoted = False
                    landed_as_king = is_king
                    if not is_king and land_r == PROMOTION_ROW:
                        landed_as_king = True
                        promoted = True
                        # If promoted, future jumps use King directions
                    
                    # Recurse for further jumps
                    dfs(land_r, land_c, landed_as_king, new_path, new_score, new_visited, is_promoted or promoted)
            
            # If no jumps found from this node, record the capture chain
            if not found_jump and current_path:
                captures.append((current_path, current_score, is_promoted or is_king))

        # Start DFS from all active pieces
        for r, c in my_men:
            dfs(r, c, False, [], 0, {(r, c)}, False)
        for r, c in my_kings:
            dfs(r, c, True, [], 0, {(r, c)}, False)
            
        return captures

    # --- Evaluation & Selection ---

    def evaluate_move(start, end):
        # Heuristic score for non-capturing moves
        score = 0
        
        r, c = start
        nr, nc = end
        
        # 1. Promotion Incentive
        if color == 'b' and r == 6 and nr == 7 and start in my_men_set:
            score += 20
        if color == 'w' and r == 1 and nr == 0 and start in my_men_set:
            score += 20
            
        # 2. Safety & Positioning
        # Men: encourage advancement (away from back row)
        if start in my_men_set:
            if color == 'b': score += (7 - nr)  # Lower row is better
            else: score += (nr) # Higher row is better
        # Kings: encourage center control (rows 3, 4)
        else:
            if 2 <= nr <= 5: score += 2
            
        # 3. Avoid immediate losses (basic check if moving into threatened square)
        # Simplified: check if destination is attacked by opponent men (forwards)
        threatened = False
        opp_attack_dirs = [(1, -1), (1, 1)] if color == 'b' else [(-1, -1), (-1, 1)]
        for dr, dc in opp_attack_dirs:
            check_r, check_c = nr - dr, nc - dc
            if (check_r, check_c) in opp_men_set:
                threatened = True
                break
        if threatened:
            score -= 5
            
        return score

    # --- Main Decision Logic ---

    # 1. Check for Captures (Mandatory)
    capture_moves = get_captures()
    
    if capture_moves:
        # Sort captures:
        # Primary: Maximize capture score (Material gain)
        # Secondary: Prefer moves that result in a King (Promotion)
        # Tertiary: Maximize path length (more options later)
        # Quaternary: Prefer landing closer to promotion row (positional)
        
        best_capture = None
        best_val = -float('inf')
        
        for path, score, is_king in capture_moves:
            # Calculate positional bonus for the final landing square
            end = path[-1]
            pos_bonus = 0
            if is_king:
                # Kings prefer center
                if 2 <= end[0] <= 5: pos_bonus = 2
            else:
                # Men prefer advancing
                if color == 'b': pos_bonus = (7 - end[0]) * 0.5
                else: pos_bonus = (end[0]) * 0.5
            
            # Composite value
            val = (score * 10) + (len(path)//2 * 2) + pos_bonus
            
            if val > best_val:
                best_val = val
                best_capture = path
        
        # Return the start and end of the chain (first step is start, last is end)
        return (best_capture[0], best_capture[-1])

    # 2. No Captures: Heuristic Non-Capturing Moves
    basic_moves = get_basic_moves()
    
    if not basic_moves:
        # No moves available (Stalemate/Loss)
        # Return a dummy move or the only piece to avoid error, though game likely over
        # If we have pieces, we are stuck.
        # Fallback: return ((0,0),(0,0)) to indicate pass if allowed, or raise error.
        # In Checkers, passing isn't allowed. We must return something legal or a dummy.
        # We'll assume if list is empty, game is effectively over.
        # To prevent crash, we return a tuple of the first piece to itself (invalid but safe format)
        if all_my_pieces:
            p = next(iter(all_my_pieces))
            return (p, p)
        return ((0,0), (0,0))

    # Sort heuristic moves
    best_move = basic_moves[0]
    best_score = -float('inf')
    
    for move in basic_moves:
        s = evaluate_move(move[0], move[1])
        if s > best_score:
            best_score = s
            best_move = move
            
    return best_move
