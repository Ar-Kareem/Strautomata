
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    import re
    
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece-square tables (from white's perspective, flip for black)
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
    
    PST_KING_MID = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
    
    PST = {'P': PST_PAWN, 'N': PST_KNIGHT, 'B': PST_BISHOP, 'R': PST_ROOK, 'Q': PST_QUEEN, 'K': PST_KING_MID}
    
    def sq_to_idx(sq):
        f = ord(sq[0]) - ord('a')
        r = int(sq[1]) - 1
        return r * 8 + f
    
    def evaluate(pieces_dict, color):
        score = 0
        my_color = 'w' if color == 'white' else 'b'
        for sq, piece in pieces_dict.items():
            pc, pt = piece[0], piece[1]
            val = PIECE_VALUES.get(pt, 0)
            idx = sq_to_idx(sq)
            if pc == 'w':
                pst_idx = (7 - (idx // 8)) * 8 + (idx % 8)
            else:
                pst_idx = idx
            pst_val = PST.get(pt, [0]*64)[pst_idx]
            total = val + pst_val
            if pc == my_color:
                score += total
            else:
                score -= total
        return score
    
    def order_moves(moves):
        def score(m):
            s = 0
            if '#' in m: s += 10000
            if '+' in m: s += 500
            if 'x' in m: s += 300
            if '=' in m: s += 800
            if m in ('O-O', 'O-O-O'): s += 50
            return -s
        return sorted(moves, key=score)
    
    # Simple move ordering for best move selection
    ordered = order_moves(legal_moves)
    
    # Check for immediate checkmate
    for m in ordered:
        if '#' in m:
            return (m, memory)
    
    # If only one legal move, return it
    if len(legal_moves) == 1:
        return (legal_moves[0], memory)
    
    # Simple heuristic scoring
    def score_move(move):
        s = 0
        if '#' in move: return 100000
        if '+' in move: s += 50
        if 'x' in move: s += 30
        if '=Q' in move: s += 80
        if '=R' in move: s += 40
        if move in ('O-O', 'O-O-O'): s += 25
        # Center control bonus
        if 'e4' in move or 'd4' in move or 'e5' in move or 'd5' in move:
            s += 15
        # Development bonus for knights and bishops early
        if move[0] in 'NB' and not 'x' in move:
            s += 10
        return s
    
    best_move = ordered[0]
    best_score = -float('inf')
    
    for move in ordered:
        sc = score_move(move)
        if sc > best_score:
            best_score = sc
            best_move = move
    
    return (best_move, memory)
