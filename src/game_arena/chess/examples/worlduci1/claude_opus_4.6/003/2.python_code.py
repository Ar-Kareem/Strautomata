
import time
import random

# Piece values
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables (from white's perspective, index 0 = a1)
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
    ],
    'K_end': [
        -50,-40,-30,-20,-20,-30,-40,-50,
        -30,-20,-10,  0,  0,-10,-20,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-30,  0,  0,  0,  0,-30,-30,
        -50,-30,-30,-30,-30,-30,-30,-50
    ]
}

FILES = 'abcdefgh'
RANKS = '12345678'

def sq_to_idx(sq):
    """Convert algebraic notation to (file, rank) indices (0-7)."""
    return FILES.index(sq[0]), int(sq[1]) - 1

def idx_to_sq(f, r):
    """Convert (file, rank) indices to algebraic notation."""
    return FILES[f] + RANKS[r]

def pst_index_white(f, r):
    """PST index for white (rank 0 = row 7 in table, rank 7 = row 0)."""
    return (7 - r) * 8 + f

def pst_index_black(f, r):
    """PST index for black (mirror vertically)."""
    return r * 8 + f

class Board:
    def __init__(self, pieces, to_play):
        self.board = {}  # (f, r) -> (color, piece_type)
        for sq, pc in pieces.items():
            f, r = sq_to_idx(sq)
            self.board[(f, r)] = (pc[0], pc[1])
        self.to_play = 'w' if to_play == 'white' else 'b'
        self.ep_square = None  # (f, r) of en passant target square
        # Infer castling rights conservatively
        self.castling = {'wK': False, 'wQ': False, 'bK': False, 'bQ': False}
        self._infer_castling()
    
    def _infer_castling(self):
        # White king-side
        if self.board.get((4, 0)) == ('w', 'K') and self.board.get((7, 0)) == ('w', 'R'):
            self.castling['wK'] = True
        if self.board.get((4, 0)) == ('w', 'K') and self.board.get((0, 0)) == ('w', 'R'):
            self.castling['wQ'] = True
        if self.board.get((4, 7)) == ('b', 'K') and self.board.get((7, 7)) == ('b', 'R'):
            self.castling['bK'] = True
        if self.board.get((4, 7)) == ('b', 'K') and self.board.get((0, 7)) == ('b', 'R'):
            self.castling['bQ'] = True
    
    def copy(self):
        b = Board.__new__(Board)
        b.board = dict(self.board)
        b.to_play = self.to_play
        b.ep_square = self.ep_square
        b.castling = dict(self.castling)
        return b
    
    def opponent(self):
        return 'b' if self.to_play == 'w' else 'w'
    
    def is_on_board(self, f, r):
        return 0 <= f <= 7 and 0 <= r <= 7
    
    def is_attacked_by(self, square, by_color):
        """Check if square (f,r) is attacked by any piece of by_color."""
        f, r = square
        
        # Knight attacks
        for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nf, nr = f+df, r+dr
            if self.is_on_board(nf, nr):
                p = self.board.get((nf, nr))
                if p and p[0] == by_color and p[1] == 'N':
                    return True
        
        # King attacks
        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if df == 0 and dr == 0:
                    continue
                nf, nr = f+df, r+dr
                if self.is_on_board(nf, nr):
                    p = self.board.get((nf, nr))
                    if p and p[0] == by_color and p[1] == 'K':
                        return True
        
        # Pawn attacks
        pawn_dir = -1 if by_color == 'w' else 1  # direction pawns attack FROM
        for df in [-1, 1]:
            nf, nr = f+df, r+pawn_dir
            if self.is_on_board(nf, nr):
                p = self.board.get((nf, nr))
                if p and p[0] == by_color and p[1] == 'P':
                    return True
        
        # Sliding pieces: bishop/queen diagonals
        for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nf, nr = f+df, r+dr
            while self.is_on_board(nf, nr):
                p = self.board.get((nf, nr))
                if p:
                    if p[0] == by_color and p[1] in ('B', 'Q'):
                        return True
                    break
                nf += df
                nr += dr
        
        # Sliding pieces: rook/queen straights
        for df, dr in [(-1,0),(1,0),(0,-1),(0,1)]:
            nf, nr = f+df, r+dr
            while self.is_on_board(nf, nr):
                p = self.board.get((nf, nr))
                if p:
                    if p[0] == by_color and p[1] in ('R', 'Q'):
                        return True
                    break
                nf += df
                nr += dr
        
        return False
    
    def find_king(self, color):
        for pos, piece in self.board.items():
            if piece == (color, 'K'):
                return pos
        return None
    
    def in_check(self, color):
        king_pos = self.find_king(color)
        if king_pos is None:
            return True
        opp = 'b' if color == 'w' else 'w'
        return self.is_attacked_by(king_pos, opp)
    
    def generate_pseudo_legal_moves(self):
        """Generate all pseudo-legal moves (may leave king in check)."""
        moves = []
        color = self.to_play
        opp = self.opponent()
        
        for (f, r), (c, pt) in list(self.board.items()):
            if c != color:
                continue
            
            if pt == 'P':
                direction = 1 if color == 'w' else -1
                start_rank = 1 if color == 'w' else 6
                promo_rank = 7 if color == 'w' else 0
                
                # Forward one
                nr = r + direction
                if self.is_on_board(f, nr) and (f, nr) not in self.board:
                    if nr == promo_rank:
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append((f, r, f, nr, promo))
                    else:
                        moves.append((f, r, f, nr, None))
                    # Forward two from start
                    if r == start_rank:
                        nr2 = r + 2 * direction
                        if (f, nr2) not in self.board:
                            moves.append((f, r, f, nr2, None))
                
                # Captures
                for df in [-1, 1]:
                    nf = f + df
                    nr = r + direction
                    if not self.is_on_board(nf, nr):
                        continue
                    target = self.board.get((nf, nr))
                    if target and target[0] == opp:
                        if nr == promo_rank:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append((f, r, nf, nr, promo))
                        else:
                            moves.append((f, r, nf, nr, None))
                    # En passant
                    if self.ep_square and (nf, nr) == self.ep_square:
                        moves.append((f, r, nf, nr, None))
            
            elif pt == 'N':
                for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    nf, nr = f+df, r+dr
                    if self.is_on_board(nf, nr):
                        target = self.board.get((nf, nr))
                        if not target or target[0] == opp:
                            moves.append((f, r, nf, nr, None))
            
            elif pt == 'K':
                for df in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if df == 0 and dr == 0:
                            continue
                        nf, nr = f+df, r+dr
                        if self.is_on_board(nf, nr):
                            target = self.board.get((nf, nr))
                            if not target or target[0] == opp:
                                moves.append((f, r, nf, nr, None))
                
                # Castling
                if color == 'w' and (f, r) == (4, 0):
                    if self.castling.get('wK') and not self.in_check('w'):
                        if (5,0) not in self.board and (6,0) not in self.board:
                            if not self.is_attacked_by((5,0), opp) and not self.is_attacked_by((6,0), opp):
                                moves.append((4, 0, 6, 0, None))
                    if self.castling.get('wQ') and not self.in_check('w'):
                        if (3,0) not in self.board and (2,0) not in self.board and (1,0) not in self.board:
                            if not self.is_attacked_by((3,0), opp) and not self.is_attacked_by((2,0), opp):
                                moves.append((4, 0, 2, 0, None))
                elif color == 'b' and (f, r) == (4, 7):
                    if self.castling.get('bK') and not self.in_check('b'):
                        if (5,7) not in self.board and (6,7) not in self.board:
                            if not self.is_attacked_by((5,7), opp) and not self.is_attacked_by((6,7), opp):
                                moves.append((4, 7, 6, 7, None))
                    if self.castling.get('bQ') and not self.in_check('b'):
                        if (3,7) not in self.board and (2,7) not in self.board and (1,7) not in self.board:
                            if not self.is_attacked_by((3,7), opp) and not self.is_attacked_by((2,7), opp):
                                moves.append((4, 7, 2, 7, None))
            
            elif pt in ('B', 'R', 'Q'):
                directions = []
                if pt in ('B', 'Q'):
                    directions += [(-1,-1),(-1,1),(1,-1),(1,1)]
                if pt in ('R', 'Q'):
                    directions += [(-1,0),(1,0),(0,-1),(0,1)]
                
                for df, dr in directions:
                    nf, nr = f+df, r+dr
                    while self.is_on_board(nf, nr):
                        target = self.board.get((nf, nr))
                        if target:
                            if target[0] == opp:
                                moves.append((f, r, nf, nr, None))
                            break
                        moves.append((f, r, nf, nr, None))
                        nf += df
                        nr += dr
        
        return moves
    
    def make_move(self, move):
        """Make a move and return a new board."""
        ff, fr, tf, tr, promo = move
        b = self.copy()
        piece = b.board.get((ff, fr))
        if piece is None:
            return b
        
        color, pt = piece
        captured = b.board.get((tf, tr))
        
        # En passant capture
        if pt == 'P' and (tf, tr) == self.ep_square:
            ep_pawn_r = fr  # the captured pawn is on the same rank as the moving pawn
            if (tf, ep_pawn_r) in b.board:
                del b.board[(tf, ep_pawn_r)]
        
        # Reset ep square
        b.ep_square = None
        
        # Set ep square for double pawn push
        if pt == 'P' and abs(tr - fr) == 2:
            b.ep_square = (ff, (fr + tr) // 2)
        
        # Move the piece
        del b.board[(ff, fr)]
        if promo:
            promo_map = {'q': 'Q', 'r': 'R', 'b': 'B', 'n': 'N'}
            b.board[(tf, tr)] = (color, promo_map[promo])
        else:
            b.board[(tf, tr)] = piece
        
        # Castling: move rook
        if pt == 'K':
            if (ff, fr) == (4, 0) and (tf, tr) == (6, 0):  # white king-side
                if (7, 0) in b.board:
                    b.board[(5, 0)] = b.board.pop((7, 0))
            elif (ff, fr) == (4, 0) and (tf, tr) == (2, 0):  # white queen-side
                if (0, 0) in b.board:
                    b.board[(3, 0)] = b.board.pop((0, 0))
            elif (ff, fr) == (4, 7) and (tf, tr) == (6, 7):  # black king-side
                if (7, 7) in b.board:
                    b.board[(5, 7)] = b.board.pop((7, 7))
            elif (ff, fr) == (4, 7) and (tf, tr) == (2, 7):  # black queen-side
                if (0, 7) in b.board:
                    b.board[(3, 7)] = b.board.pop((0, 7))
        
        # Update castling rights
        if pt == 'K':
            if color == 'w':
                b.castling['wK'] = False
                b.castling['wQ'] = False
            else:
                b.castling['bK'] = False
                b.castling['bQ'] = False
        if pt == 'R':
            if (ff, fr) == (0, 0):
                b.castling['wQ'] = False
            elif (ff, fr) == (7, 0):
                b.castling['wK'] = False
            elif (ff, fr) == (0, 7):
                b.castling['bQ'] = False
            elif (ff, fr) == (7, 7):
                b.castling['bK'] = False
        # If a rook is captured
        if captured:
            if (tf, tr) == (0, 0):
                b.castling['wQ'] = False
            elif (tf, tr) == (7, 0):
                b.castling['wK'] = False
            elif (tf, tr) == (0, 7):
                b.castling['bQ'] = False
            elif (tf, tr) == (7, 7):
                b.castling['bK'] = False
        
        b.to_play = b.opponent() if b.to_play == color else color
        # Actually just flip
        b.to_play = 'b' if self.to_play == 'w' else 'w'
        
        return b
    
    def generate_legal_moves(self):
        """Generate all legal moves."""
        legal = []
        color = self.to_play
        for move in self.generate_pseudo_legal_moves():
            new_board = self.make_move(move)
            if not new_board.in_check(color):
                legal.append(move)
        return legal
    
    def move_to_uci(self, move):
        ff, fr, tf, tr, promo = move
        s = idx_to_sq(ff, fr) + idx_to_sq(tf, tr)
        if promo:
            s += promo
        return s
    
    def is_endgame(self):
        """Simple endgame detection."""
        material = 0
        for (c, pt) in self.board.values():
            if pt != 'K' and pt != 'P':
                material += PIECE_VALUES.get(pt, 0)
        return material <= 1300  # roughly when queens are off + limited pieces
    
    def evaluate(self):
        """Evaluate position from the perspective of the side to play."""
        endgame = self.is_endgame()
        score = 0
        
        for (f, r), (c, pt) in self.board.items():
            val = PIECE_VALUES.get(pt, 0)
            
            # PST
            if pt == 'K' and endgame:
                pst_table = PST['K_end']
            else:
                pst_table = PST.get(pt)
            
            if pst_table:
                if c == 'w':
                    pst_val = pst_table[pst_index_white(f, r)]
                else:
                    pst_val = pst_table[pst_index_black(f, r)]
            else:
                pst_val = 0
            
            if c == 'w':
                score += val + pst_val
            else:
                score -= val + pst_val
        
        if self.to_play == 'w':
            return score
        else:
            return -score


def move_sort_key(board, move):
    """Score moves for ordering. Higher is better."""
    ff, fr, tf, tr, promo = move
    score = 0
    target = board.board.get((tf, tr))
    moving = board.board.get((ff, fr))
    
    if target:
        # MVV-LVA
        score += 10 * PIECE_VALUES.get(target[1], 0) - PIECE_VALUES.get(moving[1], 0) + 10000
    
    if promo:
        promo_val = {'q': 900, 'r': 500, 'b': 330, 'n': 320}
        score += promo_val.get(promo, 0) + 8000
    
    # Bonus for moving to center
    center_bonus = 0
    if 2 <= tf <= 5 and 2 <= tr <= 5:
        center_bonus = 10
    if 3 <= tf <= 4 and 3 <= tr <= 4:
        center_bonus = 20
    score += center_bonus
    
    return score


def alphabeta(board, depth, alpha, beta, start_time, time_limit, maximizing=True):
    """Alpha-beta search. Returns (score, best_move)."""
    if time.time() - start_time > time_limit:
        return board.evaluate(), None
    
    if depth == 0:
        return quiesce(board, alpha, beta, start_time, time_limit, 4), None
    
    moves = board.generate_legal_moves()
    
    if not moves:
        if board.in_check(board.to_play):
            return -99999 - depth, None  # Checkmate (worse the deeper = we prefer earlier mates)
        return 0, None  # Stalemate
    
    # Sort moves
    moves.sort(key=lambda m: move_sort_key(board, m), reverse=True)
    
    best_move = moves[0]
    best_score = -100000
    
    for move in moves:
        if time.time() - start_time > time_limit:
            break
        new_board = board.make_move(move)
        score, _ = alphabeta(new_board, depth - 1, -beta, -alpha, start_time, time_limit)
        score = -score
        
        if score > best_score:
            best_score = score
            best_move = move
        
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    
    return best_score, best_move


def quiesce(board, alpha, beta, start_time, time_limit, depth):
    """Quiescence search - only consider captures."""
    if time.time() - start_time > time_limit:
        return board.evaluate()
    
    stand_pat = board.evaluate()
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat
    
    if depth <= 0:
        return stand_pat
    
    moves = board.generate_legal_moves()
    # Only captures and promotions
    captures = []
    for m in moves:
        ff, fr, tf, tr, promo = m
        if board.board.get((tf, tr)) or promo:
            captures.append(m)
        elif board.board.get((ff, fr), (None, None))[1] == 'P' and (tf, tr) == board.ep_square:
            captures.append(m)
    
    captures.sort(key=lambda m: move_sort_key(board, m), reverse=True)
    
    for move in captures:
        if time.time() - start_time > time_limit:
            break
        new_board = board.make_move(move)
        score = -quiesce(new_board, -beta, -alpha, start_time, time_limit, depth - 1)
        
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    
    return alpha


def policy(pieces: dict[str, str], to_play: str) -> str:
    start_time = time.time()
    time_limit = 0.75  # leave some margin
    
    board = Board(pieces, to_play)
    
    legal_moves = board.generate_legal_moves()
    
    if not legal_moves:
        # Should not happen if we're called with legal moves
        # Return something
        return "0000"
    
    if len(legal_moves) == 1:
        return board.move_to_uci(legal_moves[0])
    
    best_move = legal_moves[0]
    
    # Iterative deepening
    for depth in range(1, 20):
        if time.time() - start_time > time_limit * 0.6:
            break
        
        score, move = alphabeta(board, depth, -100000, 100000, start_time, time_limit)
        
        if move is not None:
            best_move = move
        
        if time.time() - start_time > time_limit * 0.6:
            break
        
        # If we found checkmate, stop
        if abs(score) > 90000:
            break
    
    return board.move_to_uci(best_move)
