
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': 0,
    }
    
    check_bonus = 0.5
    castle_bonus = 5
    
    promotion_gains = {
        'Q': 8,  # Queen promotion gain (9 - 1)
        'R': 4,  # Rook promotion gain (5 - 1)
        'B': 2,  # Bishop promotion gain (3 - 1)
        'N': 2,  # Knight promotion gain (3 - 1)
    }
    
    best_score = -float('inf')
    best_move = None
    
    for move in legal_moves:
        score = 0
        
        # Handle castling
        if move == 'O-O' or move == 'O-O-O':
            score += castle_bonus
        
        # Handle promotions
        if '=' in move and move not in ['O-O', 'O-O-O']:
            promoted_type = move.split('=')[1]
            score += promotion_gains.get(promoted_type, 0)
        
        # Handle captures
        if 'x' in move:
            try:
                dest_part = move.split('x')[-1]
                dest_str = dest_part.split('=')[0]
                destination = dest_str
            except:
                destination = 'a1'  # Default in case of parsing error
            
            if destination in pieces:
                captured_piece = pieces[destination]
                captured_color = captured_piece[0]
                current_player_color = 'w' if to_play == 'white' else 'b'
                if captured_color != current_player_color:
                    captured_type = captured_piece[1]
                    score += piece_values.get(captured_type, 0)
            else:
                # En passant capture: assume pawn
                score += 1
        
        # Handle check or checkmate
        if move.endswith('#'):
            score += 10000
        elif move.endswith('+'):
            score += check_bonus
        
        # Update best move if this move is better
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score:
            # Tie-breaker: prefer the first occurrence in legal_moves
            pass  # Best move remains the first one encountered with the max score
    
    return best_move
