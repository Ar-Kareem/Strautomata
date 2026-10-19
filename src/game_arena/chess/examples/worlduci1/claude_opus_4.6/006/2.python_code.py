
import time
import random

# Piece values
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

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
        0,  0,  0,  0,  0,  0,  0,  0,
    ],
    'N': [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ],
    'B': [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ],
    'R': [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0,
    ],
    'Q': [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20,
    ],
    'K': [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20,
    ],
}

def sq_to_idx(sq):
    return ord(sq[0]) - ord('a'), int(sq[1]) - 1

def idx_to_sq(f, r):
    return chr(f + ord('a')) + str(r + 1)

def in_bounds(f, r):
    return 0 <= f <= 7 and 0 <= r <= 7

def pst_index_white(f, r):
    # PST is stored from rank 8 (top) to rank 1 (bottom) for white
    return (7 - r) * 8 + f

def pst_index_black(f, r):
    return r * 8 + f

class Board:
    def __init__(self, pieces, to_play):
        # board[file][rank] = piece code or None
        self.board = [[None]*8 for _ in range(8)]
        for sq, pc in pieces.items():
            f, r = sq_to_idx(sq)
            self.board[f][r] = pc
        self.to_play = 'w' if to_play == 'white' else 'b'
        self.opponent = 'b' if self.to_play == 'w' else 'w'
        
    def get(self, f, r):
        if not in_bounds(f, r):
            return None
        return self.board[f][r]
    
    def copy(self):
        b = Board.__new__(Board)
        b.board = [row[:] for row in self.board]
        b.to_play = self.to_play
        b.opponent = self.opponent
        return b
    
    def find_king(self, color):
        for f in range(8):
            for r in range(8):
                p = self.board[f][r]
                if p and p[0] == color and p[1] == 'K':
                    return (f, r)
        return None
    
    def is_attacked_by(self, f, r, by_color):
        """Check if square (f,r) is attacked by any piece of by_color."""
        # Knight attacks
        for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nf, nr = f+df, r+dr
            p = self.get(nf, nr)
            if p and p[0] == by_color and p[1] == 'N':
                return True
        
        # King attacks
        for df in [-1,0,1]:
            for dr in [-1,0,1]:
                if df == 0 and dr == 0:
                    continue
                nf, nr = f+df, r+dr
                p = self.get(nf, nr)
                if p and p[0] == by_color and p[1] == 'K':
                    return True
        
        # Pawn attacks
        pawn_dir = 1 if by_color == 'w' else -1
        # Pawn on (f-1, r-pawn_dir) or (f+1, r-pawn_dir) attacks (f,r)
        for df in [-1, 1]:
            nf, nr = f+df, r - pawn_dir
            p = self.get(nf, nr)
            if p and p[0] == by_color and p[1] == 'P':
                return True
        
        # Rook/Queen (straight lines)
        for df, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
            nf, nr = f+df, r+dr
            while in_bounds(nf, nr):
                p = self.board[nf][nr]
                if p:
                    if p[0] == by_color and p[1] in ('R', 'Q'):
                        return True
                    break
                nf += df
                nr += dr
        
        # Bishop/Queen (diagonals)
        for df, dr in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            nf, nr = f+df, r+dr
            while in_bounds(nf, nr):
                p = self.board[nf][nr]
                if p:
                    if p[0] == by_color and p[1] in ('B', 'Q'):
                        return True
                    break
                nf += df
                nr += dr
        
        return False
    
    def in_check(self, color):
        kpos = self.find_king(color)
        if not kpos:
            return True
        opp = 'b' if color == 'w' else 'w'
        return self.is_attacked_by(kpos[0], kpos[1], opp)
    
    def make_move_simple(self, ff, fr, tf, tr, promo=None):
        """Make a move on a copy and return new board."""
        nb = self.copy()
        piece = nb.board[ff][fr]
        nb.board[ff][fr] = None
        
        if promo:
            nb.board[tf][tr] = piece[0] + promo
        else:
            nb.board[tf][tr] = piece
        
        # Castling: move rook too
        if piece and piece[1] == 'K':
            if ff == 4 and tf == 6:  # kingside
                rook = nb.board[7][fr]
                nb.board[7][fr] = None
                nb.board[5][fr] = rook
            elif ff == 4 and tf == 2:  # queenside
                rook = nb.board[0][fr]
                nb.board[0][fr] = None
                nb.board[3][fr] = rook
        
        # En passant capture
        if piece and piece[1] == 'P' and ff != tf and self.board[tf][tr] is None:
            nb.board[tf][fr] = None
        
        # Swap turns
        nb.to_play, nb.opponent = nb.opponent, nb.to_play
        return nb
    
    def gen_pseudo_legal(self, color, ep_target=None):
        """Generate pseudo-legal moves for color. Returns list of (ff, fr, tf, tr, promo)."""
        moves = []
        opp = 'b' if color == 'w' else 'w'
        
        for f in range(8):
            for r in range(8):
                p = self.board[f][r]
                if not p or p[0] != color:
                    continue
                pt = p[1]
                
                if pt == 'P':
                    direction = 1 if color == 'w' else -1
                    start_rank = 1 if color == 'w' else 6
                    promo_rank = 7 if color == 'w' else 0
                    
                    # Forward one
                    nr = r + direction
                    if in_bounds(f, nr) and self.board[f][nr] is None:
                        if nr == promo_rank:
                            for pp in ['Q','R','B','N']:
                                moves.append((f, r, f, nr, pp))
                        else:
                            moves.append((f, r, f, nr, None))
                        # Forward two from start
                        if r == start_rank:
                            nr2 = r + 2*direction
                            if self.board[f][nr2] is None:
                                moves.append((f, r, f, nr2, None))
                    
                    # Captures
                    for df in [-1, 1]:
                        nf = f + df
                        nr = r + direction
                        if not in_bounds(nf, nr):
                            continue
                        target = self.board[nf][nr]
                        if target and target[0] == opp:
                            if nr == promo_rank:
                                for pp in ['Q','R','B','N']:
                                    moves.append((f, r, nf, nr, pp))
                            else:
                                moves.append((f, r, nf, nr, None))
                        # En passant
                        if ep_target and (nf, nr) == ep_target:
                            moves.append((f, r, nf, nr, None))
                
                elif pt == 'N':
                    for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                        nf, nr = f+df, r+dr
                        if not in_bounds(nf, nr):
                            continue
                        target = self.board[nf][nr]
                        if target is None or target[0] == opp:
                            moves.append((f, r, nf, nr, None))
                
                elif pt == 'B':
                    for df, dr in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                        nf, nr = f+df, r+dr
                        while in_bounds(nf, nr):
                            target = self.board[nf][nr]
                            if target is None:
                                moves.append((f, r, nf, nr, None))
                            elif target[0] == opp:
                                moves.append((f, r, nf, nr, None))
                                break
                            else:
                                break
                            nf += df
                            nr += dr
                
                elif pt == 'R':
                    for df, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nf, nr = f+df, r+dr
                        while in_bounds(nf, nr):
                            target = self.board[nf][nr]
                            if target is None:
                                moves.append((f, r, nf, nr, None))
                            elif target[0] == opp:
                                moves.append((f, r, nf, nr, None))
                                break
                            else:
                                break
                            nf += df
                            nr += dr
                
                elif pt == 'Q':
                    for df, dr in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                        nf, nr = f+df, r+dr
                        while in_bounds(nf, nr):
                            target = self.board[nf][nr]
                            if target is None:
                                moves.append((f, r, nf, nr, None))
                            elif target[0] == opp:
                                moves.append((f, r, nf, nr, None))
                                break
                            else:
                                break
                            nf += df
                            nr += dr
                
                elif pt == 'K':
                    for df in [-1,0,1]:
                        for dr in [-1,0,1]:
                            if df == 0 and dr == 0:
                                continue
                            nf, nr = f+df, r+dr
                            if not in_bounds(nf, nr):
                                continue
                            target = self.board[nf][nr]
                            if target is None or target[0] == opp:
                                moves.append((f, r, nf, nr, None))
                    
                    # Castling (simplified - check if king on e file, rook present)
                    base_rank = 0 if color == 'w' else 7
                    if f == 4 and r == base_rank:
                        # Kingside
                        if (self.board[7][base_rank] and self.board[7][base_rank] == color + 'R' and
                            self.board[5][base_rank] is None and self.board[6][base_rank] is None):
                            if (not self.is_attacked_by(4, base_rank, opp) and
                                not self.is_attacked_by(5, base_rank, opp) and
                                not self.is_attacked_by(6, base_rank, opp)):
                                moves.append((4, base_rank, 6, base_rank, None))
                        # Queenside
                        if (self.board[0][base_rank] and self.board[0][base_rank] == color + 'R' and
                            self.board[1][base_rank] is None and self.board[2][base_rank] is None and 
                            self.board[3][base_rank] is None):
                            if (not self.is_attacked_by(4, base_rank, opp) and
                                not self.is_attacked_by(3, base_rank, opp) and
                                not self.is_attacked_by(2, base_rank, opp)):
                                moves.append((4, base_rank, 2, base_rank, None))
        
        return moves
    
    def gen_legal_moves(self, color, ep_target=None):
        pseudo = self.gen_pseudo_legal(color, ep_target)
        legal = []
        for m in pseudo:
            ff, fr, tf, tr, promo = m
            nb = self.make_move_simple(ff, fr, tf, tr, promo)
            if not nb.in_check(color):
                legal.append(m)
        return legal
    
    def move_to_uci(self, m):
        ff, fr, tf, tr, promo = m
        s = idx_to_sq(ff, fr) + idx_to_sq(tf, tr)
        if promo:
            s += promo.lower()
        return s


