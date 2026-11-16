
import copy

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

def sq_to_idx(sq):
    return (ord(sq[0]) - ord('a'), int(sq[1]) - 1)

def idx_to_sq(f, r):
    return chr(ord('a') + f) + str(r + 1)

def pst_index(sq, color):
    f, r = sq_to_idx(sq)
    if color == 'w':
        return (7 - r) * 8 + f
    else:
        return r * 8 + f

def evaluate(pieces, to_play):
    score = 0
    my_color = 'w' if to_play == 'white' else 'b'
    
    for sq, piece in pieces.items():
        color, ptype = piece[0], piece[1]
        val = PIECE_VALUES.get(ptype, 0)
        pst_val = PST.get(ptype, [0]*64)[pst_index(sq, color)]
        total = val + pst_val
        if color == my_color:
            score += total
        else:
            score -= total
    return score

def is_attacked(pieces, sq, by_color):
    f, r = sq_to_idx(sq)
    
    # Pawn attacks
    pawn_dir = -1 if by_color == 'w' else 1
    for df in [-1, 1]:
        nf, nr = f + df, r + pawn_dir
        if 0 <= nf < 8 and 0 <= nr < 8:
            nsq = idx_to_sq(nf, nr)
            if nsq in pieces and pieces[nsq] == by_color + 'P':
                return True
    
    # Knight attacks
    for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            nsq = idx_to_sq(nf, nr)
            if nsq in pieces and pieces[nsq] == by_color + 'N':
                return True
    
    # King attacks
    for df in [-1, 0, 1]:
        for dr in [-1, 0, 1]:
            if df == 0 and dr == 0:
                continue
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                nsq = idx_to_sq(nf, nr)
                if nsq in pieces and pieces[nsq] == by_color + 'K':
                    return True
    
    # Sliding pieces (Rook, Queen - straight lines)
    for df, dr in [(0,1),(0,-1),(1,0),(-1,0)]:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            nsq = idx_to_sq(nf, nr)
            if nsq in pieces:
                if pieces[nsq] in [by_color + 'R', by_color + 'Q']:
                    return True
                break
            nf, nr = nf + df, nr + dr
    
    # Sliding pieces (Bishop, Queen - diagonals)
    for df, dr in [(1,1),(1,-1),(-1,1),(-1,-1)]:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            nsq = idx_to_sq(nf, nr)
            if nsq in pieces:
                if pieces[nsq] in [by_color + 'B', by_color + 'Q']:
                    return True
                break
            nf, nr = nf + df, nr + dr
    
    return False

def find_king(pieces, color):
    for sq, piece in pieces.items():
        if piece == color + 'K':
            return sq
    return None

def in_check(pieces, color):
    king_sq = find_king(pieces, color)
    if not king_sq:
        return True
    opp = 'b' if color == 'w' else 'w'
    return is_attacked(pieces, king_sq, opp)

def generate_pseudo_moves(pieces, color):
    moves = []
    opp = 'b' if color == 'w' else 'w'
    pawn_dir = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promo_rank = 7 if color == 'w' else 0
    
    for sq, piece in pieces.items():
        if piece[0] != color:
            continue
        ptype = piece[1]
        f, r = sq_to_idx(sq)
        
        if ptype == 'P':
            # Forward
            nf, nr = f, r + pawn_dir
            if 0 <= nr < 8:
                nsq = idx_to_sq(nf, nr)
                if nsq not in pieces:
                    if nr == promo_rank:
                        for p in ['q', 'r', 'b', 'n']:
                            moves.append(sq + nsq + p)
                    else:
                        moves.append(sq + nsq)
                    # Double push
                    if r == start_rank:
                        nr2 = r + 2 * pawn_dir
                        nsq2 = idx_to_sq(f, nr2)
                        if nsq2 not in pieces:
                            moves.append(sq + nsq2)
            # Captures
            for df in [-1, 1]:
                nf2, nr2 = f + df, r + pawn_dir
                if 0 <= nf2 < 8 and 0 <= nr2 < 8:
                    nsq = idx_to_sq(nf2, nr2)
                    if nsq in pieces and pieces[nsq][0] == opp:
                        if nr2 == promo_rank:
                            for p in ['q', 'r', 'b', 'n']:
                                moves.append(sq + nsq + p)
                        else:
                            moves.append(sq + nsq)
        
        elif ptype == 'N':
            for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    nsq = idx_to_sq(nf, nr)
                    if nsq not in pieces or pieces[nsq][0] == opp:
                        moves.append(sq + nsq)
        
        elif ptype == 'K':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        nsq = idx_to_sq(nf, nr)
                        if nsq not in pieces or pieces[nsq][0] == opp:
                            moves.append(sq + nsq)
        
        elif ptype in ['R', 'Q']:
            for df, dr in [(0,1),(0,-1),(1,0),(-1,0)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    nsq = idx_to_sq(nf, nr)
                    if nsq not in pieces:
                        moves.append(sq + nsq)
                    elif pieces[nsq][0] == opp:
                        moves.append(sq + nsq)
                        break
                    else:
                        break
                    nf, nr = nf + df, nr + dr
        
        if ptype in ['B', 'Q']:
            for df, dr in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    nsq = idx_to_sq(nf, nr)
                    if nsq not in pieces:
                        moves.append(sq + nsq)
                    elif pieces[nsq][0] == opp:
                        moves.append(sq + nsq)
                        break
                    else:
                        break
                    nf, nr = nf + df, nr + dr
    
    return moves

def make_move(pieces, move):
    new_pieces = dict(pieces)
    src, dst = move[:2], move[2:4]
    piece = new_pieces.pop(src, None)
    if piece:
        if len(move) == 5:
            color = piece[0]
            piece = color + move[4].upper()
        if dst in new_pieces:
            del new_pieces[dst]
        new_pieces[dst] = piece
    return new_pieces

def generate_legal_moves(pieces, color):
    pseudo = generate_pseudo_moves(pieces, color)
    legal = []
    for move in pseudo:
        new_pieces = make_move(pieces, move)
        if not in_check(new_pieces, color):
            legal.append(move)
    return legal

def minimax(pieces, depth, alpha, beta, maximizing, my_color):
    opp_color = 'b' if my_color == 'w' else 'w'
    current_color = my_color if maximizing else opp_color
    to_play = 'white' if current_color == 'w' else 'black'
    
    moves = generate_legal_moves(pieces, current_color)
    
    if depth == 0 or not moves:
        if not moves:
            if in_check(pieces, current_color):
                return -100000 if maximizing else 100000
            return 0
        return evaluate(pieces, 'white' if my_color == 'w' else 'black')
    
    if maximizing:
        max_eval = -float('inf')
        for move in moves:
            new_pieces = make_move(pieces, move)
            ev = minimax(new_pieces, depth - 1, alpha, beta, False, my_color)
            max_eval = max(max_eval, ev)
            alpha = max(alpha, ev)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_pieces = make_move(pieces, move)
            ev = minimax(new_pieces, depth - 1, alpha, beta, True, my_color)
            min_eval = min(min_eval, ev)
            beta = min(beta, ev)
            if beta <= alpha:
                break
        return min_eval

def policy(pieces: dict[str, str], to_play: str) -> str:
    my_color = 'w' if to_play == 'white' else 'b'
    legal_moves = generate_legal_moves(pieces, my_color)
    
    if not legal_moves:
        return "0000"
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    depth = 3
    if len(pieces) <= 10:
        depth = 4
    
    for move in legal_moves:
        new_pieces = make_move(pieces, move)
        score = minimax(new_pieces, depth - 1, -float('inf'), float('inf'), False, my_color)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
