
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Piece values for capture scoring
    piece_value = {
        'Q': 9,
        'R': 5,
        'B': 3,
        'N': 3,
        'P': 1,
        'K': 0  # King cannot be captured
    }

    # Identify own color for move parsing
    own_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'

    best_score = -1
    best_move = legal_moves[0]  # default fallback

    for move in legal_moves:
        score = 0

        # Immediate checkmate takes highest priority
        if move.endswith('#'):
            return move, memory

        # Reward check moves
        if move.endswith('+'):
            score += 1.5

        # Reward castling for king safety
        if move == 'O-O' or move == 'O-O-O':
            score += 1.0

        # Reward promotions
        if '=Q' in move:
            score += 8.0  # Queen promotion: huge gain
        elif '=R' in move:
            score += 4.0
        elif '=B' in move:
            score += 2.0
        elif '=N' in move:
            score += 2.0

        # Detect captures and score by captured piece value
        if 'x' in move:
            # Capture: the piece after 'x' is the captured square
            # Example: Bxf5 → captured on f5
            captured_square = ''.join(filter(str.isdigit, move.split('x')[1].split('=')[0]))
            if captured_square in pieces:
                piece_code = pieces[captured_square]
                if piece_code[0] == opponent_color:
                    piece_type = piece_code[1]
                    score += piece_value[piece_type]

        # Prefer earlier discovered best moves in tie
        if score > best_score:
            best_score = score
            best_move = move

    return best_move, memory
