
import math

# Piece values for material evaluation
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-Square Tables (PST) to encourage good positioning
# Values are added to base piece value. 
# Table is from White's perspective (Rank 0 is rank 8, Rank 7 is rank 1).
# We will index using (row, col).

PST_PAWN = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

PST_KNIGHT = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

PST_BISHOP = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

PST_ROOK = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

PST_QUEEN = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5],
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

PST_KING_MIDGAME = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
]

PST = {
    'P': PST_PAWN,
    'N': PST_KNIGHT,
    'B': PST_BISHOP,
    'R': PST_ROOK,
    'Q': PST_QUEEN,
    'K': PST_KING_MIDGAME
}

class ChessEngine:
    def __init__(self, pieces, to_play):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.colors = [[None for _ in range(8)] for _ in range(8)]
        self.to_play = to_play
        self.my_color = 'w' if to_play == 'white' else 'b'
        self.opp_color = 'b' if self.my_color == 'w' else 'w'
        
        # Parse board
        for sq, piece_code in pieces.items():
            col = ord(sq[0]) - ord('a')
            row = 8 - int(sq[1])
            piece_type = piece_code[1]
            color = piece_code[0]
            self.board[row][col] = piece_type
            self.colors[row][col] = color

    def get_piece_value(self, piece, row, col):
        """Returns material + positional value."""
        val = PIECE_VALUES[piece]
        # Apply PST
        pst = PST.get(piece)
        if pst:
            val += pst[row][col]
        return val

    def evaluate_board(self):
        """Evaluates board from perspective of current player."""
        score = 0
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                color = self.colors[r][c]
                if piece:
                    val = self.get_piece_value(piece, r, c)
                    if color == self.my_color:
                        score += val
                    else:
                        score -= val
        return score

    def is_inside(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == 'K' and self.colors[r][c] == color:
                    return (r, c)
        return None

    def is_square_attacked(self, r, c, by_color):
        """Checks if square (r,c) is attacked by 'by_color'."""
        # Knight attacks
        knight_moves = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr, dc in knight_moves:
            nr, nc = r+dr, c+dc
            if self.is_inside(nr, nc) and self.board[nr][nc] == 'N' and self.colors[nr][nc] == by_color:
                return True
        
        # King attacks
        king_moves = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for dr, dc in king_moves:
            nr, nc = r+dr, c+dc
            if self.is_inside(nr, nc) and self.board[nr][nc] == 'K' and self.colors[nr][nc] == by_color:
                return True

        # Pawn attacks
        # If by_color is white, pawns attack upwards (decreasing row index)
        # If by_color is black, pawns attack downwards (increasing row index)
        p_dir = -1 if by_color == 'w' else 1
        for dc in [-1, 1]:
            nr, nc = r + p_dir, c + dc
            if self.is_inside(nr, nc) and self.board[nr][nc] == 'P' and self.colors[nr][nc] == by_color:
                return True

        # Rook / Queen (Straight lines)
        directions = [(-1,0),(1,0),(0,-1),(0,1)]
        for dr, dc in directions:
            nr, nc = r+dr, c+dc
            while self.is_inside(nr, nc):
                target = self.board[nr][nc]
                if target:
                    if self.colors[nr][nc] == by_color and target in ['R', 'Q']:
                        return True
                    break # Blocked
                nr += dr
                nc += dc
        
        # Bishop / Queen (Diagonals)
        directions = [(-1,-1),(-1,1),(1,-1),(1,1)]
        for dr, dc in directions:
            nr, nc = r+dr, c+dc
            while self.is_inside(nr, nc):
                target = self.board[nr][nc]
                if target:
                    if self.colors[nr][nc] == by_color and target in ['B', 'Q']:
                        return True
                    break
                nr += dr
                nc += dc
        
        return False

    def is_in_check(self, color):
        king_pos = self.find_king(color)
        if not king_pos: return True # Should not happen
        opp = 'b' if color == 'w' else 'w'
        return self.is_square_attacked(king_pos[0], king_pos[1], opp)

    def generate_pseudo_legal_moves(self, color):
        moves = [] # List of (r1, c1, r2, c2, promo)
        
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if not piece or self.colors[r][c] != color:
                    continue
                
                # Pawn
                if piece == 'P':
                    direction = -1 if color == 'w' else 1
                    start_row = 6 if color == 'w' else 1
                    promo_row = 0 if color == 'w' else 7
                    
                    # Move forward
                    nr = r + direction
                    if self.is_inside(nr, c) and not self.board[nr][c]:
                        if nr == promo_row:
                            for p in ['q', 'r', 'b', 'n']:
                                moves.append((r, c, nr, c, p))
                        else:
                            moves.append((r, c, nr, c, None))
                            # Double push
                            if r == start_row:
                                nnr = r + 2*direction
                                if not self.board[nnr][c]:
                                    moves.append((r, c, nnr, c, None))
                    
                    # Captures
                    for dc in [-1, 1]:
                        nc = c + dc
                        if self.is_inside(nr, nc):
                            target = self.board[nr][nc]
                            if target and self.colors[nr][nc] != color:
                                if nr == promo_row:
                                    for p in ['q', 'r', 'b', 'n']:
                                        moves.append((r, c, nr, nc, p))
                                else:
                                    moves.append((r, c, nr, nc, None))
                
                # Knight
                elif piece == 'N':
                    knight_moves = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
                    for dr, dc in knight_moves:
                        nr, nc = r+dr, c+dc
                        if self.is_inside(nr, nc):
                            target = self.board[nr][nc]
                            if not target or self.colors[nr][nc] != color:
                                moves.append((r, c, nr, nc, None))
                
                # King
                elif piece == 'K':
                    king_moves = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
                    for dr, dc in king_moves:
                        nr, nc = r+dr, c+dc
                        if self.is_inside(nr, nc):
                            target = self.board[nr][nc]
                            if not target or self.colors[nr][nc] != color:
                                moves.append((r, c, nr, nc, None))
                
                # Sliding pieces
                elif piece in ['R', 'B', 'Q']:
                    directions = []
                    if piece in ['R', 'Q']:
                        directions += [(-1,0),(1,0),(0,-1),(0,1)]
                    if piece in ['B', 'Q']:
                        directions += [(-1,-1),(-1,1),(1,-1),(1,1)]
                    
                    for dr, dc in directions:
                        nr, nc = r+dr, c+dc
                        while self.is_inside(nr, nc):
                            target = self.board[nr][nc]
                            if not target:
                                moves.append((r, c, nr, nc, None))
                            elif self.colors[nr][nc] != color:
                                moves.append((r, c, nr, nc, None))
                                break
                            else:
                                break
                            nr += dr
                            nc += dc
        return moves

    def make_move(self, move):
        r1, c1, r2, c2, promo = move
        piece = self.board[r1][c1]
        color = self.colors[r1][c1]
        
        # Store state for unmake
        captured_piece = self.board[r2][c2]
        captured_color = self.colors[r2][c2]
        
        # Apply move
        self.board[r2][c2] = piece
        self.colors[r2][c2] = color
        self.board[r1][c1] = None
        self.colors[r1][c1] = None
        
        if promo:
            self.board[r2][c2] = promo.upper()
            
        return (captured_piece, captured_color, r1, c1)

    def unmake_move(self, move, undo_info):
        r1, c1, r2, c2, promo = move
        captured_piece, captured_color, _, _ = undo_info
        
        orig_piece = 'P' if promo else self.board[r2][c2]
        orig_color = self.colors[r2][c2]
        
        self.board[r1][c1] = orig_piece
        self.colors[r1][c1] = orig_color
        
        self.board[r2][c2] = captured_piece
        self.colors[r2][c2] = captured_color

    def get_legal_moves(self):
        pseudo_moves = self.generate_pseudo_legal_moves(self.my_color)
        legal_moves = []
        for move in pseudo_moves:
            undo = self.make_move(move)
            if not self.is_in_check(self.my_color):
                legal_moves.append(move)
            self.unmake_move(move, undo)
        return legal_moves

    def search(self, depth, alpha, beta, maximizing):
        if depth == 0:
            return self.evaluate_board(), None
        
        current_color = self.my_color if maximizing else self.opp_color
        moves = self.generate_pseudo_legal_moves(current_color)
        
        # Filter legal moves and sort for better pruning
        valid_moves = []
        for move in moves:
            undo = self.make_move(move)
            # Check if move leaves current player in check
            # Note: is_in_check checks if 'current_color' king is attacked
            if not self.is_in_check(current_color):
                valid_moves.append(move)
            self.unmake_move(move, undo)
            
        if not valid_moves:
            if self.is_in_check(current_color):
                # Checkmate
                return (-100000 if maximizing else 100000), None
            else:
                # Stalemate
                return 0, None
        
        # Move ordering: Captures first
        def score(m):
            r1, c1, r2, c2, promo = m
            s = 0
            if self.board[r2][c2]: # Capture
                s += 10 * PIECE_VALUES.get(self.board[r2][c2], 0) - PIECE_VALUES.get(self.board[r1][c1], 0)
            if promo: s += 800
            return -s # Descending sort
        
        valid_moves.sort(key=score)
        
        best_move = valid_moves[0] # Default
        
        if maximizing:
            max_eval = -float('inf')
            for move in valid_moves:
                undo = self.make_move(move)
                eval_score, _ = self.search(depth-1, alpha, beta, False)
                self.unmake_move(move, undo)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in valid_moves:
                undo = self.make_move(move)
                eval_score, _ = self.search(depth-1, alpha, beta, True)
                self.unmake_move(move, undo)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def get_best_move_uci(self):
        legal = self.get_legal_moves()
        if not legal:
            return None # Should not happen per problem statement
        
        if len(legal) == 1:
            return self.to_uci(legal[0])
            
        # Perform search
        # Depth 3 is a good balance for 1s in Python
        _, best_move = self.search(3, -float('inf'), float('inf'), True)
        
        if best_move:
            return self.to_uci(best_move)
        else:
            # Fallback
            return self.to_uci(legal[0])

    def to_uci(self, move):
        r1, c1, r2, c2, promo = move
        uci = ""
        uci += chr(c1 + ord('a'))
        uci += str(8 - r1)
        uci += chr(c2 + ord('a'))
        uci += str(8 - r2)
        if promo:
            uci += promo
        return uci

def policy(pieces: dict[str, str], to_play: str) -> str:
    engine = ChessEngine(pieces, to_play)
    return engine.get_best_move_uci()
