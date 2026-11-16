
def policy(me, opp, color):
    target_home = 0 if color == 'b' else 7
    moves = []

    # Generate all possible moves
    for (r, c) in me:
        row_incr = -1 if color == 'b' else 1
        new_r = r + row_incr

        if 0 <= new_r < 8:
            # Straight move
            new_pos_straight = (new_r, c)
            if new_pos_straight not in me:
                is_capture = False
                if new_pos_straight in opp:
                    is_capture = True
                moves.append(((r, c), new_pos_straight, is_capture))

            # Diagonal left
            new_col = c - 1
            if 0 <= new_col < 8:
                new_pos_diag = (new_r, new_col)
                if new_pos_diag not in me and new_pos_diag in opp:
                    moves.append(((r, c), new_pos_diag, True))

                # Diagonal right
                new_col = c + 1
                new_pos_diag = (new_r, new_col)
                if new_pos_diag not in me and new_pos_diag in opp:
                    moves.append(((r, c), new_pos_diag, True))

    # Step 1: Check for promotion moves
    for move in moves:
        _, new_pos, _ = move
        if new_pos[0] == target_home:
            return (new_pos, new_pos)

    # Step 2: Prioritize capture moves
    capture_moves = [m for m in moves if m[2]]

    if capture_moves:
        best_score = -1
        best_move = None
        for move in capture_moves:
            from_pos, to_pos, _ = move
            captured_row = to_pos[0]
            if color == 'b':
                # Captured piece is white, enemy home is 7
                enemy_distance = 7 - captured_row
            else:
                # Captured piece is black, enemy home is 0
                enemy_distance = captured_row
            score = 1000 + enemy_distance
            if score > best_score:
                best_score = score
                best_move = move
        return (best_move[0], best_move[1])

    # Step 3: If no capture, return any valid move
    # Since all moves are valid and move forward, return the first one
    return moves[0][0], moves[0][1] if moves else None
