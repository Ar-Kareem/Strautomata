
def policy(pieces: dict[str, str], to_play: str) -> str:
    import random
    
    # Piece values
    PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Piece-square tables (from white's perspective)
    PST = {
        'P': [
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ],
        'N': [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ],
        'B': [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ],
        'R': [
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10, 10, 10, 10, 10,  5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            0,  0,  0,  5,  5,  0,  0,  0
        ],
        'Q': [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -5,  0,  5,  5,  5,  5,  0, -5,
            0,  0,  5,  5,  5,  5,  0, -5,
            -10,  5,  5,  5,  5,  5,  0,-10,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20
        ],
        'K': [
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            20, 20,  0,  0,  0,  0, 20, 20,
            20, 30, 10,  0,  0, 10, 30, 20
        ]
    }
    
    def sq_to_idx(sq):
        file = ord(sq[0]) - ord('a')
        rank = int(sq[1]) - 1
        return rank * 8 + file
    
    def idx_to_sq(idx):
        rank = idx // 8
        file = idx % 8
        return chr(ord('a') + file) + str(rank + 1)
    
    def get_pst_value(piece_type, sq, is_white):
        idx = sq_to_idx(sq)
        if not is_white:
            # Mirror for black
            idx = 63 - idx
        return PST.get(piece_type, [0]*64)[idx] / 100.0
    
    def evaluate_position(pieces_dict):
        score = 0
        for sq, piece in pieces_dict.items():
            color = piece[0]
            piece_type = piece[1]
            value = PIECE_VALUES[piece_type]
            pst_bonus = get_pst_value(piece_type, sq, color == 'w')
            
            if color == 'w':
                score += value + pst_bonus
            else:
                score -= value + pst_bonus
        
        return score
    
    def generate_legal_moves(pieces_dict, color):
        moves = []
        color_prefix = 'w' if color == 'white' else 'b'
        
        for sq, piece in pieces_dict.items():
            if piece[0] != color_prefix[0]:
                continue
            
            piece_type = piece[1]
            from_idx = sq_to_idx(sq)
            from_file = ord(sq[0]) - ord('a')
            from_rank = int(sq[1]) - 1
            
            if piece_type == 'P':
                direction = 1 if color_prefix == 'w' else -1
                start_rank = 1 if color_prefix == 'w' else 6
                promo_rank = 7 if color_prefix == 'w' else 0
                
                # Forward
                new_rank = from_rank + direction
                if 0 <= new_rank <= 7:
                    to_sq = chr(ord('a') + from_file) + str(new_rank + 1)
                    if to_sq not in pieces_dict:
                        if new_rank == promo_rank:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append(sq + to_sq + promo)
                        else:
                            moves.append(sq + to_sq)
                        
                        # Double push
                        if from_rank == start_rank:
                            new_rank2 = from_rank + 2 * direction
                            to_sq2 = chr(ord('a') + from_file) + str(new_rank2 + 1)
                            if to_sq2 not in pieces_dict:
                                moves.append(sq + to_sq2)
                
                # Captures
                for df in [-1, 1]:
                    new_file = from_file + df
                    new_rank = from_rank + direction
                    if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                        to_sq = chr(ord('a') + new_file) + str(new_rank + 1)
                        if to_sq in pieces_dict and pieces_dict[to_sq][0] != color_prefix[0]:
                            if new_rank == promo_rank:
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(sq + to_sq + promo)
                            else:
                                moves.append(sq + to_sq)
            
            elif piece_type == 'N':
                deltas = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
                for df, dr in deltas:
                    new_file = from_file + df
                    new_rank = from_rank + dr
                    if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                        to_sq = chr(ord('a') + new_file) + str(new_rank + 1)
                        if to_sq not in pieces_dict or pieces_dict[to_sq][0] != color_prefix[0]:
                            moves.append(sq + to_sq)
            
            elif piece_type in ['B', 'R', 'Q']:
                if piece_type == 'B':
                    directions = [(-1,-1),(-1,1),(1,-1),(1,1)]
                elif piece_type == 'R':
                    directions = [(-1,0),(1,0),(0,-1),(0,1)]
                else:  # Queen
                    directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
                
                for df, dr in directions:
                    for dist in range(1, 8):
                        new_file = from_file + df * dist
                        new_rank = from_rank + dr * dist
                        if not (0 <= new_file <= 7 and 0 <= new_rank <= 7):
                            break
                        to_sq = chr(ord('a') + new_file) + str(new_rank + 1)
                        if to_sq in pieces_dict:
                            if pieces_dict[to_sq][0] != color_prefix[0]:
                                moves.append(sq + to_sq)
                            break
                        moves.append(sq + to_sq)
            
            elif piece_type == 'K':
                for df in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if df == 0 and dr == 0:
                            continue
                        new_file = from_file + df
                        new_rank = from_rank + dr
                        if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                            to_sq = chr(ord('a') + new_file) + str(new_rank + 1)
                            if to_sq not in pieces_dict or pieces_dict[to_sq][0] != color_prefix[0]:
                                moves.append(sq + to_sq)
                
                # Castling (simple version)
                if color_prefix == 'w' and sq == 'e1':
                    if 'h1' in pieces_dict and pieces_dict['h1'] == 'wR':
                        if 'f1' not in pieces_dict and 'g1' not in pieces_dict:
                            moves.append('e1g1')
                    if 'a1' in pieces_dict and pieces_dict['a1'] == 'wR':
                        if 'b1' not in pieces_dict and 'c1' not in pieces_dict and 'd1' not in pieces_dict:
                            moves.append('e1c1')
                elif color_prefix == 'b' and sq == 'e8':
                    if 'h8' in pieces_dict and pieces_dict['h8'] == 'bR':
                        if 'f8' not in pieces_dict and 'g8' not in pieces_dict:
                            moves.append('e8g8')
                    if 'a8' in pieces_dict and pieces_dict['a8'] == 'bR':
                        if 'b8' not in pieces_dict and 'c8' not in pieces_dict and 'd8' not in pieces_dict:
                            moves.append('e8c8')
        
        return moves
    
    def apply_move(pieces_dict, move):
        new_pieces = pieces_dict.copy()
        from_sq = move[:2]
        to_sq = move[2:4]
        piece = new_pieces[from_sq]
        
        del new_pieces[from_sq]
        
        # Handle promotion
        if len(move) == 5:
            promo_piece = move[4].upper()
            new_pieces[to_sq] = piece[0] + promo_piece
        else:
            new_pieces[to_sq] = piece
        
        # Handle castling
        if piece[1] == 'K' and abs(ord(from_sq[0]) - ord(to_sq[0])) == 2:
            if to_sq == 'g1':
                new_pieces['f1'] = new_pieces['h1']
                del new_pieces['h1']
            elif to_sq == 'c1':
                new_pieces['d1'] = new_pieces['a1']
                del new_pieces['a1']
            elif to_sq == 'g8':
                new_pieces['f8'] = new_pieces['h8']
                del new_pieces['h8']
            elif to_sq == 'c8':
                new_pieces['d8'] = new_pieces['a8']
                del new_pieces['a8']
        
        return new_pieces
    
    # Generate legal moves
    legal_moves = generate_legal_moves(pieces, to_play)
    
    if not legal_moves:
        return ""
    
    # Evaluate each move
    best_move = None
    best_score = float('-inf') if to_play == 'white' else float('inf')
    
    for move in legal_moves:
        new_pieces = apply_move(pieces, move)
        score = evaluate_position(new_pieces)
        
        # Add bonuses for tactical considerations
        if len(move) == 5:  # Promotion
            score += 8 if to_play == 'white' else -8
        
        to_sq = move[2:4]
        if to_sq in pieces:  # Capture
            captured = pieces[to_sq][1]
            score += PIECE_VALUES[captured] * 0.1 * (1 if to_play == 'white' else -1)
        
        if to_play == 'white':
            if score > best_score:
                best_score = score
                best_move = move
        else:
            if score < best_score:
                best_score = score
                best_move = move
    
    return best_move if best_move else random.choice(legal_moves)
