
import copy

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables (from white's perspective, flip for black)
PST = {
    'P': [0,0,0,0,0,0,0,0, 50,50,50,50,50,50,50,50, 10,10,20,30,30,20,10,10, 5,5,10,25,25,10,5,5, 0,0,0,20,20,0,0,0, 5,-5,-10,0,0,-10,-5,5, 5,10,10,-20,-20,10,10,5, 0,0,0,0,0,0,0,0],
    'N': [-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,0,0,0,-20,-40, -30,0,10,15,15,10,0,-30, -30,5,15,20,20,15,5,-30, -30,0,15,20,20,15,0,-30, -30,5,10,15,15,10,5,-30, -40,-20,0,5,5,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50],
    'B': [-20,-10,-10,-10,-10,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,10,10,5,0,-10, -10,5,5,10,10,5,5,-10, -10,0,10,10,10,10,0,-10, -10,10,10,10,10,10,10,-10, -10,5,0,0,0,0,5,-10, -20,-10,-10,-10,-10,-10,-10,-20],
    'R': [0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0],
    'Q': [-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5, 0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10, -10,0,5,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20],
    'K': [-30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -20,-30,-30,-40,-40,-30,-30,-20, -10,-20,-20,-20,-20,-20,-20,-10, 20,20,0,0,0,0,20,20, 20,30,10,0,0,10,30,20]
}

def sq_to_idx(sq):
    return (ord(sq[0]) - ord('a')) + (int(sq[1]) - 1) * 8

def idx_to_sq(idx):
    return chr(ord('a') + idx % 8) + str(idx // 8 + 1)

def evaluate(pieces, color):
    score = 0
    my_color = 'w' if color == 'white' else 'b'
    for sq, piece in pieces.items():
        pc, pt = piece[0], piece[1]
        val = PIECE_VALUES[pt]
        idx = sq_to_idx(sq)
        if pc == 'w':
            pst_val = PST[pt][idx]
        else:
            pst_val = PST[pt][63 - idx]
        total = val + pst_val
        if pc == my_color:
            score += total
        else:
            score -= total
    return score

def generate_moves(pieces, color):
    moves = []
    my_color = 'w' if color == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    for sq, piece in pieces.items():
        if piece[0] != my_color:
            continue
        pt = piece[1]
        f, r = ord(sq[0]) - ord('a'), int(sq[1]) - 1
        
        if pt == 'P':
            direction = 1 if my_color == 'w' else -1
            start_rank = 1 if my_color == 'w' else 6
            promo_rank = 7 if my_color == 'w' else 0
            
            # Forward
            nr = r + direction
            if 0 <= nr <= 7:
                nsq = chr(ord('a') + f) + str(nr + 1)
                if nsq not in pieces:
                    if nr == promo_rank:
                        for p in ['q', 'r', 'b', 'n']:
                            moves.append(sq + nsq + p)
                    else:
                        moves.append(sq + nsq)
                    # Double push
                    if r == start_rank:
                        nr2 = r + 2 * direction
                        nsq2 = chr(ord('a') + f) + str(nr2 + 1)
                        if nsq2 not in pieces:
                            moves.append(sq + nsq2)
            # Captures
            for df in [-1, 1]:
                nf = f + df
                nr = r + direction
                if 0 <= nf <= 7 and 0 <= nr <= 7:
                    nsq = chr(ord('a') + nf) + str(nr + 1)
                    if nsq in pieces and pieces[nsq][0] == opp_color:
                        if nr == promo_rank:
                            for p in ['q', 'r', 'b', 'n']:
                                moves.append(sq + nsq + p)
                        else:
                            moves.append(sq + nsq)
        
        elif pt == 'N':
            for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nf, nr = f + df, r + dr
                if 0 <= nf <= 7 and 0 <= nr <= 7:
                    nsq = chr(ord('a') + nf) + str(nr + 1)
                    if nsq not in pieces or pieces[nsq][0] == opp_color:
                        moves.append(sq + nsq)
        
        elif pt == 'K':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf <= 7 and 0 <= nr <= 7:
                        nsq = chr(ord('a') + nf) + str(nr + 1)
                        if nsq not in pieces or pieces[nsq][0] == opp_color:
                            moves.append(sq + nsq)
        
        elif pt in ['R', 'Q']:
            for df, dr in [(0,1),(0,-1),(1,0),(-1,0)]:
                nf, nr = f + df, r + dr
                while 0 <= nf <= 7 and 0 <= nr <= 7:
                    nsq = chr(ord('a') + nf) + str(nr + 1)
                    if nsq not in pieces:
                        moves.append(sq + nsq)
                    elif pieces[nsq][0] == opp_color:
                        moves.append(sq + nsq)
                        break
                    else:
                        break
                    nf, nr = nf + df, nr + dr
        
        if pt in ['B', 'Q']:
            for df, dr in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                nf, nr = f + df, r + dr
                while 0 <= nf <= 7 and 0 <= nr <= 7:
                    nsq = chr(ord('a') + nf) + str(nr + 1)
                    if nsq not in pieces:
                        moves.append(sq + nsq)
                    elif pieces[nsq][0] == opp_color:
                        moves.append(sq + nsq)
                        break
                    else:
                        break
                    nf, nr = nf + df, nr + dr
    
    return moves

def make_move(pieces, move):
    new_pieces = dict(pieces)
    fr, to = move[:2], move[2:4]
    piece = new_pieces.pop(fr)
    if len(move) == 5:
        promo = move[4].upper()
        piece = piece[0] + promo
    new_pieces[to] = piece
    return new_pieces

def minimax(pieces, color, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(pieces, color), None
    
    current = color if maximizing else ('black' if color == 'white' else 'white')
    moves = generate_moves(pieces, current)
    
    if not moves:
        return evaluate(pieces, color), None
    
    # Move ordering: captures first
    def move_score(m):
        to = m[2:4]
        if to in pieces:
            return PIECE_VALUES.get(pieces[to][1], 0)
        return 0
    moves.sort(key=move_score, reverse=True)
    
    best_move = moves[0]
    if maximizing:
        max_eval = -100000
        for move in moves:
            new_pieces = make_move(pieces, move)
            eval_score, _ = minimax(new_pieces, color, depth - 1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = 100000
        for move in moves:
            new_pieces = make_move(pieces, move)
            eval_score, _ = minimax(new_pieces, color, depth - 1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(pieces: dict[str, str], to_play: str) -> str:
    moves = generate_moves(pieces, to_play)
    if not moves:
        # Shouldn't happen if called correctly
        return "0000"
    
    _, best_move = minimax(pieces, to_play, 3, -100000, 100000, True)
    return best_move if best_move else moves[0]
