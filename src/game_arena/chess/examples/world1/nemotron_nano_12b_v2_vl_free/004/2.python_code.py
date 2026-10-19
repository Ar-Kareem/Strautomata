
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    value_map = {'Q': 900, 'R': 500, 'B': 300, 'N': 300, 'P': 100}

    scored_moves = []
    for move in legal_moves:
        score = 0

        # Check for promotions (prioritized highest)
        if '=' in move:
            _, promoted_piece = move.split('=', 1)
            current_score = 10000 + value_map.get(promoted_piece, 0)
        # Check for captures
        elif 'x' in move:
            dest_square = move.split('x', 1)[1]
            captured_piece = pieces.get(dest_square, '')
            if captured_piece:
                captured_val = value_map.get(captured_piece[1], 0)
                capturing_char = move[0] if move[0] in value_map else 'P'
                capturing_val = value_map.get(capturing_char, 0)
                current_score = captured_val - capturing_val
            else:
                current_score = 0
        # Check moves
        elif move.endswith('+'):
            current_score += 2500
        # Castling moves
        elif move.startswith('O-'):
            current_score += 2000
        else:
            current_score = 0

        scored_moves.append((-current_score, move))

    scored_moves.sort()
    return scored_moves[0][1]
