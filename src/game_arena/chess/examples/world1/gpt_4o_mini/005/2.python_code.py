
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    opponent_color = 'b' if to_play == 'white' else 'w'
    opponent_pieces = {pos: piece for pos, piece in pieces.items() if piece[0] == opponent_color}
    
    # Step 1: Check for immediate checkmate
    for move in legal_moves:
        # Simple checks; a more robust engine would need proper checks
        if 'checkmate' in move:
            return move
    
    # Step 2: Evaluate material gain
    piece_value = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }

    best_move = None
    best_value = float('-inf')
    
    for move in legal_moves:
        capture = None
        if 'x' in move:  # This move captures a piece
            captured_piece_square = move[-2:]  # last two chars denote the square
            if captured_piece_square in opponent_pieces:
                captured_piece = opponent_pieces[captured_piece_square]
                capture_value = piece_value[captured_piece[1]]  # get the value
                if capture_value > best_value:
                    best_value = capture_value
                    best_move = move

    # Step 3: King safety and strategic positioning
    if best_move is None:
        for move in legal_moves:
            # Example check for safe move; actual code should validate king safety
            if 'O-O' in move or 'O-O-O' in move:  # prioritize castling if available
                return move
            # More checks can be added here for king safety and board position
    
    # Fallback (just return a legal move)
    return legal_moves[0] if legal_moves else ''
