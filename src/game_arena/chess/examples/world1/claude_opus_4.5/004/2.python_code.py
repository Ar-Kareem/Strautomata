
import time

# Piece values
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

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

def sq_to_idx(sq, is_white):
    file = ord(sq[0]) - ord('a')
    rank = int(sq[1]) - 1
    if is_white:
        return (7 - rank) * 8 + file
    else:
        return rank * 8 + file

def evaluate(pieces, to_play):
    score = 0
    my_color = 'w' if to_play == 'white' else 'b'
    
    for sq, piece in pieces.items():
        color = piece[0]
        ptype = piece[1]
        value = PIECE_VALUES.get(ptype, 0)
        is_white = (color == 'w')
        pst_bonus = PST.get(ptype, [0]*64)[sq_to_idx(sq, is_white)]
        
        total = value + pst_bonus
        if color == my_color:
            score += total
        else:
            score -= total
    
    return score

def order_moves(moves):
    def score(m):
        s = 0
        if '#' in m:
            s += 10000
        if '+' in m:
            s += 100
        if 'x' in m:
            s += 50
        if '=' in m:
            s += 80
        if 'O-O' in m:
            s += 30
        return s
    return sorted(moves, key=score, reverse=True)

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    if not legal_moves:
        return ""
    
    # Quick check for checkmate
    for m in legal_moves:
        if '#' in m:
            return m
    
    # Simple heuristic scoring for moves
    ordered = order_moves(legal_moves)
    
    # Score moves based on simple heuristics
    best_move = ordered[0]
    best_score = -float('inf')
    
    for move in ordered:
        score = 0
        
        # Checkmate
        if '#' in move:
            return move
        
        # Check
        if '+' in move:
            score += 50
        
        # Captures - try to estimate value
        if 'x' in move:
            score += 30
            # Try to identify captured piece type from destination
            # Higher priority for queen/rook captures
            if 'xQ' in move or move.endswith('Q'):
                score += 100
        
        # Promotions
        if '=Q' in move:
            score += 80
        elif '=' in move:
            score += 40
        
        # Castling is generally good
        if move == 'O-O' or move == 'O-O-O':
            score += 40
        
        # Center pawn moves
        if move in ['e4', 'd4', 'e5', 'd5']:
            score += 20
        
        # Knight/Bishop development
        if move[0] == 'N' or move[0] == 'B':
            score += 10
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
