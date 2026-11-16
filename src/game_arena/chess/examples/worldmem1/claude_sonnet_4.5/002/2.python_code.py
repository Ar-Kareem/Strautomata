
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    import random
    
    # Piece values
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece-square tables (simplified, for white perspective)
    PST_PAWN = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    PST_KNIGHT = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    PST_BISHOP = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    
    PST_ROOK = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ]
    
    PST_QUEEN = [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]
    
    PST_KING = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
    
    PST = {'P': PST_PAWN, 'N': PST_KNIGHT, 'B': PST_BISHOP, 'R': PST_ROOK, 'Q': PST_QUEEN, 'K': PST_KING}
    
    def square_to_index(square, color):
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        if color == 'w':
            return rank * 8 + file
        else:
            return (7 - rank) * 8 + file
    
    def evaluate_position(pieces_dict, color):
        score = 0
        for square, piece in pieces_dict.items():
            piece_color = piece[0]
            piece_type = piece[1]
            value = PIECE_VALUES[piece_type]
            pst_value = PST[piece_type][square_to_index(square, piece_color)]
            total = value + pst_value
            if piece_color == color:
                score += total
            else:
                score -= total
        return score
    
    def parse_move(move_str):
        # Extract destination square from move string
        move_str = move_str.replace('+', '').replace('#', '').replace('x', '')
        
        if move_str in ['O-O', 'O-O-O']:
            return None, None
        
        # Handle promotion
        if '=' in move_str:
            move_str = move_str.split('=')[0]
        
        # Last 2 chars are usually destination
        if len(move_str) >= 2:
            dest = move_str[-2:]
            if dest[0] in 'abcdefgh' and dest[1] in '12345678':
                return None, dest
        
        return None, None
    
    def apply_move(pieces_dict, move_str, color):
        # Simplified move application (not perfect but works for evaluation)
        new_pieces = pieces_dict.copy()
        
        # Handle castling
        if move_str == 'O-O':
            if color == 'w':
                if 'e1' in new_pieces:
                    del new_pieces['e1']
                    new_pieces['g1'] = 'wK'
                if 'h1' in new_pieces:
                    del new_pieces['h1']
                    new_pieces['f1'] = 'wR'
            else:
                if 'e8' in new_pieces:
                    del new_pieces['e8']
                    new_pieces['g8'] = 'bK'
                if 'h8' in new_pieces:
                    del new_pieces['h8']
                    new_pieces['f8'] = 'bR'
            return new_pieces
        
        if move_str == 'O-O-O':
            if color == 'w':
                if 'e1' in new_pieces:
                    del new_pieces['e1']
                    new_pieces['c1'] = 'wK'
                if 'a1' in new_pieces:
                    del new_pieces['a1']
                    new_pieces['d1'] = 'wR'
            else:
                if 'e8' in new_pieces:
                    del new_pieces['e8']
                    new_pieces['c8'] = 'bK'
                if 'a8' in new_pieces:
                    del new_pieces['a8']
                    new_pieces['d8'] = 'bR'
            return new_pieces
        
        _, dest = parse_move(move_str)
        if dest is None:
            return new_pieces
        
        # Find source piece
        color_prefix = 'w' if color == 'white' else 'b'
        piece_type = 'P'
        
        if move_str[0] in 'KQRBN':
            piece_type = move_str[0]
        
        # Remove captured piece
        if dest in new_pieces:
            del new_pieces[dest]
        
        # Move piece (simplified - find any matching piece)
        for sq, pc in list(new_pieces.items()):
            if pc == color_prefix + piece_type:
                del new_pieces[sq]
                new_pieces[dest] = color_prefix + piece_type
                break
        
        return new_pieces
    
    def score_move(move_str, pieces_dict, color):
        score = 0
        
        # Prioritize checkmate
        if '#' in move_str:
            return 1000000
        
        # Prioritize checks
        if '+' in move_str:
            score += 50
        
        # Prioritize captures
        if 'x' in move_str:
            _, dest = parse_move(move_str)
            if dest and dest in pieces_dict:
                captured_piece = pieces_dict[dest][1]
                score += PIECE_VALUES.get(captured_piece, 0) / 10
        
        # Prioritize castling early
        if move_str in ['O-O', 'O-O-O']:
            score += 30
        
        # Evaluate resulting position
        color_char = 'w' if color == 'white' else 'b'
        new_pieces = apply_move(pieces_dict, move_str, color_char)
        position_score = evaluate_position(new_pieces, color_char)
        score += position_score / 100
        
        return score
    
    # Score all moves
    move_scores = []
    my_color = 'w' if to_play == 'white' else 'b'
    
    for move in legal_moves:
        sc = score_move(move, pieces, my_color)
        move_scores.append((move, sc))
    
    # Sort by score
    move_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return best move
    best_move = move_scores[0][0]
    
    return (best_move, memory)
