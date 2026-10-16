
import copy

# Piece values in centipawns
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables (simplified for speed)
PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 5, 5, 5, 5, 5, 5, 5],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [0, 0, 0, 2, 2, 0, 0, 0],
    [0, 0, 1, 2, 2, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

def algebraic_to_coords(sq):
    """Convert algebraic notation to coordinates (file, rank)"""
    if len(sq) != 2:
        return None
    try:
        return ord(sq[0]) - ord('a'), int(sq[1]) - 1
    except:
        return None

class SimpleBoard:
    def __init__(self, pieces=None):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        if pieces:
            for sq, piece in pieces.items():
                coords = algebraic_to_coords(sq)
                if coords:
                    f, r = coords
                    self.board[f][r] = piece
    
    def copy(self):
        """Create a copy of the board"""
        new_board = SimpleBoard()
        new_board.board = [row[:] for row in self.board]
        return new_board
    
    def get(self, f, r):
        if 0 <= f < 8 and 0 <= r < 8:
            return self.board[f][r]
        return None
    
    def set(self, f, r, piece):
        if 0 <= f < 8 and 0 <= r < 8:
            self.board[f][r] = piece
    
    def can_move(self, from_f, from_r, to_f, to_r):
        """Check geometric move possibility (ignoring destination content)"""
        piece = self.get(from_f, from_r)
        if not piece:
            return False
        
        ptype = piece[1]
        df = to_f - from_f
        dr = to_r - from_r
        
        if ptype == 'N':
            return (abs(df), abs(dr)) in [(1,2), (2,1)]
        
        if ptype == 'K':
            return abs(df) <= 1 and abs(dr) <= 1
        
        if ptype == 'B':
            if abs(df) != abs(dr):
                return False
            step_f = 1 if df > 0 else -1
            step_r = 1 if dr > 0 else -1
            f, r = from_f + step_f, from_r + step_r
            while (f, r) != (to_f, to_r):
                if self.get(f, r) is not None:
                    return False
                f += step_f
                r += step_r
            return True
        
        if ptype == 'R':
            if df != 0 and dr != 0:
                return False
            step_f = 0 if df == 0 else (1 if df > 0 else -1)
            step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
            f, r = from_f + step_f, from_r + step_r
            while (f, r) != (to_f, to_r):
                if self.get(f, r) is not None:
                    return False
                f += step_f
                r += step_r
            return True
        
        if ptype == 'Q':
            if df == 0 or dr == 0 or abs(df) == abs(dr):
                step_f = 0 if df == 0 else (1 if df > 0 else -1)
                step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
                f, r = from_f + step_f, from_r + step_r
                while (f, r) != (to_f, to_r):
                    if self.get(f, r) is not None:
                        return False
                    f += step_f
                    r += step_r
                return True
            return False
        
        if ptype == 'P':
            color = piece[0]
            dir_ = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            
            # Forward
            if df == 0 and dr == dir_ and self.get(to_f, to_r) is None:
                return True
            
            # Double
            if (df == 0 and from_r == start_rank and dr == 2*dir_ and
                self.get(to_f, to_r) is None and self.get(to_f, to_r - dir_) is None):
                return True
            
            # Capture (including en passant)
            if abs(df) == 1 and dr == dir_:
                return True
            
            return False
        
        return False
    
    def find_origin(self, piece_type, color, dest_f, dest_r, disambiguation):
        """Find origin square for a move"""
        candidates = []
        for f in range(8):
            for r in range(8):
                piece = self.get(f, r)
                if piece == color + piece_type and self.can_move(f, r, dest_f, dest_r):
                    # Apply disambiguation
                    if disambiguation:
                        if len(disambiguation) >= 2:
                            if (ord(disambiguation[0]) - ord('a')) != f:
                                continue
                            if int(disambiguation[1]) - 1 != r:
                                continue
                        elif disambiguation[0].isalpha():
                            if (ord(disambiguation[0]) - ord('a')) != f:
                                continue
                        elif int(disambiguation[0]) - 1 != r:
                            continue
                    candidates.append((f, r))
        return candidates
    
    def evaluate(self, perspective):
        """Evaluate board position"""
        score = 0
        for f in range(8):
            for r in range(8):
                piece = self.get(f, r)
                if piece:
                    color = piece[0]
                    ptype = piece[1]
                    value = PIECE_VALUES[ptype]
                    
                    # Simplified position bonus
                    bonus = 0
                    if ptype == 'P':
                        bonus = PAWN_TABLE[r][f] if color == 'w' else -PAWN_TABLE[7-r][f]
                    
                    if color == 'w':
                        score += value + bonus
                    else:
                        score -= value + bonus
        
        return score if perspective == 'white' else -score

def parse_move(move_str, board, color):
    """Parse SAN move string to coordinates"""
    # Castling
    if move_str in ['O-O', 'O-O-O']:
        rank = 0 if color == 'w' else 7
        king_dest = 6 if move_str == 'O-O' else 2
        return (4, rank), (king_dest, rank), None
    
    # Remove check/checkmate
    if move_str.endswith('+') or move_str.endswith('#'):
        move_str = move_str[:-1]
    
    # Promotion
    promotion = None
    if '=' in move_str:
        idx = move_str.index('=')
        promotion = move_str[idx+1]
        move_str = move_str[:idx]
    
    # Remove capture indicator
    move_str = move_str.replace('x', '')
    
    # Destination square
    if len(move_str) < 2:
        return None
    
    dest_sq = move_str[-2:]
    dest_coords = algebraic_to_coords(dest_sq)
    if not dest_coords:
        return None
    
    dest_f, dest_r = dest_coords
    
    # Piece type
    if move_str[0] in 'KQBRN':
        ptype = move_str[0]
        disambiguation = move_str[1:-2]
    else:
        ptype = 'P'
        disambiguation = move_str[:-2]
    
    # Find origin
    origins = board.find_origin(ptype, color, dest_f, dest_r, disambiguation)
    if not origins:
        return None
    
    return origins[0], (dest_f, dest_r), promotion

def policy(pieces, to_play, legal_moves, memory):
    """Choose the best move from legal_moves"""
    # Always play checkmate if available
    for move in legal_moves:
        if move.endswith('#'):
            return move, memory
    
    board = SimpleBoard(pieces)
    color = 'w' if to_play == 'white' else 'b'
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        parsed = parse_move(move, board, color)
        if not parsed:
            continue
        
        from_coords, to_coords, promotion = parsed
        
        # Apply move
        new_board = board.copy()
        piece = new_board.get(from_coords[0], from_coords[1])
        new_board.set(from_coords[0], from_coords[1], None)
        
        if promotion:
            piece = color + promotion
        
        new_board.set(to_coords[0], to_coords[1], piece)
        
        # Evaluate position
        score = new_board.evaluate(to_play)
        
        # Bonus for giving check
        if move.endswith('+'):
            score += 50
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory
