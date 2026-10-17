
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    max_score = -1
    best_move = legal_moves[0]

    for move in legal_moves:
        score = 0
        # Castling bonus
        if move in ['O-O', 'O-O-O']:
            score += 2
        # Promotion bonus
        if '=Q' in move:
            score += 8
        elif '=R' in move:
            score += 4
        elif '=B' in move:
            score += 2
        elif '=N' in move:
            score += 2
        # Checkmate detection
        if '#' in move:
            score += 1000
        # Check bonus
        if '+' in move:
            score += 1
        # Capture evaluation
        if 'x' in move:
            parts = move.split('x')
            if len(parts) >= 2:
                target_square = parts[1][:2]
                if target_square in pieces:
                    captured_piece = pieces[target_square]
                    captured_type = captured_piece[1]
                    score += piece_values.get(captured_type, 0)
        # Central pawn move bonus
        if len(move) == 2 and move[0] in 'abcdefgh' and move[1] in '3456' and 'x' not in move:
            if move in ['d4', 'e4', 'd5', 'e5']:
                score += 0.5
        # Update best move
        if score > max_score or (score == max_score and move < best_move):
            max_score = score
            best_move = move

    return best_move
