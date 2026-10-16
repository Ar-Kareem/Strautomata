
import numpy as np

# Piece values
VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables (from white's perspective, a1=0, h8=63)
# Pawns
PST_P = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]
# Knights
PST_N = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]
# Bishops
PST_B = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]
# Rooks
PST_R = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]
# Queens
PST_Q = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]
# Kings (middle game)
PST_K = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

PST = {'P': PST_P, 'N': PST_N, 'B': PST_B, 'R': PST_R, 'Q': PST_Q, 'K': PST_K}

class Board:
    __slots__ = ('grid', 'to_play', 'color_char', 'opp_color_char')
    
    def __init__(self, pieces, to_play):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        for sq, pc in pieces.items():
            c = ord(sq[0]) - ord('a')
            r = int(sq[1]) - 1
            self.grid[r][c] = pc
        self.to_play = to_play
        self.color_char = 'w' if to_play == 'white' else 'b'
        self.opp_color_char = 'b' if to_play == 'white' else 'w'
    
    def copy(self):
        b = Board.__new__(Board)
        b.grid = [row[:] for row in self.grid]
        b.to_play = self.to_play
        b.color_char = self.color_char
        b.opp_color_char = self.opp_color_char
        return b
    
    def _idx(self, sq):
        return int(sq[1]) - 1, ord(sq[0]) - ord('a')
    
    def _sq(self, r, c):
        return chr(ord('a') + c) + str(r + 1)
    
    def is_attacked(self, r, c, by_color):
        # Pawns
        if by_color == 'w':
            for dc in [-1, 1]:
                nr, nc = r - 1, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and self.grid[nr][nc] == 'wP':
                    return True
        else:
            for dc in [-1, 1]:
                nr, nc = r + 1, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and self.grid[nr][nc] == 'bP':
                    return True
        
        # Knights
        knight = by_color + 'N'
        for dr, dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.grid[nr][nc] == knight:
                return True
        
        # King
        king = by_color + 'K'
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and self.grid[nr][nc] == king:
                    return True
        
        # Sliders
        # Bishop/Queen diagonals
        for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            for i in range(1,8):
                nr, nc = r + dr*i, c + dc*i
                if not (0 <= nr < 8 and 0 <= nc < 8): break
                p = self.grid[nr][nc]
                if p:
                    if p[0] == by_color and (p[1] == 'B' or p[1] == 'Q'):
                        return True
                    break
        # Rook/Queen orthogonals
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            for i in range(1,8):
                nr, nc = r + dr*i, c + dc*i
                if not (0 <= nr < 8 and 0 <= nc < 8): break
                p = self.grid[nr][nc]
                if p:
                    if p[0] == by_color and (p[1] == 'R' or p[1] == 'Q'):
                        return True
                    break
        return False
    
    def find_king(self, color):
        k = color + 'K'
        for r in range(8):
            for c in range(8):
                if self.grid[r][c] == k:
                    return r, c
        return None
    
    def generate_pseudo_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                pc = self.grid[r][c]
                if pc and pc[0] == self.color_char:
                    ptype = pc[1]
                    if ptype == 'P':
                        moves.extend(self._pawn_moves(r, c))
                    elif ptype == 'N':
                        moves.extend(self._knight_moves(r, c))
                    elif ptype == 'B':
                        moves.extend(self._slide_moves(r, c, [(1,1),(1,-1),(-1,1),(-1,-1)]))
                    elif ptype == 'R':
                        moves.extend(self._slide_moves(r, c, [(1,0),(-1,0),(0,1),(0,-1)]))
                    elif ptype == 'Q':
                        moves.extend(self._slide_moves(r, c, [(1,1),(1,-1),(-1,1),(-1,-1),(1,0),(-1,0),(0,1),(0,-1)]))
                    elif ptype == 'K':
                        moves.extend(self._king_moves(r, c))
        return moves
    
    def _pawn_moves(self, r, c):
        moves = []
        d = 1 if self.color_char == 'w' else -1
        start_r = 1 if self.color_char == 'w' else 6
        promo_r = 7 if self.color_char == 'w' else 0
        
        # Forward 1
        nr = r + d
        if 0 <= nr < 8 and self.grid[nr][c] is None:
            if nr == promo_r:
                for p in ['q','r','b','n']:
                    moves.append(self._sq(r,c) + self._sq(nr,c) + p)
            else:
                moves.append(self._sq(r,c) + self._sq(nr,c))
            # Forward 2
            if r == start_r:
                nr2 = r + 2*d
                if self.grid[nr2][c] is None:
                    moves.append(self._sq(r,c) + self._sq(nr2,c))
        
        # Captures
        for dc in [-1, 1]:
            nc = c + dc
            if 0 <= nc < 8 and 0 <= nr < 8:
                target = self.grid[nr][nc]
                if target and target[0] == self.opp_color_char:
                    if nr == promo_r:
                        for p in ['q','r','b','n']:
                            moves.append(self._sq(r,c) + self._sq(nr,nc) + p)
                    else:
                        moves.append(self._sq(r,c) + self._sq(nr,nc))
        return moves
    
    def _knight_moves(self, r, c):
        moves = []
        for dr, dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = self.grid[nr][nc]
                if target is None or target[0] == self.opp_color_char:
                    moves.append(self._sq(r,c) + self._sq(nr,nc))
        return moves
    
    def _slide_moves(self, r, c, directions):
        moves = []
        for dr, dc in directions:
            for i in range(1,8):
                nr, nc = r+dr*i, c+dc*i
                if not (0 <= nr < 8 and 0 <= nc < 8): break
                target = self.grid[nr][nc]
                if target is None:
                    moves.append(self._sq(r,c) + self._sq(nr,nc))
                elif target[0] == self.opp_color_char:
                    moves.append(self._sq(r,c) + self._sq(nr,nc))
                    break
                else:
                    break
        return moves
    
    def _king_moves(self, r, c):
        moves = []
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr==0 and dc==0: continue
                nr, nc = r+dr, c+dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = self.grid[nr][nc]
                    if target is None or target[0] == self.opp_color_char:
                        moves.append(self._sq(r,c) + self._sq(nr,nc))
        
        # Castling
        if self.color_char == 'w' and r == 0 and c == 4:
            # Kingside
            if self.grid[0][7] == 'wR' and self.grid[0][5] is None and self.grid[0][6] is None:
                if not self.is_attacked(0,4,'b') and not self.is_attacked(0,5,'b') and not self.is_attacked(0,6,'b'):
                    moves.append('e1g1')
            # Queenside
            if self.grid[0][0] == 'wR' and self.grid[0][1] is None and self.grid[0][2] is None and self.grid[0][3] is None:
                if not self.is_attacked(0,4,'b') and not self.is_attacked(0,3,'b') and not self.is_attacked(0,2,'b'):
                    moves.append('e1c1')
        elif self.color_char == 'b' and r == 7 and c == 4:
            # Kingside
            if self.grid[7][7] == 'bR' and self.grid[7][5] is None and self.grid[7][6] is None:
                if not self.is_attacked(7,4,'w') and not self.is_attacked(7,5,'w') and not self.is_attacked(7,6,'w'):
                    moves.append('e8g8')
            # Queenside
            if self.grid[7][0] == 'bR' and self.grid[7][1] is None and self.grid[7][2] is None and self.grid[7][3] is None:
                if not self.is_attacked(7,4,'w') and not self.is_attacked(7,3,'w') and not self.is_attacked(7,2,'w'):
                    moves.append('e8c8')
        return moves
    
    def make_move(self, uci):
        # Returns new board with move applied and turn flipped
        b = self.copy()
        r1 = int(uci[1]) - 1
        c1 = ord(uci[0]) - ord('a')
        r2 = int(uci[3]) - 1
        c2 = ord(uci[2]) - ord('a')
        promo = uci[4] if len(uci) > 4 else None
        
        piece = b.grid[r1][c1]
        b.grid[r1][c1] = None
        
        # Castling: move rook
        if piece[1] == 'K' and abs(c2 - c1) == 2:
            if c2 > c1: # kingside
                b.grid[r1][5] = b.grid[r1][7]
                b.grid[r1][7] = None
            else: # queenside
                b.grid[r1][3] = b.grid[r1][0]
                b.grid[r1][0] = None
        
        # Place piece
        if promo:
            b.grid[r2][c2] = b.color_char + promo.upper()
        else:
            b.grid[r2][c2] = piece
        
        # Flip turn
        b.to_play = 'black' if b.to_play == 'white' else 'white'
        b.color_char, b.opp_color_char = b.opp_color_char, b.color_char
        return b

