
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Define opponent's home row based on current player's color
    opp_home_row = 7 if color == 'b' else 0
    
    # Generate all possible moves for current player
    moves = []
    for piece in me:
        r, c = piece
        # Determine movement direction based on color
        if color == 'b':  # Black moves downward (increasing row)
            directions = [(1, 0), (1, 1), (1, -1)]
        else:  # White moves upward (decreasing row)
            directions = [(-1, 0), (-1, 1), (-1, -1)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            # Check if new position is on the board
            if 0 <= nr < 8 and 0 <= nc < 8:
                # Check if target is empty (non-capture) or opponent piece (capture)
                if (nr, nc) not in me:
                    # Check if target is opponent piece (capture)
                    if (nr, nc) in opp:
                        moves.append(((r, c), (nr, nc)))
                    # Check if target is empty (non-capture)
                    elif (nr, nc) not in opp:
                        moves.append(((r, c), (nr, nc)))
    
    # Check for immediate wins (capture all pieces or reach opponent's home row)
    for move in moves:
        from_pos, to_pos = move
        # Simulate move: remove captured piece if applicable
        new_me = [p for p in me if p != from_pos]
        if to_pos in opp:
            new_me = [p for p in new_me if p != to_pos]
        # Check if any piece reached opponent's home row
        if any(r == opp_home_row for r, c in new_me):
            return move
    
    # Check for capture moves
    for move in moves:
        from_pos, to_pos = move
        if to_pos in opp:
            return move
    
    # Evaluate forward moves (toward opponent's home row)
    best_move = None
    best_distance = float('inf')
    for move in moves:
        from_pos, to_pos = move
        # Calculate distance to opponent's home row
        dist = abs(to_pos[0] - opp_home_row)
        # Prioritize moves that reduce distance
        if dist < best_distance:
            best_distance = dist
            best_move = move
    
    # Check safety for non-capture moves
    if best_move is None:
        best_move = moves[0]
    else:
        from_pos, to_pos = best_move
        if to_pos not in opp:  # Non-capture move
            # Check if opponent can capture this position next turn
            for opp_piece in opp:
                opp_r, opp_c = opp_piece
                # Determine opponent's movement direction
                if color == 'b':  # Black moves downward
                    opp_dirs = [(1, 0), (1, 1), (1, -1)]
                else:  # White moves upward
                    opp_dirs = [(-1, 0), (-1, 1), (-1, -1)]
                for dr, dc in opp_dirs:
                    nr, nc = opp_r + dr, opp_c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        if (nr, nc) == to_pos:
                            # Opponent can capture this position
                            best_move = None
                            break
                if best_move is None:
                    break
    
    return best_move
