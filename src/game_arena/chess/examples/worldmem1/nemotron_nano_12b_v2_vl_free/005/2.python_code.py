
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
    opp_color = 'b' if to_play == 'white' else 'w'
    best_move = None
    best_score = -float('inf')

    # Check for checkmate moves (prioritize if any available)
    checkmate_moves = [move for move in legal_moves if move.endswith('#')]
    if checkmate_moves:
        return (checkmate_moves[0], memory)

    # Prioritize promotions to higher-value pieces
    promotions = []
    for move in legal_moves:
        if '=' in move:
            promo_piece = move.split('=')[1]
            if promo_piece.lower() in piece_values:
                promotions.append((move, piece_values[promo_piece.lower()]))

    if promotions:
        promotions.sort(key=lambda x: -x[1])
        best_move = promotions[0][0]
    else:
        # Evaluate captures first
        capture_scores = []
        for move in legal_moves:
            dest_sq = move[-2:]
            captured_piece = pieces.get(dest_sq, '').lower()
            if captured_piece and captured_piece != 'k':  # king cannot be captured
                cap_value = piece_values.get(captured_piece[1], 0)
                capture_scores.append((move, cap_value))
            else:
                capture_scores.append((move, 0))

        if capture_scores:
            # Add bonus for promotions even if not captured
            for move in legal_moves:
                if '=' in move and best_move != move:
                    promo_piece = move.split('=')[1].lower()
                    if promo_piece in priority:
                        bonus = piece_values[promo_piece]
                        cap_value = capture_scores[legal_moves.index(move)][1] + bonus
                        capture_scores[legal_moves.index(move)] = (move, cap_value + bonus)

            # Select move with highest score
            capture_scores.sort(key=lambda x: -x[1])
            best_move = capture_scores[0][0]
        else:
            # Fallback to any move if no captures
            best_move = legal_moves[0]

    return (best_move, memory) if memory is None else (best_move, {})