def evaluate(board):
    score = 0
    for r in range(8):
        for c in range(8):
            pc = board.grid[r][c]
            if pc:
                val = VALUES[pc[1]]
                # PST index: white uses r*8+c, black mirrors
                if pc[0] == 'w':
                    idx = r * 8 + c
                else:
                    idx = (7 - r) * 8 + c
                pst_val = PST[pc[1]][idx]
                
                if pc[0] == board.color_char:
                    score += val + pst_val
                else:
                    score -= val + pst_val
    return score

def negamax(board, depth, alpha, beta):
    # Generate legal moves
    pseudo = board.generate_pseudo_moves()
    legal = []
    for move in pseudo:
        new_b = board.make_move(move)
        # Check if our king is safe after move
        kr, kc = new_b.find_king(board.color_char)
        if not new_b.is_attacked(kr, kc, board.opp_color_char):
            legal.append(move)
    
    if not legal:
        kr, kc = board.find_king(board.color_char)
        if board.is_attacked(kr, kc, board.opp_color_char):
            return -1000000 + depth  # Checkmate
        else:
            return 0  # Stalemate
    
    if depth == 0:
        return evaluate(board)
    
    # Sort moves: captures first (simple MVV-LVA)
    def move_score(m):
        r2 = int(m[3]) - 1
        c2 = ord(m[2]) - ord('a')
        target = board.grid[r2][c2]
        if target:
            return 10 * VALUES[target[1]] - VALUES[board.grid[int(m[1])-1][ord(m[0])-ord('a')][1]]
        return 0
    
    legal.sort(key=move_score, reverse=True)
    
    for move in legal:
        new_b = board.make_move(move)
        val = -negamax(new_b, depth - 1, -beta, -alpha)
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val
    return alpha

def policy(pieces: dict, to_play: str) -> str:
    board = Board(pieces, to_play)
    
    # Get legal moves
    pseudo = board.generate_pseudo_moves()
    legal_moves = []
    for move in pseudo:
        new_b = board.make_move(move)
        kr, kc = new_b.find_king(board.color_char)
        if not new_b.is_attacked(kr, kc, board.opp_color_char):
            legal_moves.append(move)
    
    if not legal_moves:
        return ""  # Should not happen per problem statement
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Search depth 3
    best_move = legal_moves[0]
    best_score = -9999999
    
    # Sort for better pruning
    def move_score(m):
        r2 = int(m[3]) - 1
        c2 = ord(m[2]) - ord('a')
        target = board.grid[r2][c2]
        if target:
            return 10 * VALUES[target[1]] - VALUES[board.grid[int(m[1])-1][ord(m[0])-ord('a')][1]]
        return 0
    
    legal_moves.sort(key=move_score, reverse=True)
    
    for move in legal_moves:
        new_b = board.make_move(move)
        score = -negamax(new_b, 3, -10000000, 10000000)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
