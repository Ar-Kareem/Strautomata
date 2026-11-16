
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    best_score = -10**9
    best_move = None

    for move in legal_moves:
        score = 0.0
        # Check for checkmate (#) or check (+) at the end of the move
        if move[-1] == '#':
            score += 1000.0  # Checkmate bonus
        elif move[-1] == '+':
            score += 0.5     # Check bonus

        # Clean move string by removing trailing check/mate symbols
        clean_move = move
        if clean_move[-1] in ['+', '#']:
            clean_move = clean_move[:-1]

        # Handle castling moves
        if clean_move in ['O-O', 'O-O-O']:
            score += 0.3  # Castling bonus
        else:
            # Extract target square and promotion piece if applicable
            target_square = None
            promotion_piece = None

            if '=' in clean_move:
                parts = clean_move.split('=')
                move_without_promotion = parts[0]
                target_square = move_without_promotion[-2:]
                promotion_piece = parts[-1]  # Promotion piece (e.g., 'Q')
            else:
                target_square = clean_move[-2:]

            # Check for capture on the target square
            if target_square in pieces:
                captured_piece = pieces[target_square]
                score += piece_values[captured_piece[1]]  # Add value of captured piece

            # Add promotion gain if applicable
            if promotion_piece:
                score += piece_values[promotion_piece] - piece_values['P']  # Gain from promotion

        # Update best move if current move has higher score
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
