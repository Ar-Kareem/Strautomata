
def policy(my_men, my_kings, opp_men, opp_kings, color):
    def get_cap_priority(move):
        from_pos, to_pos = move
        dr_total = to_pos[0] - from_pos[0]
        dc_total = to_pos[1] - from_pos[1]
        dr = dr_total // 2
        dc = dc_total // 2
        inter_r = from_pos[0] + dr
        inter_c = from_pos[1] + dc
        is_king_capture = (inter_r, inter_c) in opp_kings
        promote = dest_promote_move(move[1], color)
        if promote:
            return (0, 0, dr, dc)
        if is_king_capture:
            return (1, 0, dr, dc)
        return (2, get_dist_priority(to_pos, color), dr, dc)

    def dest_promote_move(to_pos, color):
        promote_row = 0 if color == 'b' else 7
        return to_pos[0] == promote_row

    def get_dist_priority(to_pos, color):
        to_r = to_pos[0]
        if color == 'b':
            return to_r
        else:
            return 7 - to_r

    # Generate all possible capture moves
    captures = []
    my_pieces = my_men + my_kings
    for piece in my_pieces:
        r, c = piece
        # Determine movement directions for capture
        if piece in my_kings:
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            if color == 'b':
                dirs = [(-1, -1), (-1, 1)]
            else:
                dirs = [(1, -1), (1, 1)]
        for dr, dc in dirs:
            inter_r, inter_c = r + dr, c + dc
            dest_r, dest_c = inter_r + dr, inter_c + dc
            if 0 <= inter_r < 8 and 0 <= inter_c < 8 and 0 <= dest_r < 8 and 0 <= dest_c < 8:
                # Check if intermediate has opponent's piece
                if (inter_r, inter_c) in opp_men or (inter_r, inter_c) in opp_kings:
                    # Check destination is empty
                    if (dest_r, dest_c) not in my_men and (dest_r, dest_c) not in my_kings and (dest_r, dest_c) not in opp_men and (dest_r, dest_c) not in opp_kings:
                        captures.append(((piece[0], piece[1]), (dest_r, dest_c)))

    if captures:
        # Prioritize captures that promote or capture kings
        captures.sort(key=get_cap_priority)
        # Choose the highest priority move
        best = captures[0][0], captures[0][1]
        return best

    # Generate non-capture moves
    non_captures = []
    for piece in my_men + my_kings:
        r, c = piece
        directions = []
        if piece in my_kings:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            if color == 'b':
                directions = [(-1, -1), (-1, 1)]
            else:
                directions = [(1, -1), (1, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) not in my_men and (nr, nc) not in my_kings and (nr, nc) not in opp_men and (nr, nc) not in opp_kings:
                    non_captures.append(((r, c), (nr, nc)))

    if non_captures:
        promote_moves = [m for m in non_captures if dest_promote_move(m[1], color)]
        if promote_moves:
            # Select move closest to promotion (already in promotion priority)
            # Sort by distance in reverse for black/w
            promote_moves.sort(key=lambda m: get_dist_priority(m[1], color))
            return promote_moves[-1] if color == 'b' else promote_moves[0]
        # Sort normal moves by priority (distance to promotion)
        non_captures.sort(key=lambda m: (get_dist_priority(m[1], color),))
        return non_captures[0]
    else:
        # Shouldn't happen as per problem statement, but fallback
        return ((0, 0), (1, 1))
