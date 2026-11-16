
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    import re
    
    # Piece values
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    # Check for immediate checkmate
    for move in legal_moves:
        if '#' in move:
            return (move, memory)
    
    # Piece-square tables (from white's perspective, flip for black)
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
    
    def sq_to_idx(sq, color):
        f = ord(sq[0]) - ord('a')
        r = int(sq[1]) - 1
        if color == 'w':
            return (7 - r) * 8 + f
        else:
            return r * 8 + f
    
    def get_pst_value(piece_type, sq, color):
        if piece_type not in PST:
            return 0
        return PST[piece_type][sq_to_idx(sq, color)]
    
    def parse_move(move):
        # Returns (piece_type, dest_square, is_capture, promotion, is_castling)
        if move == 'O-O' or move == 'O-O+' or move == 'O-O#':
            return ('K', None, False, None, 'kingside')
        if move == 'O-O-O' or move == 'O-O-O+' or move == 'O-O-O#':
            return ('K', None, False, None, 'queenside')
        
        clean = move.replace('+', '').replace('#', '')
        is_capture = 'x' in clean
        clean = clean.replace('x', '')
        
        promotion = None
        if '=' in clean:
            promotion = clean[-1]
            clean = clean[:-2]
        
        if clean[0].isupper():
            piece = clean[0]
            dest = clean[-2:]
        else:
            piece = 'P'
            dest = clean[-2:]
        
        return (piece, dest, is_capture, promotion, None)
    
    def find_captured_piece(dest):
        if dest in pieces:
            return pieces[dest][1]
        return None
    
    def evaluate_move(move):
        score = 0
        piece, dest, is_capture, promotion, castling = parse_move(move)
        
        # Castling bonus
        if castling:
            score += 60
            return score
        
        # Check bonus
        if '+' in move:
            score += 30
        
        # Capture evaluation (MVV-LVA)
        if is_capture and dest:
            captured = find_captured_piece(dest)
            if captured:
                score += PIECE_VALUES.get(captured, 0) * 10 - PIECE_VALUES.get(piece, 0)
        
        # Promotion bonus
        if promotion:
            score += PIECE_VALUES.get(promotion, 0) - 100
        
        # Positional evaluation
        if dest:
            score += get_pst_value(piece if not promotion else promotion, dest, my_color)
        
        # Bonus for controlling center
        if dest in ['d4', 'd5', 'e4', 'e5']:
            score += 15
        elif dest in ['c3', 'c4', 'c5', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f4', 'f5', 'f6']:
            score += 5
        
        return score
    
    # Evaluate all moves and pick the best
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return (best_move, memory)
