
def policy(pieces, to_play, legal_moves, memory):
    # Piece values
    piece_values = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
    
    # Helper to get piece value from code
    def get_piece_value(code):
        if code is None:
            return 0
        return piece_values.get(code[1], 0)
    
    # Enemy color
    enemy = 'b' if to_play == 'white' else 'w'
    
    # Center squares (same for both sides)
    center_squares = ['d4', 'd5', 'e4', 'e5']
    
    best_move = None
    best_score = -10000  # very low
    
    for move in legal_moves:
        score = 0
        
        # Check for checkmate and check
        if move.endswith('#'):
            score += 1000
        elif move.endswith('+'):
            score += 100
        
        # Check for capture
        if 'x' in move:
            # Extract destination square: split by 'x', take last part, remove promotion
            parts = move.split('x')
            dest_part = parts[-1]
            if '=' in dest_part:
                dest_part = dest_part.split('=')[0]
            # dest_part should be the destination square (e.g., 'f5')
            if len(dest_part) >= 2 and dest_part[-2] in 'abcdefgh' and dest_part[-1] in '12345678':
                dest_square = dest_part[-2:]
                if dest_square in pieces:
                    enemy_piece = pieces[dest_square]
                    if enemy_piece[0] == enemy:
                        score += get_piece_value(enemy_piece)
                else:
                    # En passant or other: assume pawn capture
                    score += 1
        
        # Check for promotion
        if '=' in move:
            # The promotion piece is after '=' and before any check/mate
            promo_str = move.split('=')[1]
            # Remove any trailing '+#'
            promo_piece = promo_str.rstrip('+#')
            if promo_piece in piece_values:
                score += piece_values[promo_piece]
        
        # Check for castling
        if move in ['O-O', 'O-O-O']:
            score += 20  # king safety bonus
        
        # Parse destination square for non-castling moves
        dest_square = None
        # Remove annotations
        temp_move = move.rstrip('+#')
        if '=' in temp_move:
            temp_move = temp_move.split('=')[0]
        # Now the last two characters should be the destination square
        if len(temp_move) >= 2 and temp_move[-2] in 'abcdefgh' and temp_move[-1] in '12345678':
            dest_square = temp_move[-2:]
        
        # Center control bonus
        if dest_square and dest_square in center_squares:
            score += 5
        
        # Development and pawn moves
        if dest_square:
            # Determine piece type if any
            piece_type = None
            # If the move starts with a capital letter (and not 'O' for castling, but castling already handled)
            if temp_move[0] in 'KQRBN':
                piece_type = temp_move[0]
            
            # Development for pieces
            if to_play == 'white':
                if piece_type == 'N' and dest_square in ['f3', 'c3']:
                    score += 10
                elif piece_type == 'B' and dest_square in ['c4', 'f4', 'b5', 'g5']:
                    score += 8
                elif piece_type == 'Q' and dest_square in ['d2', 'e2']:
                    score += 2
                elif piece_type == 'R' and dest_square in ['d1', 'e1']:
                    score += 3
            else:  # black
                if piece_type == 'N' and dest_square in ['f6', 'c6']:
                    score += 10
                elif piece_type == 'B' and dest_square in ['c5', 'f5', 'b4', 'g4']:
                    score += 8
                elif piece_type == 'Q' and dest_square in ['d7', 'e7']:
                    score += 2
                elif piece_type == 'R' and dest_square in ['d8', 'e8']:
                    score += 3
            
            # Pawn moves to center
            if piece_type is None:  # pawn move
                if to_play == 'white':
                    if dest_square in ['e4', 'd4', 'c4', 'f4']:
                        score += 6
                else:
                    if dest_square in ['e5', 'd5', 'c5', 'f5']:
                        score += 6
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    # Fallback: if no best move found (shouldn't happen), pick first legal move
    if best_move is None and legal_moves:
        best_move = legal_moves[0]
    
    # Return the move and memory (we don't modify memory, but we could store something)
    return best_move, memory.copy()