def evaluate(board):
    """Evaluate from white's perspective."""
    score = 0
    for f in range(8):
        for r in range(8):
            p = board.board[f][r]
            if not p:
                continue
            pt = p[1]
            val = PIECE_VALUES.get(pt, 0)
            if pt in PST:
                if p[0] == 'w':
                    pst_val = PST[pt][pst_index_white(f, r)]
                else:
                    pst_val = PST[pt][pst_index_black(f, r)]
            else:
                pst_val = 0
            
            if p[0] == 'w':
                score += val + pst_val
            else:
                score -= val + pst_val
    
    return score


def move_sort_key(board, m):
    """Sort key for move ordering (higher = search first)."""
    ff, fr, tf, tr, promo = m
    score = 0
    target = board.board[tf][tr]
    piece = board.board[ff][fr]
    
    if target:
        # MVV-LVA
        score += 10 * PIECE_VALUES.get(target[1], 0) - PIECE_VALUES.get(piece[1], 0)
    
    if promo:
        score += PIECE_VALUES.get(promo, 0)
    
    # Pawn capture en passant
    if piece and piece[1] == 'P' and ff != tf and target is None:
        score += 10 * PIECE_VALUES['P']
    
    return score


def quiesce(board, alpha, beta, color_sign, depth_left):
    """Quiescence search - only look at captures."""
    stand_pat = evaluate(board) * color_sign
    if depth_left <= 0:
        return stand_pat
    
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat
    
    moves = board.gen_pseudo_legal(board.to_play)
    # Only captures
    captures = []
    for m in moves:
        ff, fr, tf, tr, promo = m
        target = board.board[tf][tr]
        piece = board.board[ff][fr]
        is_ep = piece and piece[1] == 'P' and ff != tf and target is None
        if target or promo or is_ep:
            captures.append(m)
    
    captures.sort(key=lambda m: move_sort_key(board, m), reverse=True)
    
    for m in captures:
        ff, fr, tf, tr, promo = m
        nb = board.make_move_simple(ff, fr, tf, tr, promo)
        if nb.in_check(board.to_play):
            continue
        score = -quiesce(nb, -beta, -alpha, -color_sign, depth_left - 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    
    return alpha


def alphabeta(board, depth, alpha, beta, color_sign, start_time, time_limit):
    """Alpha-beta search."""
    if time.time() - start_time > time_limit:
        return evaluate(board) * color_sign
    
    if depth <= 0:
        return quiesce(board, alpha, beta, color_sign, 4)
    
    moves = board.gen_legal_moves(board.to_play)
    
    if not moves:
        if board.in_check(board.to_play):
            return -30000 + (10 - depth)  # Checkmate
        return 0  # Stalemate
    
    moves.sort(key=lambda m: move_sort_key(board, m), reverse=True)
    
    for m in moves:
        ff, fr, tf, tr, promo = m
        nb = board.make_move_simple(ff, fr, tf, tr, promo)
        score = -alphabeta(nb, depth - 1, -beta, -alpha, -color_sign, start_time, time_limit)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    
    return alpha


def policy(pieces: dict[str, str], to_play: str) -> str:
    start_time = time.time()
    time_limit = 0.8  # seconds
    
    board = Board(pieces, to_play)
    color = board.to_play
    color_sign = 1 if color == 'w' else -1
    
    legal_moves = board.gen_legal_moves(color)
    
    if not legal_moves:
        # Shouldn't happen if we're called with legal moves available
        # Fallback: try to generate something
        pseudo = board.gen_pseudo_legal(color)
        if pseudo:
            return board.move_to_uci(pseudo[0])
        return "0000"
    
    if len(legal_moves) == 1:
        return board.move_to_uci(legal_moves[0])
    
    # Sort moves for better ordering
    legal_moves.sort(key=lambda m: move_sort_key(board, m), reverse=True)
    
    best_move = legal_moves[0]
    best_score = -999999
    
    # Iterative deepening
    for depth in range(1, 10):
        if time.time() - start_time > time_limit * 0.5:
            break
        
        current_best = legal_moves[0]
        current_best_score = -999999
        alpha = -999999
        beta = 999999
        
        for m in legal_moves:
            if time.time() - start_time > time_limit * 0.7:
                break
            
            ff, fr, tf, tr, promo = m
            nb = board.make_move_simple(ff, fr, tf, tr, promo)
            score = -alphabeta(nb, depth - 1, -beta, -alpha, -color_sign, start_time, time_limit)
            
            if score > current_best_score:
                current_best_score = score
                current_best = m
            if score > alpha:
                alpha = score
        
        if time.time() - start_time <= time_limit * 0.8:
            best_move = current_best
            best_score = current_best_score
            # Reorder moves to put best first
            legal_moves.remove(current_best)
            legal_moves.insert(0, current_best)
        
        if best_score > 25000:  # Found checkmate
            break
    
    return board.move_to_uci(best_move)
