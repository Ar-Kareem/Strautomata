
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    import random
    
    if not legal_moves:
        return ""
    
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Position values for piece placement (simplified)
    pawn_table = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10,-20,-20, 10, 10,  5,
        5, -5,-10,  0,  0,-10, -5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5,  5, 10, 25, 25, 10,  5,  5,
       10, 10, 20, 30, 30, 20, 10, 10,
       50, 50, 50, 50, 50, 50, 50, 50,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    knight_table = [
       -50,-40,-30,-30,-30,-30,-40,-50,
       -40,-20,  0,  5,  5,  0,-20,-40,
       -30,  5, 10, 15, 15, 10,  5,-30,
       -30,  0, 15, 20, 20, 15,  0,-30,
       -30,  5, 15, 20, 20, 15,  5,-30,
       -30,  0, 10, 15, 15, 10,  0,-30,
       -40,-20,  0,  0,  0,  0,-20,-40,
       -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    def square_to_index(square):
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return rank * 8 + file
    
    def get_positional_value(piece_type, square, color):
        if piece_type == 'P':
            idx = square_to_index(square)
            if color == 'b':
                idx = 63 - idx
            return pawn_table[idx] * 0.01
        elif piece_type == 'N':
            idx = square_to_index(square)
            if color == 'b':
                idx = 63 - idx
            return knight_table[idx] * 0.01
        return 0
    
    def evaluate_position(pos, player):
        score = 0
        my_color = 'w' if player == 'white' else 'b'
        opp_color = 'b' if my_color == 'w' else 'w'
        
        for square, piece in pos.items():
            color = piece[0]
            piece_type = piece[1]
            value = piece_values[piece_type]
            pos_value = get_positional_value(piece_type, square, color)
            
            if color == my_color:
                score += value + pos_value
            else:
                score -= value + pos_value
        
        return score
    
    def apply_move(pos, move, player):
        new_pos = pos.copy()
        my_color = 'w' if player == 'white' else 'b'
        
        # Handle castling
        if move == 'O-O':
            if my_color == 'w':
                new_pos.pop('e1', None)
                new_pos.pop('h1', None)
                new_pos['g1'] = 'wK'
                new_pos['f1'] = 'wR'
            else:
                new_pos.pop('e8', None)
                new_pos.pop('h8', None)
                new_pos['g8'] = 'bK'
                new_pos['f8'] = 'bR'
            return new_pos
        elif move == 'O-O-O':
            if my_color == 'w':
                new_pos.pop('e1', None)
                new_pos.pop('a1', None)
                new_pos['c1'] = 'wK'
                new_pos['d1'] = 'wR'
            else:
                new_pos.pop('e8', None)
                new_pos.pop('a8', None)
                new_pos['c8'] = 'bK'
                new_pos['d8'] = 'bR'
            return new_pos
        
        # Parse move
        piece_type = 'P'
        for pt in ['K', 'Q', 'R', 'B', 'N']:
            if move[0] == pt:
                piece_type = pt
                move = move[1:]
                break
        
        # Find destination square
        dest = None
        promotion = None
        if '=' in move:
            parts = move.split('=')
            move = parts[0]
            promotion = parts[1].replace('+', '').replace('#', '')
        
        move = move.replace('x', '').replace('+', '').replace('#', '')
        
        # Extract destination (last 2 chars that are a square)
        for i in range(len(move) - 1, -1, -1):
            if i + 1 < len(move) and move[i] in 'abcdefgh' and move[i+1] in '12345678':
                dest = move[i:i+2]
                break
        
        if not dest:
            return new_pos
        
        # Find source square
        source = None
        for sq, pc in pos.items():
            if pc[0] == my_color and pc[1] == piece_type:
                # Simple heuristic: check if this piece could move to dest
                if piece_type == 'P':
                    if my_color == 'w':
                        if (sq[0] == dest[0] and int(dest[1]) - int(sq[1]) in [1, 2]) or \
                           (abs(ord(sq[0]) - ord(dest[0])) == 1 and int(dest[1]) - int(sq[1]) == 1):
                            source = sq
                            break
                    else:
                        if (sq[0] == dest[0] and int(sq[1]) - int(dest[1]) in [1, 2]) or \
                           (abs(ord(sq[0]) - ord(dest[0])) == 1 and int(sq[1]) - int(dest[1]) == 1):
                            source = sq
                            break
                else:
                    source = sq
                    break
        
        if source:
            new_pos.pop(source)
            if promotion:
                new_pos[dest] = my_color + promotion
            else:
                new_pos[dest] = my_color + piece_type
        
        return new_pos
    
    # Score each move
    best_moves = []
    best_score = float('-inf')
    
    for move in legal_moves:
        score = 0
        
        # Checkmate is best
        if '#' in move:
            return move
        
        # Checks are good
        if '+' in move:
            score += 50
        
        # Promotions to Queen are great
        if '=Q' in move:
            score += 80
        elif '=' in move:
            score += 70
        
        # Captures
        if 'x' in move:
            score += 30
        
        # Castling is good early
        if move in ['O-O', 'O-O-O']:
            score += 25
        
        # Evaluate position after move
        new_pos = apply_move(pieces, move, to_play)
        pos_score = evaluate_position(new_pos, to_play)
        score += pos_score
        
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    return random.choice(best_moves) if best_moves else legal_moves[0]
