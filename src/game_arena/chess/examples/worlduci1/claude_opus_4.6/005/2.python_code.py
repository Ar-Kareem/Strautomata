
import time
import random

# Piece values
PIECE_VAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables (from white's perspective, rank 0 = rank 1)
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
        -10,  0, 10, 10, 10, 10,  0,-10,
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

def sq2idx(sq):
    return ord(sq[0]) - ord('a'), int(sq[1]) - 1

def idx2sq(f, r):
    return chr(f + ord('a')) + str(r + 1)

def on_board(f, r):
    return 0 <= f <= 7 and 0 <= r <= 7

class ChessState:
    def __init__(self, pieces, to_play, castling=None, ep_square=None):
        # board[file][rank] = piece code or None
        self.board = [[None]*8 for _ in range(8)]
        for sq, pc in pieces.items():
            f, r = sq2idx(sq)
            self.board[f][r] = pc
        self.to_play = to_play  # 'w' or 'b'
        self.ep_square = ep_square  # (file, rank) or None
        if castling is None:
            self.castling = self._infer_castling()
        else:
            self.castling = castling
    
    def _infer_castling(self):
        # Infer castling rights from piece positions
        rights = set()
        # White
        if self.board[4][0] == 'wK':
            if self.board[7][0] == 'wR':
                rights.add('K')
            if self.board[0][0] == 'wR':
                rights.add('Q')
        # Black
        if self.board[4][7] == 'bK':
            if self.board[7][7] == 'bR':
                rights.add('k')
            if self.board[0][7] == 'bR':
                rights.add('q')
        return rights
    
    def copy(self):
        s = ChessState.__new__(ChessState)
        s.board = [row[:] for row in self.board]
        s.to_play = self.to_play
        s.ep_square = self.ep_square
        s.castling = set(self.castling)
        return s
    
    def find_king(self, color):
        for f in range(8):
            for r in range(8):
                if self.board[f][r] == color + 'K':
                    return (f, r)
        return None
    
    def is_attacked_by(self, sq, attacker_color):
        f, r = sq
        ac = attacker_color
        # Knight attacks
        for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nf, nr = f+df, r+dr
            if on_board(nf, nr) and self.board[nf][nr] == ac+'N':
                return True
        # Pawn attacks
        if ac == 'w':
            for df in [-1, 1]:
                nf, nr = f+df, r-1
                if on_board(nf, nr) and self.board[nf][nr] == 'wP':
                    return True
        else:
            for df in [-1, 1]:
                nf, nr = f+df, r+1
                if on_board(nf, nr) and self.board[nf][nr] == 'bP':
                    return True
        # King attacks
        for df in [-1,0,1]:
            for dr in [-1,0,1]:
                if df == 0 and dr == 0:
                    continue
                nf, nr = f+df, r+dr
                if on_board(nf, nr) and self.board[nf][nr] == ac+'K':
                    return True
        # Sliding: rook/queen (straight)
        for df, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
            nf, nr = f+df, r+dr
            while on_board(nf, nr):
                p = self.board[nf][nr]
                if p is not None:
                    if p[0] == ac and p[1] in ('R','Q'):
                        return True
                    break
                nf += df
                nr += dr
        # Sliding: bishop/queen (diagonal)
        for df, dr in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            nf, nr = f+df, r+dr
            while on_board(nf, nr):
                p = self.board[nf][nr]
                if p is not None:
                    if p[0] == ac and p[1] in ('B','Q'):
                        return True
                    break
                nf += df
                nr += dr
        return False
    
    def in_check(self, color):
        kpos = self.find_king(color)
        if kpos is None:
            return True
        opp = 'b' if color == 'w' else 'w'
        return self.is_attacked_by(kpos, opp)
    
    def gen_pseudo_moves(self):
        moves = []
        c = self.to_play
        opp = 'b' if c == 'w' else 'w'
        for f in range(8):
            for r in range(8):
                p = self.board[f][r]
                if p is None or p[0] != c:
                    continue
                pt = p[1]
                if pt == 'P':
                    direction = 1 if c == 'w' else -1
                    start_rank = 1 if c == 'w' else 6
                    promo_rank = 7 if c == 'w' else 0
                    # Forward
                    nr = r + direction
                    if on_board(f, nr) and self.board[f][nr] is None:
                        if nr == promo_rank:
                            for pp in ['q','r','b','n']:
                                moves.append((f,r,f,nr,pp))
                        else:
                            moves.append((f,r,f,nr,None))
                        # Double push
                        if r == start_rank:
                            nr2 = r + 2*direction
                            if self.board[f][nr2] is None:
                                moves.append((f,r,f,nr2,None))
                    # Captures
                    for df in [-1, 1]:
                        nf = f + df
                        if not on_board(nf, nr):
                            continue
                        target = self.board[nf][nr]
                        if target is not None and target[0] == opp:
                            if nr == promo_rank:
                                for pp in ['q','r','b','n']:
                                    moves.append((f,r,nf,nr,pp))
                            else:
                                moves.append((f,r,nf,nr,None))
                        # En passant
                        if self.ep_square is not None and (nf, nr) == self.ep_square:
                            moves.append((f,r,nf,nr,None))
                elif pt == 'N':
                    for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                        nf, nr = f+df, r+dr
                        if on_board(nf, nr):
                            target = self.board[nf][nr]
                            if target is None or target[0] == opp:
                                moves.append((f,r,nf,nr,None))
                elif pt == 'K':
                    for df in [-1,0,1]:
                        for dr in [-1,0,1]:
                            if df == 0 and dr == 0:
                                continue
                            nf, nr = f+df, r+dr
                            if on_board(nf, nr):
                                target = self.board[nf][nr]
                                if target is None or target[0] == opp:
                                    moves.append((f,r,nf,nr,None))
                    # Castling
                    if c == 'w' and f == 4 and r == 0:
                        if 'K' in self.castling and self.board[5][0] is None and self.board[6][0] is None:
                            if not self.is_attacked_by((4,0), opp) and not self.is_attacked_by((5,0), opp) and not self.is_attacked_by((6,0), opp):
                                moves.append((4,0,6,0,None))
                        if 'Q' in self.castling and self.board[3][0] is None and self.board[2][0] is None and self.board[1][0] is None:
                            if not self.is_attacked_by((4,0), opp) and not self.is_attacked_by((3,0), opp) and not self.is_attacked_by((2,0), opp):
                                moves.append((4,0,2,0,None))
                    elif c == 'b' and f == 4 and r == 7:
                        if 'k' in self.castling and self.board[5][7] is None and self.board[6][7] is None:
                            if not self.is_attacked_by((4,7), opp) and not self.is_attacked_by((5,7), opp) and not self.is_attacked_by((6,7), opp):
                                moves.append((4,7,6,7,None))
                        if 'q' in self.castling and self.board[3][7] is None and self.board[2][7] is None and self.board[1][7] is None:
                            if not self.is_attacked_by((4,7), opp) and not self.is_attacked_by((3,7), opp) and not self.is_attacked_by((2,7), opp):
                                moves.append((4,7,2,7,None))
                else:
                    # Sliding pieces
                    if pt in ('R','Q'):
                        dirs = [(1,0),(-1,0),(0,1),(0,-1)]
                    else:
                        dirs = []
                    if pt in ('B','Q'):
                        dirs = dirs + [(1,1),(1,-1),(-1,1),(-1,-1)]
                    for df, dr in dirs:
                        nf, nr = f+df, r+dr
                        while on_board(nf, nr):
                            target = self.board[nf][nr]
                            if target is None:
                                moves.append((f,r,nf,nr,None))
                            elif target[0] == opp:
                                moves.append((f,r,nf,nr,None))
                                break
                            else:
                                break
                            nf += df
                            nr += dr
        return moves
    
    def make_move(self, move):
        ff, fr, tf, tr, promo = move
        s = self.copy()
        p = s.board[ff][fr]
        captured = s.board[tf][tr]
        c = self.to_play
        opp = 'b' if c == 'w' else 'w'
        
        s.ep_square = None
        
        # En passant capture
        if p[1] == 'P' and (tf, tr) == self.ep_square:
            cap_rank = tr - 1 if c == 'w' else tr + 1
            s.board[tf][cap_rank] = None
        
        # Move piece
        s.board[ff][fr] = None
        if promo:
            s.board[tf][tr] = c + promo.upper()
        else:
            s.board[tf][tr] = p
        
        # Double pawn push -> set ep square
        if p[1] == 'P' and abs(tr - fr) == 2:
            ep_r = (fr + tr) // 2
            s.ep_square = (ff, ep_r)
        
        # Castling move rook
        if p[1] == 'K':
            if ff == 4 and tf == 6:  # Kingside
                s.board[5][fr] = s.board[7][fr]
                s.board[7][fr] = None
            elif ff == 4 and tf == 2:  # Queenside
                s.board[3][fr] = s.board[0][fr]
                s.board[0][fr] = None
        
        # Update castling rights
        if p[1] == 'K':
            if c == 'w':
                s.castling.discard('K')
                s.castling.discard('Q')
            else:
                s.castling.discard('k')
                s.castling.discard('q')
        if p[1] == 'R':
            if c == 'w':
                if ff == 0 and fr == 0:
                    s.castling.discard('Q')
                elif ff == 7 and fr == 0:
                    s.castling.discard('K')
            else:
                if ff == 0 and fr == 7:
                    s.castling.discard('q')
                elif ff == 7 and fr == 7:
                    s.castling.discard('k')
        # If rook captured
        if captured:
            if tf == 0 and tr == 0:
                s.castling.discard('Q')
            elif tf == 7 and tr == 0:
                s.castling.discard('K')
            elif tf == 0 and tr == 7:
                s.castling.discard('q')
            elif tf == 7 and tr == 7:
                s.castling.discard('k')
        
        s.to_play = opp
        return s
    
    def gen_legal_moves(self):
        pseudo = self.gen_pseudo_moves()
        legal = []
        c = self.to_play
        for m in pseudo:
            ns = self.make_move(m)
            if not ns.in_check(c):
                legal.append(m)
        return legal
    
    def move_to_uci(self, move):
        ff, fr, tf, tr, promo = move
        s = idx2sq(ff, fr) + idx2sq(tf, tr)
        if promo:
            s += promo
        return s


def evaluate(state):
    """Evaluate position from white's perspective."""
    score = 0
    for f in range(8):
        for r in range(8):
            p = state.board[f][r]
            if p is None:
                continue
            pt = p[1]
            val = PIECE_VAL[pt]
            # PST index: for white, index = (7-r)*8 + f; for black, index = r*8 + f
            if p[0] == 'w':
                pst_idx = (7 - r) * 8 + f
                score += val + PST[pt][pst_idx]
            else:
                pst_idx = r * 8 + f
                score -= val + PST[pt][pst_idx]
    return score


def move_sort_key(state, move):
    """Higher is better for move ordering."""
    ff, fr, tf, tr, promo = move
    score = 0
    captured = state.board[tf][tr]
    if captured:
        # MVV-LVA
        score += 10 * PIECE_VAL[captured[1]] - PIECE_VAL[state.board[ff][fr][1]]
    if promo:
        score += PIECE_VAL[promo.upper()]
    # Center bonus
    if 2 <= tf <= 5 and 2 <= tr <= 5:
        score += 5
    return score


def quiesce(state, alpha, beta, color_sign, depth=0):
    stand_pat = evaluate(state) * color_sign
    if depth >= 6:
        return stand_pat
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat
    
    # Generate captures only
    moves = state.gen_pseudo_moves()
    c = state.to_play
    capture_moves = []
    for m in moves:
        ff, fr, tf, tr, promo = m
        target = state.board[tf][tr]
        is_ep = (state.board[ff][fr] and state.board[ff][fr][1] == 'P' and state.ep_square == (tf, tr))
        if target is not None or is_ep or promo:
            capture_moves.append(m)
    
    capture_moves.sort(key=lambda m: move_sort_key(state, m), reverse=True)
    
    for m in capture_moves:
        ns = state.make_move(m)
        if ns.in_check(c):
            continue
        score = -quiesce(ns, -beta, -alpha, -color_sign, depth + 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def alphabeta(state, depth, alpha, beta, color_sign, start_time, time_limit):
    if time.time() - start_time > time_limit:
        return evaluate(state) * color_sign
    
    if depth <= 0:
        return quiesce(state, alpha, beta, color_sign)
    
    moves = state.gen_legal_moves()
    if len(moves) == 0:
        c = state.to_play
        if state.in_check(c):
            return -30000 + (4 - depth)  # Checkmate
        return 0  # Stalemate
    
    moves.sort(key=lambda m: move_sort_key(state, m), reverse=True)
    
    for m in moves:
        ns = state.make_move(m)
        score = -alphabeta(ns, depth - 1, -beta, -alpha, -color_sign, start_time, time_limit)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def policy(pieces: dict[str, str], to_play: str) -> str:
    start_time = time.time()
    time_limit = 0.85
    
    c = 'w' if to_play == 'white' else 'b'
    color_sign = 1 if c == 'w' else -1
    
    state = ChessState(pieces, c)
    
    legal_moves = state.gen_legal_moves()
    
    if not legal_moves:
        # Shouldn't happen if called correctly, but fallback
        # Generate any pseudo move
        pseudo = state.gen_pseudo_moves()
        if pseudo:
            return state.move_to_uci(pseudo[0])
        return "0000"
    
    if len(legal_moves) == 1:
        return state.move_to_uci(legal_moves[0])
    
    # Sort moves for better pruning
    legal_moves.sort(key=lambda m: move_sort_key(state, m), reverse=True)
    
    best_move = legal_moves[0]
    
    # Iterative deepening
    for depth in range(1, 20):
        if time.time() - start_time > time_limit * 0.5:
            break
        
        best_score = -100000
        best_at_depth = legal_moves[0]
        alpha = -100000
        beta = 100000
        
        for m in legal_moves:
            if time.time() - start_time > time_limit * 0.8:
                break
            ns = state.make_move(m)
            score = -alphabeta(ns, depth - 1, -beta, -alpha, -color_sign, start_time, time_limit)
            if score > best_score:
                best_score = score
                best_at_depth = m
            if score > alpha:
                alpha = score
        
        if time.time() - start_time <= time_limit * 0.8:
            best_move = best_at_depth
            # Reorder: put best move first
            legal_moves.remove(best_move)
            legal_moves.insert(0, best_move)
            
            # If we found checkmate, stop
            if best_score > 25000:
                break
    
    return state.move_to_uci(best_move)
