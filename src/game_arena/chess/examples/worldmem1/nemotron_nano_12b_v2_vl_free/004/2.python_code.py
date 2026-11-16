
def policy(pieces, to_play, legal_moves, memory):
    if not legal_moves:
        return ("", {})

    opponent = 'b' if to_play == 'white' else 'w'
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}

    # Step 1: Check for captures and select the highest-value capture
    captures = []
    for move in legal_moves:
        if 'x' in move:
            # Split move into target parts
            parts = move.split('x', 1)
            target_sq = parts[1][:2] if len(parts) > 1 else None
            if target_sq and target_sq in pieces:
                captured_piece = pieces[target_sq]
                if captured_piece[0] == opponent:
                    captured_type = captured_piece[1]
                    if captured_type in piece_values:
                        captures.append((move, piece_values[captured_type]))
    
    # Select the best capture if any
    if captures:
        # Sort by value descending, then by move string (lex order)
        captures.sort(key=lambda x: (-x[1], x[0]))
        best_capture = captures[0][0]
        return (best_capture, {})

    # Step 2: Prioritize castling if possible
    castling_moves = ['O-O', 'O-O-O']
    possible_castling = [m for m in castling_moves if m in legal_moves]
    if possible_castling:
        return (min(possible_castling), {})  # Prefer 'O-O' over 'O-O-O'

    # Step 3: Prioritize moves involving the highest-value pieces
    move_ranking = []
    for move in legal_moves:
        move_part = move.split('=', 1)[0]  # Ignore promotion part
        if move_part == 'O-O' or move_part == 'O-O-O':
            continue  # Already handled castling

        if move_part[0] in piece_values:
            piece_type = move_part[0]
            move_ranking.append((-piece_values[piece_type], move))
        elif move_part[0] == 'O':
            # Castling moves like 'O-O-O' are handled earlier
            continue
        else:
            # Pawn moves or other promotions
            move_ranking.append((-1, move))  # Pawns have lower priority

    # Select the best move based on priority
    if move_ranking:
        move_ranking.sort(key=lambda x: x[0])
        best_move = move_ranking[0][1]
        return (best_move, {})

    # Fallback to first legal move if none of the above
    return (legal_moves[0], {})
