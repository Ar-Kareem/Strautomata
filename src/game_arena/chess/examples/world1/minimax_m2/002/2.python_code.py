
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Step 1: Check for checkmate
    for move in legal_moves:
        if move.endswith('#'):
            return move
    
    # Step 2: Capture moves with highest captured piece value
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    best_capture_move = None
    max_captured_value = -1
    
    for move in legal_moves:
        if 'x' in move:
            parts = move.split('x')
            target_part = parts[-1]
            target_square = target_part[0:2]
            captured_piece = pieces.get(target_square)
            if captured_piece is not None:
                captured_value = piece_values[captured_piece[1]]
            else:
                if move[0].islower():
                    captured_value = 1
                else:
                    captured_value = 0
            if captured_value > max_captured_value:
                max_captured_value = captured_value
                best_capture_move = move
    
    if best_capture_move is not None:
        return best_capture_move
    
    # Step 3: Non-capturing checks
    for move in legal_moves:
        if 'x' not in move and move.endswith('+'):
            return move
    
    # Step 4: Non-capturing non-checking moves
    best_move = None
    best_score = -1
    
    for move in legal_moves:
        if 'x' not in move and not move.endswith('+'):
            score = 0
            if move in ['O-O', 'O-O-O']:
                score = 10
            else:
                if '=' in move:
                    target_square = move.split('=')[0]
                else:
                    target_square = move[-2:]
                if target_square in ['d4', 'd5', 'e4', 'e5']:
                    score = 1
            if score > best_score:
                best_score = score
                best_move = move
    
    if best_move is not None:
        return best_move
    
    return legal_moves[0]
