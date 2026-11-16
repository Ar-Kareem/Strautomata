
import time

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    start_time = time.time()
    max_time = 0.8  # Leave buffer for safety
    
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece-square tables (from white's perspective, flip for black)
    pst = {
        'P': [0,0,0,0,0,0,0,0, 5,10,10,-20,-20,10,10,5, 5,-5,-10,0,0,-10,-5,5,
              0,0,0,20,20,0,0,0, 5,5,10,25,25,10,5,5, 10,10,20,30,30,20,10,10,
              50,50,50,50,50,50,50,50, 0,0,0,0,0,0,0,0],
        'N': [-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,5,5,0,-20,-40,
              -30,5,10,15,15,10,5,-30, -30,0,15,20,20,15,0,-30,
              -30,5,15,20,20,15,5,-30, -30,0,10,15,15,10,0,-30,
              -40,-20,0,0,0,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50],
        'B': [-20,-10,-10,-10,-10,-10,-10,-20, -10,5,0,0,0,0,5,-10,
              -10,10,10,10,10,10,10,-10, -10,0,10,10,10,10,0,-10,
              -10,5,5,10,10,5,5,-10, -10,0,5,10,10,5,0,-10,
              -10,0,0,0,0,0,0,-10, -20,-10,-10,-10,-10,-10,-10,-20],
        'R': [0,0,0,5,5,0,0,0, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
              -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
              5,10,10,10,10,10,10,5, 0,0,0,0,0,0,0,0],
        'Q': [-20,-10,-10,-5,-5,-10,-10,-20, -10,0,5,0,0,0,0,-10,
              -10,5,5,5,5,5,0,-10, 0,0,5,5,5,5,0,-5,
              -5,0,5,5,5,5,0,-5, -10,0,5,5,5,5,0,-10,
              -10,0,0,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20],
        'K': [20,30,10,0,0,10,30,20, 20,20,0,0,0,0,20,20,
              -10,-20,-20,-20,-20,-20,-20,-10, -20,-30,-30,-40,-40,-30,-30,-20,
              -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30,
              -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30]
    }
    
    def sq_to_idx(sq):
        return (ord(sq[0]) - ord('a')) + (int(sq[1]) - 1) * 8
    
    def evaluate(pcs):
        score = 0
        for sq, piece in pcs.items():
            color, ptype = piece[0], piece[1]
            val = piece_values[ptype]
            idx = sq_to_idx(sq)
            if color == 'b':
                idx = (7 - idx // 8) * 8 + (idx % 8)
            pos_bonus = pst[ptype][idx] if ptype in pst else 0
            total = val + pos_bonus
            if color == my_color:
                score += total
            else:
                score -= total
        return score
    
    def get_legal_moves(pcs, color):
        moves = []
        opp = 'b' if color == 'w' else 'w'
        
        for sq, piece in pcs.items():
            if piece[0] != color:
                continue
            ptype = piece[1]
            f, r = ord(sq[0]) - ord('a'), int(sq[1]) - 1
            
            def add_move(nf, nr, promo=None):
                if 0 <= nf < 8 and 0 <= nr < 8:
                    nsq = chr(ord('a') + nf) + str(nr + 1)
                    if nsq not in pcs or pcs[nsq][0] == opp:
                        mv = sq + nsq + (promo if promo else '')
                        moves.append(mv)
            
            if ptype == 'P':
                direction = 1 if color == 'w' else -1
                start_rank = 1 if color == 'w' else 6
                promo_rank = 7 if color == 'w' else 0
                
                nsq = chr(ord('a') + f) + str(r + direction + 1)
                if nsq not in pcs:
                    if r + direction == promo_rank:
                        for p in ['q', 'r', 'b', 'n']:
                            moves.append(sq + nsq + p)
                    else:
                        moves.append(sq + nsq)
                        if r == start_rank:
                            nsq2 = chr(ord('a') + f) + str(r + 2*direction + 1)
                            if nsq2 not in pcs:
                                moves.append(sq + nsq2)
                
                for df in [-1, 1]:
                    if 0 <= f + df < 8 and 0 <= r + direction < 8:
                        csq = chr(ord('a') + f + df) + str(r + direction + 1)
                        if csq in pcs and pcs[csq][0] == opp:
                            if r + direction == promo_rank:
                                for p in ['q', 'r', 'b', 'n']:
                                    moves.append(sq + csq + p)
                            else:
                                moves.append(sq + csq)
            
            elif ptype == 'N':
                for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    add_move(f+df, r+dr)
            
            elif ptype == 'K':
                for df in [-1,0,1]:
                    for dr in [-1,0,1]:
                        if df != 0 or dr != 0:
                            add_move(f+df, r+dr)
            
            elif ptype in ['R', 'Q']:
                for df, dr in [(0,1),(0,-1),(1,0),(-1,0)]:
                    for i in range(1, 8):
                        nf, nr = f + df*i, r + dr*i
                        if 0 <= nf < 8 and 0 <= nr < 8:
                            nsq = chr(ord('a') + nf) + str(nr + 1)
                            if nsq not in pcs:
                                moves.append(sq + nsq)
                            elif pcs[nsq][0] == opp:
                                moves.append(sq + nsq)
                                break
                            else:
                                break
                        else:
                            break
            
            if ptype in ['B', 'Q']:
                for df, dr in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                    for i in range(1, 8):
                        nf, nr = f + df*i, r + dr*i
                        if 0 <= nf < 8 and 0 <= nr < 8:
                            nsq = chr(ord('a') + nf) + str(nr + 1)
                            if nsq not in pcs:
                                moves.append(sq + nsq)
                            elif pcs[nsq][0] == opp:
                                moves.append(sq + nsq)
                                break
                            else:
                                break
                        else:
                            break
        
        return moves
    
    def make_move(pcs, move):
        new_pcs = pcs.copy()
        fr, to = move[:2], move[2:4]
        piece = new_pcs.pop(fr)
        if len(move) == 5:
            piece = piece[0] + move[4].upper()
        new_pcs[to] = piece
        return new_pcs
    
    def minimax(pcs, depth, alpha, beta, maximizing, color):
        if time.time() - start_time > max_time:
            return evaluate(pcs), None
        
        moves = get_legal_moves(pcs, color)
        if not moves or depth == 0:
            return evaluate(pcs), None
        
        # Order moves: captures first
        def move_score(m):
            to_sq = m[2:4]
            if to_sq in pcs:
                return piece_values.get(pcs[to_sq][1], 0)
            return 0
        moves.sort(key=move_score, reverse=True)
        
        best_move = moves[0]
        opp = 'b' if color == 'w' else 'w'
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                new_pcs = make_move(pcs, move)
                eval_score, _ = minimax(new_pcs, depth-1, alpha, beta, False, opp)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                new_pcs = make_move(pcs, move)
                eval_score, _ = minimax(new_pcs, depth-1, alpha, beta, True, opp)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    legal_moves = get_legal_moves(pieces, my_color)
    if not legal_moves:
        return "0000", memory
    
    best_move = legal_moves[0]
    
    for depth in range(1, 6):
        if time.time() - start_time > max_time * 0.7:
            break
        _, move = minimax(pieces, depth, -float('inf'), float('inf'), True, my_color)
        if move and move in legal_moves:
            best_move = move
    
    if best_move not in legal_moves:
        best_move = legal_moves[0]
    
    return best_move, memory
