
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    best_score = -float('inf')
    best_move = legal_moves[0]

    for move in legal_moves:
        score = 0.0

        # Bonus for castling
        if move == 'O-O' or move == 'O-O-O':
            score += 5.0

        # Penalty for non-castling king moves
        if move.startswith('K') and move not in ['O-O', 'O-O-O']:
            score -= 0.5

        # Penalty for non-capturing, non-promotion queen moves
        if move.startswith('Q') and not ('x' in move or '=' in move):
            score -= 0.3

        # Handle promotions
        if '=' in move:
            promo_parts = move.split('=')
            promo_piece = promo_parts[1][0]  # Take the first character, e.g., 'Q'
            promo_value = piece_values.get(promo_piece, 0)
            # Promotion gain is (new piece value) - pawn value (1)
            promo_gain = promo_value - 1
            score += promo_gain

            # Check if the promotion is also a capture (has 'x')
            if 'x' in move:
                x_index = move.index('x')
                # Get the captured square up to the '='
                dest_square_part = move[x_index+1:].split('=')[0]
                captured_square = dest_square_part
                captured_p = pieces.get(captured_square)
                if captured_p:
                    captured_value = piece_values.get(captured_p[1], 0)
                    # moving piece is a pawn (value 1)
                    capture_gain = captured_value - 1
                    score += capture_gain

        # Handle normal captures (no promotion)
        elif 'x' in move:
            x_index = move.index('x')
            # Extract the destination square, up to first non-alphanumeric
            dest_square_part = move[x_index+1:]
            # Split on the first occurrence of any of +, #, =, etc.
            for sep in ['+', '#', '=']:
                if sep in dest_square_part:
                    dest_square_part = dest_square_part.split(sep)[0]
                    break
            captured_square = dest_square_part
            captured_p = pieces.get(captured_square)
            if captured_p:
                captured_value = piece_values.get(captured_p[1], 0)
                # Determine moving piece's value
                move_start = move[0]
                if move_start in 'abcdefgh':
                    moving_value = 1  # pawn
                else:
                    if move_start == 'K':
                        moving_value = 0
                    else:
                        # For other pieces
                        moving_value = piece_values.get(move_start, 0)
                capture_gain = captured_value - moving_value
                score += capture_gain

        # Bonus for check
        if move.endswith('+'):
            score += 0.1

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
