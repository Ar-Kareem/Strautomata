
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Check for immediate wins (reaching opponent's home row)
    for piece in me:
        r, c = piece
        if color == 'b':  # Black moves down (towards row 0)
            directions = [(1, 0), (1, -1), (1, 1)]
        else:  # White moves up (towards row 7)
            directions = [(-1, 0), (-1, -1), (-1, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = (nr, nc)
                # Check if move reaches opponent's home row
                if color == 'b' and nr == 0:
                    return ((r, c), (nr, nc))
                elif color == 'w' and nr == 7:
                    return ((r, c), (nr, nc))
                # Check if capturing the last opponent piece
                if target in opp and len(opp) == 1:
                    return ((r, c), (nr, nc))
    
    # Generate all possible moves
    moves = []
    for piece in me:
        r, c = piece
        if color == 'b':
            directions = [(1, 0), (1, -1), (1, 1)]
        else:
            directions = [(-1, 0), (-1, -1), (-1, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = (nr, nc)
                if target not in opp:  # Empty square
                    moves.append(((r, c), (nr, nc)))
                else:  # Capture opponent piece
                    moves.append(((r, c), (nr, nc)))
    
    # Evaluate moves using heuristic
    best_move = None
    best_eval = -float('inf')
    for move in moves:
        from_pos, to_pos = move
        # Simulate move on a copy of the state
        new_me = [p for p in me if p != from_pos] + [to_pos]
        new_opp = [p for p in opp if p != to_pos]
        # Evaluate new state
        my_pieces = len(new_me)
        opp_pieces = len(new_opp)
        total_distance = 0
        for piece in new_me:
            r, c = piece
            if color == 'w':  # White moves up (distance to row 7)
                total_distance += 7 - r
            else:  # Black moves down (distance to row 0)
                total_distance += r
        eval_val = my_pieces - opp_pieces + total_distance
        # Select move with highest evaluation
        if eval_val > best_eval:
            best_eval = eval_val
            best_move = move
    return best_move
