
def policy(pieces: dict[str, str], to_play: str) -> str:
    import random
    
    # Piece values
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece-square tables (simplified)
    PAWN_TABLE = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    KNIGHT_TABLE = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    KING_MIDDLE_TABLE = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
    
    def sq_to_idx(sq):
        return (ord(sq[0]) - ord('a')) + (8 - int(sq[1])) * 8
    
    def get_piece_value(piece_type, sq, color):
        base_value = PIECE_VALUES.get(piece_type, 0)
        idx = sq_to_idx(sq)
        
        if color == 'b':
            idx = 63 - idx
        
        if piece_type == 'P':
            return base_value + PAWN_TABLE[idx]
        elif piece_type == 'N':
            return base_value + KNIGHT_TABLE[idx]
        elif piece_type == 'K':
            return base_value + KING_MIDDLE_TABLE[idx]
        return base_value
    
    def evaluate_position(pieces_dict, color):
        score = 0
        for sq, piece in pieces_dict.items():
            piece_color = 'w' if piece[0] == 'w' else 'b'
            piece_type = piece[1]
            value = get_piece_value(piece_type, sq, piece_color)
            
            if piece_color == color:
                score += value
            else:
                score -= value
        return score
    
    def parse_move(move_str):
        return move_str[:2], move_str[2:4], move_str[4:] if len(move_str) > 4 else None
    
    def apply_move(pieces_dict, move_str):
        new_pieces = pieces_dict.copy()
        from_sq, to_sq, promotion = parse_move(move_str)
        
        piece = new_pieces.get(from_sq)
        if piece:
            del new_pieces[from_sq]
            if promotion:
                new_pieces[to_sq] = piece[0] + promotion.upper()
            else:
                new_pieces[to_sq] = piece
        
        return new_pieces
    
    def get_legal_moves(pieces_dict, color):
        moves = []
        my_color = 'w' if color == 'white' else 'b'
        
        for sq, piece in pieces_dict.items():
            if piece[0] != my_color:
                continue
            
            piece_type = piece[1]
            file_idx = ord(sq[0]) - ord('a')
            rank = int(sq[1])
            
            if piece_type == 'P':
                direction = 1 if my_color == 'w' else -1
                new_rank = rank + direction
                
                if 1 <= new_rank <= 8:
                    new_sq = chr(ord('a') + file_idx) + str(new_rank)
                    if new_sq not in pieces_dict:
                        if new_rank == 8 or new_rank == 1:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append(sq + new_sq + promo)
                        else:
                            moves.append(sq + new_sq)
                    
                    for df in [-1, 1]:
                        if 0 <= file_idx + df <= 7:
                            capture_sq = chr(ord('a') + file_idx + df) + str(new_rank)
                            if capture_sq in pieces_dict and pieces_dict[capture_sq][0] != my_color:
                                if new_rank == 8 or new_rank == 1:
                                    for promo in ['q', 'r', 'b', 'n']:
                                        moves.append(sq + capture_sq + promo)
                                else:
                                    moves.append(sq + capture_sq)
                
                if (my_color == 'w' and rank == 2) or (my_color == 'b' and rank == 7):
                    new_rank = rank + 2 * direction
                    new_sq = chr(ord('a') + file_idx) + str(new_rank)
                    mid_sq = chr(ord('a') + file_idx) + str(rank + direction)
                    if new_sq not in pieces_dict and mid_sq not in pieces_dict:
                        moves.append(sq + new_sq)
            
            elif piece_type == 'N':
                knight_moves = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
                for df, dr in knight_moves:
                    new_file = file_idx + df
                    new_rank = rank + dr
                    if 0 <= new_file <= 7 and 1 <= new_rank <= 8:
                        new_sq = chr(ord('a') + new_file) + str(new_rank)
                        if new_sq not in pieces_dict or pieces_dict[new_sq][0] != my_color:
                            moves.append(sq + new_sq)
            
            elif piece_type in ['B', 'R', 'Q']:
                directions = []
                if piece_type in ['B', 'Q']:
                    directions += [(1,1), (1,-1), (-1,1), (-1,-1)]
                if piece_type in ['R', 'Q']:
                    directions += [(1,0), (-1,0), (0,1), (0,-1)]
                
                for df, dr in directions:
                    for dist in range(1, 8):
                        new_file = file_idx + df * dist
                        new_rank = rank + dr * dist
                        if not (0 <= new_file <= 7 and 1 <= new_rank <= 8):
                            break
                        new_sq = chr(ord('a') + new_file) + str(new_rank)
                        if new_sq in pieces_dict:
                            if pieces_dict[new_sq][0] != my_color:
                                moves.append(sq + new_sq)
                            break
                        moves.append(sq + new_sq)
            
            elif piece_type == 'K':
                for df in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if df == 0 and dr == 0:
                            continue
                        new_file = file_idx + df
                        new_rank = rank + dr
                        if 0 <= new_file <= 7 and 1 <= new_rank <= 8:
                            new_sq = chr(ord('a') + new_file) + str(new_rank)
                            if new_sq not in pieces_dict or pieces_dict[new_sq][0] != my_color:
                                moves.append(sq + new_sq)
        
        return moves
    
    # Get legal moves
    legal_moves = get_legal_moves(pieces, to_play)
    
    if not legal_moves:
        return ""
    
    # Evaluate moves
    best_move = None
    best_score = -999999
    my_color = 'w' if to_play == 'white' else 'b'
    
    for move in legal_moves:
        new_pieces = apply_move(pieces, move)
        
        # Check for captures and promotions
        from_sq, to_sq, promotion = parse_move(move)
        capture_value = 0
        if to_sq in pieces:
            capture_value = PIECE_VALUES.get(pieces[to_sq][1], 0)
        
        promotion_value = 0
        if promotion:
            promotion_value = PIECE_VALUES.get(promotion.upper(), 0) - 100
        
        # Evaluate position after move
        position_score = evaluate_position(new_pieces, my_color)
        
        # Combine scores
        total_score = position_score + capture_value * 1.2 + promotion_value
        
        if total_score > best_score:
            best_score = total_score
            best_move = move
    
    return best_move if best_move else random.choice(legal_moves)
