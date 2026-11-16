
def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    direction = 1 if color == 'w' else -1
    target_row = 0 if color == 'b' else 7  # Opponent's home row
    all_moves = []

    # Generate all possible moves
    for (r, c) in me:
        # Check straight move
        new_r = r + direction
        new_c = c
        if 0 <= new_r < 8:
            new_pos = (new_r, new_c)
            if new_pos not in me_set and new_pos not in opp_set:
                all_moves.append(((r, c), new_pos))
        
        # Check diagonal captures
        for delta_col in (-1, 1):
            new_r = r + direction
            new_c = c + delta_col
            if 0 <= new_r < 8 and 0 <= new_c < 8:
                new_pos = (new_r, new_c)
                if new_pos in opp_set:
                    all_moves.append(((r, c), new_pos))
    
    # Check for any move that reaches the target row immediately
    for move in all_moves:
        _, to_pos = move
        if to_pos[0] == target_row:
            return move
    
    # Check for valid capture moves
    opp_set = set(opp)  # Reconstruct to avoid set modification issues
    captures = [m for m in all_moves if m[1] in opp_set]
    if captures:
        best_capture = None
        best_priority = float('-inf')
        for capture in captures:
            _, (new_r, _) = capture
            if color == 'b':
                priority = -new_r
            else:
                priority = new_r
            if priority > best_priority:
                best_priority = priority
                best_capture = capture
        return best_capture
    
    # No captures, select best move towards target
    best_move = None
    best_val = float('-inf')
    for move in all_moves:
        _, (new_r, _) = move
        if color == 'b':
            value = -new_r
        else:
            value = new_r
        if value > best_val:
            best_val = value
            best_move = move
    return best_move
