
def policy(pieces: dict[str, str], to_play: str, legal_moves: list = None) -> str:
    import random
    
    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if color == 'w' else 'w'
    
    # Piece values
    VAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece-square tables (simplified, for white, flip rank for black)
    PST = {
        'P': [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5,  5, 10, 25, 25, 10,  5,  5],
            [0,  0,  0, 20, 20,  0,  0,  0],
            [5, -5,-10,  0,  0,-10, -5,  5],
            [5, 10, 10,-20,-20, 10, 10,  5],
            [0,  0,  0,  0,  0,  0,  0,  0]
        ],
        'N': [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ],
        'B': [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ],
        'R': [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [5, 10, 10, 10, 10, 10, 10,  5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [0,  0,  0,  5,  5,  0,  0,  0]
        ],
        'Q': [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [-5,  0,  5,  5,  5,  5,  0, -5],
            [0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ],
        'K': [
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [20, 20,  0,  0,  0,  0, 20, 20],
            [20, 30, 10,  0,  0, 10, 30, 20]
        ]
    }
    
    def sq_idx(sq):
        return ord(sq[0]) - ord('a'), int(sq[1]) - 1
    
    def idx_sq(f, r):
        return chr(ord('a') + f) + str(r + 1)
    
    def eval_piece(pc, sq):
        f, r = sq_idx(sq)
        if pc[0] == 'b':
            r = 7 - r  # flip for black
        return VAL[pc[1]] + PST[pc[1]][r][f]
    
    def evaluate(pos, col):
        score = 0
        for sq, pc in pos.items():
            v = eval_piece(pc, sq)
            if pc[0] == col:
                score += v
            else:
                score -= v
        return score
    
    def is_attacked(pos, sq, by_col):
        """Check if square sq is attacked by by_col"""
        f, r = sq_idx(sq)
        # Pawns
        if by_col == 'w':
            for df in (-1, 1):
                nf, nr = f + df, r - 1
                if 0 <= nf < 8 and 0 <= nr < 8:
                    pc = pos.get(idx_sq(nf, nr))
                    if pc == 'wP':
                        return True
        else:
            for df in (-1, 1):
                nf, nr = f + df, r + 1
                if 0 <= nf < 8 and 0 <= nr < 8:
                    pc = pos.get(idx_sq(nf, nr))
                    if pc == 'bP':
                        return True
        # Knights
        for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                pc = pos.get(idx_sq(nf, nr))
                if pc and pc[0] == by_col and pc[1] == 'N':
                    return True
        # King
        for df in (-1,0,1):
            for dr in (-1,0,1):
                if df == 0 and dr == 0:
                    continue
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    pc = pos.get(idx_sq(nf, nr))
                    if pc and pc[0] == by_col and pc[1] == 'K':
                        return True
        # Rays (Bishop, Rook, Queen)
        directions = [
            ((-1,-1),(-1,1),(1,-1),(1,1)),  # Bishop
            ((-1,0),(1,0),(0,-1),(0,1))     # Rook
        ]
        for i, dirs in enumerate(directions):
            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    pc = pos.get(idx_sq(nf, nr))
                    if pc:
                        if pc[0] == by_col and (pc[1] == 'Q' or (i == 0 and pc[1] == 'B') or (i == 1 and pc[1] == 'R')):
                            return True
                        break
                    nf += df
                    nr += dr
        return False
    
    def find_king(pos, col):
        for sq, pc in pos.items():
            if pc == col + 'K':
                return sq
        return None
    
    def is_check(pos, col):
        ksq = find_king(pos, col)
        if not ksq:
            return False
        return is_attacked(pos, ksq, 'b' if col == 'w' else 'w')
    
    def apply_move(pos, move, col):
        """Return new position dict after move"""
        new_pos = dict(pos)
        src = move[:2]
        dst = move[2:4]
        piece = new_pos.pop(src)
        
        # En passant capture
        if piece[1] == 'P' and src[0] != dst[0] and dst not in pos:
            ep_sq = dst[0] + str(int(dst[1]) - 1 if col == 'w' else int(dst[1]) + 1)
            if ep_sq in new_pos:
                del new_pos[ep_sq]
        
        # Normal capture (remove dst if exists)
        if dst in new_pos:
            del new_pos[dst]
        
        # Promotion
        if len(move) == 5:
            piece = col + move[4].upper()
        
        # Castling: move rook
        if piece[1] == 'K' and abs(ord(src[0]) - ord(dst[0])) == 2:
            if dst[0] == 'g':  # kingside
                r_src = 'h' + src[1]
                r_dst = 'f' + src[1]
            else:  # queenside
                r_src = 'a' + src[1]
                r_dst = 'd' + src[1]
            if r_src in new_pos:
                new_pos[r_dst] = new_pos.pop(r_src)
        
        new_pos[dst] = piece
        return new_pos
    
    def generate_legal_moves(pos, col):
        """Fallback move generator"""
        moves = []
        opp = 'b' if col == 'w' else 'w'
        
        for sq, pc in pos.items():
            if pc[0] != col:
                continue
            f, r = sq_idx(sq)
            ptype = pc[1]
            
            if ptype == 'P':
                direction = 1 if col == 'w' else -1
                start_rank = 1 if col == 'w' else 6
                # Forward 1
                nr = r + direction
                if 0 <= nr < 8:
                    dst = idx_sq(f, nr)
                    if dst not in pos:
                        # Promotion?
                        if nr == 7 or nr == 0:
                            for promo in 'qrbn':
                                moves.append(sq + dst + promo)
                        else:
                            moves.append(sq + dst)
                        # Forward 2
                        if r == start_rank:
                            nr2 = r + 2*direction
                            dst2 = idx_sq(f, nr2)
                            if dst2 not in pos:
                                moves.append(sq + dst2)
                # Captures
                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        dst = idx_sq(nf, nr)
                        if dst in pos and pos[dst][0] == opp:
                            if nr == 7 or nr == 0:
                                for promo in 'qrbn':
                                    moves.append(sq + dst + promo)
                            else:
                                moves.append(sq + dst)
                        # En passant (simplified: if empty and on rank 3/4)
                        elif dst not in pos and (r == 3 or r == 4):
                            # Check if opponent pawn just moved here (approximate)
                            ep_sq = idx_sq(nf, r)
                            if ep_sq in pos and pos[ep_sq] == opp + 'P':
                                moves.append(sq + dst)
            
            elif ptype == 'N':
                for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        dst = idx_sq(nf, nr)
                        if dst not in pos or pos[dst][0] != col:
                            moves.append(sq + dst)
            
            elif ptype == 'K':
                for df in (-1,0,1):
                    for dr in (-1,0,1):
                        if df == 0 and dr == 0:
                            continue
                        nf, nr = f + df, r + dr
                        if 0 <= nf < 8 and 0 <= nr < 8:
                            dst = idx_sq(nf, nr)
                            if dst not in pos or pos[dst][0] != col:
                                moves.append(sq + dst)
                # Castling (simplified: check if squares empty and not attacked)
                if not is_check(pos, col):
                    # Kingside
                    if col == 'w' and sq == 'e1' and 'h1' in pos and pos['h1'] == 'wR':
                        if 'f1' not in pos and 'g1' not in pos:
                            if not is_attacked(pos, 'f1', opp) and not is_attacked(pos, 'g1', opp):
                                moves.append('e1g1')
                    elif col == 'b' and sq == 'e8' and 'h8' in pos and pos['h8'] == 'bR':
                        if 'f8' not in pos and 'g8' not in pos:
                            if not is_attacked(pos, 'f8', opp) and not is_attacked(pos, 'g8', opp):
                                moves.append('e8g8')
                    # Queenside
                    if col == 'w' and sq == 'e1' and 'a1' in pos and pos['a1'] == 'wR':
                        if 'b1' not in pos and 'c1' not in pos and 'd1' not in pos:
                            if not is_attacked(pos, 'd1', opp) and not is_attacked(pos, 'c1', opp):
                                moves.append('e1c1')
                    elif col == 'b' and sq == 'e8' and 'a8' in pos and pos['a8'] == 'bR':
                        if 'b8' not in pos and 'c8' not in pos and 'd8' not in pos:
                            if not is_attacked(pos, 'd8', opp) and not is_attacked(pos, 'c8', opp):
                                moves.append('e8c8')
            
            elif ptype in ('B', 'R', 'Q'):
                dirs = []
                if ptype in ('B', 'Q'):
                    dirs.extend([(-1,-1),(-1,1),(1,-1),(1,1)])
                if ptype in ('R', 'Q'):
                    dirs.extend([(-1,0),(1,0),(0,-1),(0,1)])
                for df, dr in dirs:
                    nf, nr = f + df, r + dr
                    while 0 <= nf < 8 and 0 <= nr < 8:
                        dst = idx_sq(nf, nr)
                        if dst not in pos:
                            moves.append(sq + dst)
                        else:
                            if pos[dst][0] != col:
                                moves.append(sq + dst)
                            break
                        nf += df
                        nr += dr
        
        # Filter illegal moves (that leave king in check)
        legal = []
        for mv in moves:
            new_pos = apply_move(pos, mv, col)
            if not is_check(new_pos, col):
                legal.append(mv)
        return legal
    
    # Use provided legal_moves or generate
    if legal_moves is None:
        legal_moves = generate_legal_moves(pieces, color)
    
    if not legal_moves:
        return "e2e4"  # Should not happen
    
    best_score = -99999999
    candidates = []
    
    for move in legal_moves:
        new_pos = apply_move(pieces, move, color)
        
        # Base evaluation
        score = evaluate(new_pos, color)
        
        # Check bonus
        if is_check(new_pos, opp_color):
            score += 500
            # Checkmate test (simplified: if opponent has no moves)
            opp_moves = generate_legal_moves(new_pos, opp_color)
            if not opp_moves:
                return move  # Immediate mate
        
        # Capture bonus (MVV-LVA)
        dst = move[2:4]
        if dst in pieces and pieces[dst][0] != color:
            victim = pieces[dst][1]
            attacker = pieces[move[:2]][1]
            score += 10 * VAL[victim] - VAL[attacker]
        
        if score > best_score:
            best_score = score
            candidates = [move]
        elif score == best_score:
            candidates.append(move)
    
    return random.choice(candidates)
