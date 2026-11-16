
import copy

def policy(pieces: dict[str, str], to_play: str) -> str:
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    PIECE_VALUES = {'K': 20000, 'Q': 900, 'R': 500, 'B': 330, 'N': 320, 'P': 100}
    
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
    
    def sq_to_idx(sq):
        f = ord(sq[0]) - ord('a')
        r = int(sq[1]) - 1
        return r * 8 + f
    
    def get_pst_value(piece_type, sq, color):
        idx = sq_to_idx(sq)
        if color == 'b':
            idx = 63 - idx
        if piece_type == 'P':
            return PST_PAWN[63 - idx]
        elif piece_type == 'N':
            return PST_KNIGHT[63 - idx]
        elif piece_type == 'B':
            return PST_BISHOP[63 - idx]
        return 0
    
    def evaluate(pieces_state, color):
        score = 0
        for sq, piece in pieces_state.items():
            pc, pt = piece[0], piece[1]
            val = PIECE_VALUES.get(pt, 0) + get_pst_value(pt, sq, pc)
            if pc == color:
                score += val
            else:
                score -= val
        return score
    
    def generate_moves(pieces_state, color):
        moves = []
        opp = 'b' if color == 'w' else 'w'
        
        for sq, piece in pieces_state.items():
            if piece[0] != color:
                continue
            pt = piece[1]
            f, r = ord(sq[0]) - ord('a'), int(sq[1]) - 1
            
            if pt == 'P':
                dir = 1 if color == 'w' else -1
                start_rank = 1 if color == 'w' else 6
                promo_rank = 7 if color == 'w' else 0
                
                # Forward
                nr = r + dir
                if 0 <= nr <= 7:
                    nsq = chr(ord('a') + f) + str(nr + 1)
                    if nsq not in pieces_state:
                        if nr == promo_rank:
                            for p in 'qrbn':
                                moves.append(sq + nsq + p)
                        else:
                            moves.append(sq + nsq)
                        # Double push
                        if r == start_rank:
                            nr2 = r + 2 * dir
                            nsq2 = chr(ord('a') + f) + str(nr2 + 1)
                            if nsq2 not in pieces_state:
                                moves.append(sq + nsq2)
                # Captures
                for df in [-1, 1]:
                    nf = f + df
                    if 0 <= nf <= 7 and 0 <= nr <= 7:
                        nsq = chr(ord('a') + nf) + str(nr + 1)
                        if nsq in pieces_state and pieces_state[nsq][0] == opp:
                            if nr == promo_rank:
                                for p in 'qrbn':
                                    moves.append(sq + nsq + p)
                            else:
                                moves.append(sq + nsq)
            
            elif pt == 'N':
                for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    nf, nr = f + df, r + dr
                    if 0 <= nf <= 7 and 0 <= nr <= 7:
                        nsq = chr(ord('a') + nf) + str(nr + 1)
                        if nsq not in pieces_state or pieces_state[nsq][0] == opp:
                            moves.append(sq + nsq)
            
            elif pt == 'K':
                for df in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if df == 0 and dr == 0:
                            continue
                        nf, nr = f + df, r + dr
                        if 0 <= nf <= 7 and 0 <= nr <= 7:
                            nsq = chr(ord('a') + nf) + str(nr + 1)
                            if nsq not in pieces_state or pieces_state[nsq][0] == opp:
                                moves.append(sq + nsq)
            
            elif pt in 'RBQ':
                dirs = []
                if pt in 'RQ':
                    dirs += [(0,1),(0,-1),(1,0),(-1,0)]
                if pt in 'BQ':
                    dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
                for df, dr in dirs:
                    nf, nr = f + df, r + dr
                    while 0 <= nf <= 7 and 0 <= nr <= 7:
                        nsq = chr(ord('a') + nf) + str(nr + 1)
                        if nsq in pieces_state:
                            if pieces_state[nsq][0] == opp:
                                moves.append(sq + nsq)
                            break
                        moves.append(sq + nsq)
                        nf, nr = nf + df, nr + dr
        return moves
    
    def apply_move(pieces_state, move):
        new_pieces = dict(pieces_state)
        fr, to = move[:2], move[2:4]
        piece = new_pieces.pop(fr)
        if len(move) == 5:
            piece = piece[0] + move[4].upper()
        new_pieces[to] = piece
        return new_pieces
    
    def minimax(pieces_state, depth, alpha, beta, maximizing, color):
        opp = 'b' if color == 'w' else 'w'
        
        if depth == 0:
            return evaluate(pieces_state, my_color), None
        
        current = color if maximizing else opp
        moves = generate_moves(pieces_state, current)
        
        if not moves:
            return evaluate(pieces_state, my_color), None
        
        # Move ordering: captures first
        def move_score(m):
            to = m[2:4]
            if to in pieces_state:
                return PIECE_VALUES.get(pieces_state[to][1], 0)
            return 0
        moves.sort(key=move_score, reverse=True)
        
        best_move = moves[0]
        if maximizing:
            max_eval = -100000
            for move in moves:
                new_state = apply_move(pieces_state, move)
                eval_score, _ = minimax(new_state, depth - 1, alpha, beta, False, color)
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
                new_state = apply_move(pieces_state, move)
                eval_score, _ = minimax(new_state, depth - 1, alpha, beta, True, color)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    legal_moves = generate_moves(pieces, my_color)
    
    if not legal_moves:
        return ""
    
    _, best_move = minimax(pieces, 3, -100000, 100000, True, my_color)
    
    if best_move and best_move in legal_moves:
        return best_move
    return legal_moves[0]
