
def policy(me, opp, color):
    # Convert opponent positions to a set for faster lookup
    opp_set = set(opp)
    my_set = set(me)
    
    # Define movement direction based on color
    direction = 1 if color == 'b' else -1  # Black moves down (increasing row), white moves up (decreasing row)
    home_row = 0 if color == 'w' else 7
    opp_home_row = 0 if color == 'b' else 7
    
    # Generate all legal moves
    legal_moves = []
    
    for r, c in me:
        # Forward move
        fr, fc = r + direction, c
        if 0 <= fr <= 7 and (fr, fc) not in my_set and (fr, fc) not in opp_set:
            legal_moves.append(((r, c), (fr, fc)))
            
        # Diagonal captures
        for dc in [-1, 1]:
            tr, tc = r + direction, c + dc
            if 0 <= tr <= 7 and 0 <= tc <= 7 and (tr, tc) in opp_set:
                legal_moves.append(((r, c), (tr, tc)))
                
        # Diagonal non-captures
        for dc in [-1, 1]:
            tr, tc = r + direction, c + dc
            if 0 <= tr <= 7 and 0 <= tc <= 7 and (tr, tc) not in my_set and (tr, tc) not in opp_set:
                legal_moves.append(((r, c), (tr, tc)))

    # 1. Check for winning moves
    for move in legal_moves:
        (_, _), (to_r, _) = move
        if to_r == opp_home_row:
            return move

    # 2. Check for safe captures
    safe_captures = []
    for move in legal_moves:
        (from_r, from_c), (to_r, to_c) = move
        if abs(from_c - to_c) == 1 and (to_r, to_c) in opp_set:
            # This is a capture. Check if the capturing piece can be immediately recaptured.
            is_safe = True
            # Check if opponent can recapture from their new positions
            opp_direction = 1 if color == 'w' else -1  # Opponent's direction
            for orc, occ in opp:
                # Opponent can move forward to where we moved
                if (orc + opp_direction, occ) == (to_r, to_c):
                    is_safe = False
                    break
                # Opponent can capture from diagonals to where we moved
                for dc in [-1, 1]:
                    if (orc + opp_direction, occ + dc) == (to_r, to_c):
                        is_safe = False
                        break
                if not is_safe:
                    break
            if is_safe:
                safe_captures.append(move)
    
    if safe_captures:
        # Among safe captures, prefer those that advance more
        best_capture = max(safe_captures, key=lambda move: move[1][0] if color == 'b' else -move[1][0])
        return best_capture

    # 3. Advance pieces, especially from back ranks
    if legal_moves:
        # Prioritize advancing pieces toward opponent's home row
        def move_priority(move):
            (_, _), (to_r, _) = move
            # Give higher priority to moves that advance more
            if color == 'b':
                return to_r
            else:
                return -to_r
        
        # Sort moves by priority
        legal_moves.sort(key=move_priority, reverse=True)
        return legal_moves[0]

    # This should never happen if there are legal moves, but just in case:
    # Return the first legal move found
    if legal_moves:
        return legal_moves[0]
        
    # Should never reach here as we must have a legal move
    # But if we do, return a default (should not happen in a real game)
    return ((0, 0), (0, 0))
