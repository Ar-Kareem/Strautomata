
import copy

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

def evaluate(pieces, color):
    my_color = 'w' if color == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    score = 0
    for sq, piece in pieces.items():
        pc, pt = piece[0], piece[1]
        val = PIECE_VALUES[pt] + PST[pt][pst_index(sq, pc)]
        if pc == my_color:
            score += val
        else:
            score -= val
    return score

def generate_moves(pieces, color):
    my_color = 'w' if color == 'white' else 'b'
    moves = []
    
    for sq, piece in pieces.items():
        if piece[0] != my_color:
            continue
        pt = piece[1]
        f, r = sq_to_idx(sq)
        
        if pt == 'P':
            direction = 1 if my_color == 'w' else -1
            start_rank = 1 if my_color == 'w' else 6
            promo_rank = 7 if my_color == 'w' else 0
            
            # Forward move
            nr = r + direction
            if 0 <= nr <= 7:
                dest = idx_to_sq(f, nr)
                if dest not in pieces:
                    if nr == promo_rank:
                        for p in ['q', 'r', 'b', 'n']:
                            moves.append(sq + dest + p)
                    else:
                        moves.append(sq + dest)
                    # Double move
                    if r == start_rank:
                        nr2 = r + 2 * direction
                        dest2 = idx_to_sq(f, nr2)
                        if dest2 not in pieces:
                            moves.append(sq + dest2)
            
            # Captures
            for df in [-1, 1]:
                nf = f + df
                nr = r + direction
                if 0 <= nf <= 7 and 0 <= nr <= 7:
                    dest = idx_to_sq(nf, nr)
                    if dest in pieces and pieces[dest][0] != my_color:
                        if nr == promo_rank:
                            for p in ['q', 'r', 'b', 'n']:
                                moves.append(sq + dest + p)
                        else:
                            moves.append(sq + dest)
        
        elif pt == 'N':
            for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nf, nr = f + df, r + dr
                if 0 <= nf <= 7 and 0 <= nr <= 7:
                    dest = idx_to_sq(nf, nr)
                    if dest not in pieces or pieces[dest][0] != my_color:
                        moves.append(sq + dest)
        
        elif pt == 'B':
            for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                for i in range(1, 8):
                    nf, nr = f + df*i, r + dr*i
                    if not (0 <= nf <= 7 and 0 <= nr <= 7):
                        break
                    dest = idx_to_sq(nf, nr)
                    if dest in pieces:
                        if pieces[dest][0] != my_color:
                            moves.append(sq + dest)
                        break
                    moves.append(sq + dest)
        
        elif pt == 'R':
            for df, dr in [(-1,0),(1,0),(0,-1),(0,1)]:
                for i in range(1, 8):
                    nf, nr = f + df*i, r + dr*i
                    if not (0 <= nf <= 7 and 0 <= nr <= 7):
                        break
                    dest = idx_to_sq(nf, nr)
                    if dest in pieces:
                        if pieces[dest][0] != my_color:
                            moves.append(sq + dest)
                        break
                    moves.append(sq + dest)
        
        elif pt == 'Q':
            for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]:
                for i in range(1, 8):
                    nf, nr = f + df*i, r + dr*i
                    if not (0 <= nf <= 7 and 0 <= nr <= 7):
                        break
                    dest = idx_to_sq(nf, nr)
                    if dest in pieces:
                        if pieces[dest][0] != my_color:
                            moves.append(sq + dest)
                        break
                    moves.append(sq + dest)
        
        elif pt == 'K':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf <= 7 and 0 <= nr <= 7:
                        dest = idx_to_sq(nf, nr)
                        if dest not in pieces or pieces[dest][0] != my_color:
                            moves.append(sq + dest)
    
    return moves

def is_attacked(pieces, sq, by_color):
    f, r = sq_to_idx(sq)
    
    # Knight attacks
    for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nf, nr = f + df, r + dr
        if 0 <= nf <= 7 and 0 <= nr <= 7:
            dest = idx_to_sq(nf, nr)
            if dest in pieces and pieces[dest] == by_color + 'N':
                return True
    
    # King attacks
    for df in [-1, 0, 1]:
        for dr in [-1, 0, 1]:
            if df == 0 and dr == 0:
                continue
            nf, nr = f + df, r + dr
            if 0 <= nf <= 7 and 0 <= nr <= 7:
                dest = idx_to_sq(nf, nr)
                if dest in pieces and pieces[dest] == by_color + 'K':
                    return True
    
    # Pawn attacks
    pawn_dir = -1 if by_color == 'w' else 1
    for df in [-1, 1]:
        nf, nr = f + df, r + pawn_dir
        if 0 <= nf <= 7 and 0 <= nr <= 7:
            dest = idx_to_sq(nf, nr)
            if dest in pieces and pieces[dest] == by_color + 'P':
                return True
    
    # Sliding pieces
    for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        for i in range(1, 8):
            nf, nr = f + df*i, r + dr*i
            if not (0 <= nf <= 7 and 0 <= nr <= 7):
                break
            dest = idx_to_sq(nf, nr)
            if dest in pieces:
                if pieces[dest] in [by_color + 'B', by_color + 'Q']:
                    return True
                break
    
    for df, dr in [(-1,0),(1,0),(0,-1),(0,1)]:
        for i in range(1, 8):
            nf, nr = f + df*i, r + dr*i
            if not (0 <= nf <= 7 and 0 <= nr <= 7):
                break
            dest = idx_to_sq(nf, nr)
            if dest in pieces:
                if pieces[dest] in [by_color + 'R', by_color + 'Q']:
                    return True
                break
    
    return False

def make_move(pieces, move):
    new_pieces = dict(pieces)
    src, dst = move[:2], move[2:4]
    piece = new_pieces.pop(src)
    if len(move) == 5:
        piece = piece[0] + move[4].upper()
    new_pieces[dst] = piece
    return new_pieces

def is_legal(pieces, move, color):
    my_color = 'w' if color == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    new_pieces = make_move(pieces, move)
    king_sq = None
    for sq, p in new_pieces.items():
        if p == my_color + 'K':
            king_sq = sq
            break
    if king_sq is None:
        return False
    return not is_attacked(new_pieces, king_sq, opp_color)

def minimax(pieces, color, depth, alpha, beta, maximizing):
    opp = 'black' if color == 'white' else 'white'
    
    if depth == 0:
        return evaluate(pieces, color if maximizing else opp), None
    
    moves = generate_moves(pieces, color if maximizing else opp)
    legal = [m for m in moves if is_legal(pieces, m, color if maximizing else opp)]
    
    if not legal:
        return evaluate(pieces, color if maximizing else opp), None
    
    # Move ordering
    def score_move(m):
        dst = m[2:4]
        if dst in pieces:
            return PIECE_VALUES.get(pieces[dst][1], 0)
        return 0
    legal.sort(key=score_move, reverse=True)
    
    best_move = legal[0]
    if maximizing:
        max_eval = -999999
        for m in legal:
            new_pieces = make_move(pieces, m)
            eval_score, _ = minimax(new_pieces, color, depth-1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = m
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = 999999
        for m in legal:
            new_pieces = make_move(pieces, m)
            eval_score, _ = minimax(new_pieces, color, depth-1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = m
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(pieces: dict[str, str], to_play: str) -> str:
    moves = generate_moves(pieces, to_play)
    legal = [m for m in moves if is_legal(pieces, m, to_play)]
    
    if not legal:
        return moves[0] if moves else "e2e4"
    
    _, best = minimax(pieces, to_play, 3, -999999, 999999, True)
    return best if best else legal[0]
