
import copy

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables for positional evaluation (from white's perspective)
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
    return (ord(sq[0]) - ord('a'), int(sq[1]) - 1)

def idx_to_sq(f, r):
    return chr(ord('a') + f) + str(r + 1)

def pst_index(f, r, is_white):
    if is_white:
        return (7 - r) * 8 + f
    else:
        return r * 8 + f

def evaluate(pieces, my_color):
    score = 0
    my_prefix = 'w' if my_color == 'white' else 'b'
    opp_prefix = 'b' if my_color == 'white' else 'w'
    
    for sq, piece in pieces.items():
        color = piece[0]
        ptype = piece[1]
        f, r = sq_to_idx(sq)
        val = PIECE_VALUES.get(ptype, 0)
        pst_val = PST.get(ptype, [0]*64)[pst_index(f, r, color == 'w')]
        
        if color == my_prefix:
            score += val + pst_val
        else:
            score -= val + pst_val
    return score

def generate_moves(pieces, color):
    moves = []
    prefix = 'w' if color == 'white' else 'b'
    opp_prefix = 'b' if color == 'white' else 'w'
    pawn_dir = 1 if prefix == 'w' else -1
    start_rank = 1 if prefix == 'w' else 6
    promo_rank = 7 if prefix == 'w' else 0
    
    for sq, piece in pieces.items():
        if piece[0] != prefix:
            continue
        ptype = piece[1]
        f, r = sq_to_idx(sq)
        
        if ptype == 'P':
            # Forward
            nf, nr = f, r + pawn_dir
            if 0 <= nr <= 7:
                nsq = idx_to_sq(nf, nr)
                if nsq not in pieces:
                    if nr == promo_rank:
                        for p in 'qrbn':
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
                nf, nr = f + df, r + pawn_dir
                if 0 <= nf <= 7 and 0 <= nr <= 7:
                    nsq = idx_to_sq(nf, nr)
                    if nsq in pieces and pieces[nsq][0] == opp_prefix:
                        if nr == promo_rank:
                            for p in 'qrbn':
                                moves.append(sq + nsq + p)
                        else:
                            moves.append(sq + nsq)
        
        elif ptype == 'N':
            for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nf, nr = f + df, r + dr
                if 0 <= nf <= 7 and 0 <= nr <= 7:
                    nsq = idx_to_sq(nf, nr)
                    if nsq not in pieces or pieces[nsq][0] == opp_prefix:
                        moves.append(sq + nsq)
        
        elif ptype == 'B':
            for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                for i in range(1, 8):
                    nf, nr = f + df*i, r + dr*i
                    if not (0 <= nf <= 7 and 0 <= nr <= 7):
                        break
                    nsq = idx_to_sq(nf, nr)
                    if nsq in pieces:
                        if pieces[nsq][0] == opp_prefix:
                            moves.append(sq + nsq)
                        break
                    moves.append(sq + nsq)
        
        elif ptype == 'R':
            for df, dr in [(-1,0),(1,0),(0,-1),(0,1)]:
                for i in range(1, 8):
                    nf, nr = f + df*i, r + dr*i
                    if not (0 <= nf <= 7 and 0 <= nr <= 7):
                        break
                    nsq = idx_to_sq(nf, nr)
                    if nsq in pieces:
                        if pieces[nsq][0] == opp_prefix:
                            moves.append(sq + nsq)
                        break
                    moves.append(sq + nsq)
        
        elif ptype == 'Q':
            for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]:
                for i in range(1, 8):
                    nf, nr = f + df*i, r + dr*i
                    if not (0 <= nf <= 7 and 0 <= nr <= 7):
                        break
                    nsq = idx_to_sq(nf, nr)
                    if nsq in pieces:
                        if pieces[nsq][0] == opp_prefix:
                            moves.append(sq + nsq)
                        break
                    moves.append(sq + nsq)
        
        elif ptype == 'K':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf <= 7 and 0 <= nr <= 7:
                        nsq = idx_to_sq(nf, nr)
                        if nsq not in pieces or pieces[nsq][0] == opp_prefix:
                            moves.append(sq + nsq)
    
    return moves

def make_move(pieces, move):
    new_pieces = dict(pieces)
    src = move[:2]
    dst = move[2:4]
    promo = move[4] if len(move) > 4 else None
    
    piece = new_pieces.pop(src, None)
    if piece is None:
        return new_pieces
    
    if dst in new_pieces:
        del new_pieces[dst]
    
    if promo:
        new_pieces[dst] = piece[0] + promo.upper()
    else:
        new_pieces[dst] = piece
    
    return new_pieces

def minimax(pieces, depth, alpha, beta, maximizing, my_color):
    if depth == 0:
        return evaluate(pieces, my_color), None
    
    current_color = my_color if maximizing else ('black' if my_color == 'white' else 'white')
    moves = generate_moves(pieces, current_color)
    
    if not moves:
        return evaluate(pieces, my_color), None
    
    # Move ordering: captures first
    opp_prefix = 'b' if current_color == 'white' else 'w'
    captures = [m for m in moves if m[2:4] in pieces and pieces[m[2:4]][0] == opp_prefix]
    non_captures = [m for m in moves if m not in captures]
    moves = captures + non_captures
    
    best_move = moves[0] if moves else None
    
    if maximizing:
        max_eval = -999999
        for move in moves:
            new_pieces = make_move(pieces, move)
            eval_score, _ = minimax(new_pieces, depth - 1, alpha, beta, False, my_color)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = 999999
        for move in moves:
            new_pieces = make_move(pieces, move)
            eval_score, _ = minimax(new_pieces, depth - 1, alpha, beta, True, my_color)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(pieces: dict[str, str], to_play: str) -> str:
    my_moves = generate_moves(pieces, to_play)
    
    if not my_moves:
        return "0000"
    
    # Try depth 3 search
    _, best_move = minimax(pieces, 3, -999999, 999999, True, to_play)
    
    if best_move and best_move in my_moves:
        return best_move
    
    # Fallback: return first legal move
    return my_moves[0]
