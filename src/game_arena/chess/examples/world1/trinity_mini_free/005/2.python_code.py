
def policy(pieces, to_play, legal_moves):
    # Define piece values for material evaluation
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100
    }
    
    best_move = None
    best_score = -1
    
    for move in legal_moves:
        # Prioritize castling for king safety
        if move in ['O-O', 'O-O-O']:
            score = 10
            if score > best_score:
                best_score = score
                best_move = move
            continue
        
        # Evaluate captures
        if 'x' in move:
            dest = move.split('x')[-1]
            if dest in pieces:
                captured_piece = pieces[dest]
                piece_type = captured_piece[1]
                score = piece_values.get(piece_type, 0)
            else:
                score = 0
        else:
            score = 0
        
        # Evaluate promotions
        if '=' in move:
            promoted_piece = move.split('=')[-1]
            if promoted_piece in piece_values:
                score += piece_values[promoted_piece]
        
        # Update best move if current score is higher
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
