
def policy(pieces: dict, to_play: str, legal_moves: list, memory: dict) -> tuple:
    """
    Chess move selection policy prioritizing:
    1. Immediate checkmate if available
    2. Capturing high-value enemy pieces
    3. Moving knights and bishops to central squares
    """
    # Helper to extract destination square from move string
    def get_square(move_str):
        if '=' in move_str:
            return move_str.split('=')[0]
        elif 'x' in move_str:
            parts = move_str.split('x')
            dest_part = parts[-1].split('=')[0] if '=' in parts[-1] else parts[-1]
            return dest_part
        else:
            return move_str[-2:] if len(move_str) >= 2 else move_str

    # Priority values for captured pieces (Q, R, B, N, P)
    piece_values = {'q': 9, 'r': 5, 'b': 3, 'n': 3, 'p': 1, 'k': 0}

    # Check for immediate checkmate moves
    checkmate_moves = [m for m in legal_moves if m.endswith('++')]
    if checkmate_moves:
        return (checkmate_moves[0], {})

    # Find best capture move
    best_capture = None
    max_value = -1
    for move in legal_moves:
        dest = get_square(move)
        square_occupant = pieces.get(dest, '')
        if not square_occupant or square_occupant[0] == to_play[0]:
            continue  # Not capturing opponent's piece
        captured_type = square_occupant[1].lower()
        captured_value = piece_values.get(captured_type, 0)
        if captured_value > max_value:
            max_value = captured_value
            best_capture = move

    if best_capture is not None:
        return (best_capture, {})

    # Square desirability map for knights/bishops
    square_scores = {
        'd4': 100, 'd5': 90, 'e4': 100, 'e5': 90,
        'c3': 60, 'f3': 60, 'c6': 60, 'f6': 60,
        'a4': 20, 'h4': 20, 'a5': 20, 'h5': 20,
        'a3': 10, 'h3': 10, 'a6': 10, 'h6': 10,
        'b4': 30, 'b5': 40, 'g4': 30, 'g5': 40,
        **{f'{c2}{rank}': max(1, square_scores.get(f'{c2}{rank}', 0)) for c2 in 'chf' for rank in range(1,9)}
    }

    # Select best move based on positional value
    best_score = -float('inf')
    best_move = None
    for move in legal_moves:
        dest = get_square(move)
        dest_score = square_scores.get(dest, 0)
        if '=' in move:
            piece_type = 'P'
        else:
            first_char = move[0]
            piece_type = first_char.upper() if first_char in 'NBQKR' else 'P'
        
        # Prioritize knights and bishops to central squares
        if piece_type in ['N', 'B']:
            priority = 7 if piece_type == 'N' else 5
            score = dest_score * priority + 1000 if 'N' == piece_type and dest in {'d4', 'e5', 'd5', 'e4'} else pos_score
        elif piece_type == 'R':
            score = dest_score * 3 if any(c in 'a1h8' for c in dest) else dest_score * 2
        else:
            score = dest_score

        if score > best_score:
            best_score = score
            best_move = move

    return (best_move, {}) if legal_moves else ('', {})
