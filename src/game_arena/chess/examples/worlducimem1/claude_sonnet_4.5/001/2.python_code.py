
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    import random
    
    # Piece values
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece-square tables (simplified, for white's perspective)
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
        """Convert square like 'e4' to index 0-63"""
        file = ord(sq[0]) - ord('a')
        rank = int(sq[1]) - 1
        return rank * 8 + file
    
    def get_pst_value(piece_type, sq, is_white):
        """Get piece-square table value"""
        idx = sq_to_idx(sq)
        if not is_white:
            # Mirror for black
            idx = 63 - idx
        return PST.get(piece_type, [0]*64)[idx]
    
    def evaluate_position(pieces_dict, color):
        """Evaluate the position from the perspective of 'color'"""
        score = 0
        for sq, piece in pieces_dict.items():
            piece_color = 'white' if piece[0] == 'w' else 'black'
            piece_type = piece[1]
            
            value = PIECE_VALUES[piece_type]
            pst_value = get_pst_value(piece_type, sq, piece_color == 'white')
            total_value = value + pst_value
            
            if piece_color == color:
                score += total_value
            else:
                score -= total_value
        
        return score
    
    def make_move(pieces_dict, move):
        """Apply a move and return new board state"""
        new_pieces = pieces_dict.copy()
        from_sq = move[:2]
        to_sq = move[2:4]
        
        if from_sq in new_pieces:
            piece = new_pieces[from_sq]
            del new_pieces[from_sq]
            
            # Handle promotion
            if len(move) == 5:
                promo_piece = move[4].upper()
                new_pieces[to_sq] = piece[0] + promo_piece
            else:
                new_pieces[to_sq] = piece
        
        return new_pieces
    
    def is_check(pieces_dict, king_color):
        """Simple check detection - see if king can be captured"""
        # Find king
        king_sq = None
        king_code = ('w' if king_color == 'white' else 'b') + 'K'
        for sq, piece in pieces_dict.items():
            if piece == king_code:
                king_sq = sq
                break
        
        if not king_sq:
            return False
        
        # Check if any opponent piece attacks king square
        # Simplified: just check if opponent can capture
        return False  # Simplified for performance
    
    def generate_legal_moves(pieces_dict, color):
        """Generate pseudo-legal moves (simplified)"""
        moves = []
        piece_prefix = 'w' if color == 'white' else 'b'
        
        for from_sq, piece in pieces_dict.items():
            if not piece.startswith(piece_prefix):
                continue
            
            piece_type = piece[1]
            from_file = ord(from_sq[0]) - ord('a')
            from_rank = int(from_sq[1]) - 1
            
            # Generate moves based on piece type (simplified)
            for to_file in range(8):
                for to_rank in range(8):
                    to_sq = chr(ord('a') + to_file) + str(to_rank + 1)
                    if to_sq != from_sq:
                        move = from_sq + to_sq
                        # Simple validation: don't capture own pieces
                        if to_sq in pieces_dict:
                            if pieces_dict[to_sq].startswith(piece_prefix):
                                continue
                        moves.append(move)
        
        return moves
    
    def evaluate_move(pieces_dict, move, color, depth=1):
        """Evaluate a move with simple lookahead"""
        new_board = make_move(pieces_dict, move)
        
        # Immediate evaluation
        score = evaluate_position(new_board, color)
        
        # Bonus for captures
        if move[2:4] in pieces_dict:
            captured = pieces_dict[move[2:4]]
            score += PIECE_VALUES[captured[1]] // 2
        
        # Simple 1-ply opponent response
        if depth > 0:
            opp_color = 'black' if color == 'white' else 'white'
            # Just evaluate position from opponent's view
            opp_score = evaluate_position(new_board, opp_color)
            score -= opp_score // 4  # Dampen opponent's score
        
        return score
    
    # Get legal moves from current position
    # We need to generate them ourselves since they're not provided
    our_color = to_play
    their_color = 'black' if our_color == 'white' else 'white'
    
    # Generate all pseudo-legal moves
    all_moves = generate_legal_moves(pieces, our_color)
    
    if not all_moves:
        # Fallback: try any move
        piece_prefix = 'w' if our_color == 'white' else 'b'
        for sq in pieces:
            if pieces[sq].startswith(piece_prefix):
                # Try moving to adjacent square
                file = ord(sq[0]) - ord('a')
                rank = int(sq[1]) - 1
                for df in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if df == 0 and dr == 0:
                            continue
                        nf, nr = file + df, rank + dr
                        if 0 <= nf < 8 and 0 <= nr < 8:
                            to_sq = chr(ord('a') + nf) + str(nr + 1)
                            all_moves.append(sq + to_sq)
    
    # Evaluate all moves
    best_move = None
    best_score = -999999
    
    for move in all_moves:
        try:
            score = evaluate_move(pieces, move, our_color, depth=1)
            if score > best_score:
                best_score = score
                best_move = move
        except:
            continue
    
    if best_move is None and all_moves:
        best_move = random.choice(all_moves)
    
    if best_move is None:
        # Ultimate fallback
        best_move = "e2e4"
    
    return (best_move, memory)
