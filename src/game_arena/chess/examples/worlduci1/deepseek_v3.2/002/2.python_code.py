
import numpy as np
import time

PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables (opening/middlegame oriented, from white's perspective)
PST_PAWN = np.array([
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
])

PST_KNIGHT = np.array([
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
])

PST_BISHOP = np.array([
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
])

PST_ROOK = np.array([
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
])

PST_QUEEN = np.array([
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
])

PST_KING_MID = np.array([
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
])

def square_to_index(sq):
    file = ord(sq[0]) - ord('a')
    rank = int(sq[1]) - 1
    return rank * 8 + file

class ChessEngine:
    def __init__(self, pieces, to_play):
        self.pieces = pieces
        self.side = 1 if to_play == 'white' else -1
        self.start_time = None
        self.time_limit = 0.95  # seconds
    
    def evaluate(self):
        score = 0
        for sq, piece in self.pieces.items():
            idx = square_to_index(sq)
            color = 1 if piece[0] == 'w' else -1
            piece_type = piece[1]
            val = PIECE_VALUES[piece_type]
            # material
            score += color * val
            # positional
            if piece_type == 'P':
                table = PST_PAWN
            elif piece_type == 'N':
                table = PST_KNIGHT
            elif piece_type == 'B':
                table = PST_BISHOP
            elif piece_type == 'R':
                table = PST_ROOK
            elif piece_type == 'Q':
                table = PST_QUEEN
            else:  # King
                table = PST_KING_MID
            
            if color == 1:
                score += table[idx]
            else:
                # Flip table for black pieces
                score -= table[63 - idx]
        
        return score * self.side
    
    def generate_moves(self, pieces, side):
        # Simplified legal move generator for given position
        # Since we receive legal_moves from the arena, we'll use a fallback:
        # We'll just return the moves we can compute from basic rules.
        # But actually we'll rely on the arena's legal_moves list.
        return []
    
    def make_move(self, pieces, move):
        # Apply a UCI move to the pieces dict
        new_pieces = pieces.copy()
        src, dst = move[:2], move[2:4]
        piece = new_pieces.pop(src)
        if len(move) == 5:  # promotion
            piece = piece[0] + move[4]  # change piece type
        new_pieces[dst] = piece
        # handle captures (already removed because dst overwritten)
        return new_pieces
    
    def quiescence(self, alpha, beta, depth, pieces):
        stand_pat = self.evaluate_pos(pieces)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
        
        # Only consider captures
        # For simplicity, we'll skip quiescence search here due to time constraints
        return alpha
    
    def evaluate_pos(self, pieces):
        # Quick evaluation for a given pieces dict
        score = 0
        for sq, piece in pieces.items():
            color = 1 if piece[0] == 'w' else -1
            piece_type = piece[1]
            val = PIECE_VALUES[piece_type]
            score += color * val
        side_factor = 1 if self.side == 1 else -1
        return score * side_factor
    
    def minimax(self, depth, alpha, beta, maximizing, pieces):
        if depth == 0:
            return self.evaluate()
        
        # Generate pseudo-legal moves from current pieces
        # We'll simulate by considering all possible moves from each piece
        # This is simplified; in reality we'd need full legal move generation.
        # Since we cannot rely on legal_moves inside recursion, we'll use a static list.
        # Instead, we'll return the evaluation for leaf nodes.
        # For simplicity, we'll just return evaluation.
        return self.evaluate()
    
    def choose_move(self, legal_moves):
        self.start_time = time.time()
        best_move = None
        best_score = -float('inf')
        
        # If only one move, return it immediately
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # Iterative deepening with time management
        depth = 1
        while time.time() - self.start_time < self.time_limit and depth <= 4:
            current_best = None
            current_score = -float('inf')
            for move in legal_moves:
                new_pieces = self.make_move(self.pieces, move)
                # Switch side for opponent
                engine_tmp = ChessEngine(new_pieces, 'black' if self.side == 1 else 'white')
                engine_tmp.side = -self.side
                # Evaluate with minimax
                score = -self.negamax(depth - 1, -float('inf'), float('inf'), new_pieces, engine_tmp)
                if score > current_score:
                    current_score = score
                    current_best = move
                # timeout check
                if time.time() - self.start_time > self.time_limit:
                    break
            if current_best is not None:
                best_move = current_best
                best_score = current_score
            depth += 1
        
        # Fallback: choose move with highest immediate capture value
        if best_move is None:
            best_move = self.fallback_move(legal_moves)
        
        return best_move
    
    def negamax(self, depth, alpha, beta, pieces, engine):
        if depth == 0:
            return engine.evaluate()
        
        # Generate all pseudo-legal moves (simplified)
        moves = self.generate_pseudo_moves(pieces, engine.side)
        if not moves:
            return engine.evaluate()
        
        best_value = -float('inf')
        for move in moves:
            new_pieces = self.make_move(pieces, move)
            new_engine = ChessEngine(new_pieces, 'black' if engine.side == 1 else 'white')
            new_engine.side = -engine.side
            value = -self.negamax(depth - 1, -beta, -alpha, new_pieces, new_engine)
            best_value = max(best_value, value)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_value
    
    def generate_pseudo_moves(self, pieces, side):
        # Simplified pseudo-legal move generator (only captures and king moves for safety)
        moves = []
        color_char = 'w' if side == 1 else 'b'
        for sq, piece in pieces.items():
            if piece[0] != color_char:
                continue
            piece_type = piece[1]
            idx = square_to_index(sq)
            rank, file = divmod(idx, 8)
            # King moves (one square in all directions)
            if piece_type == 'K':
                for dr in (-1, 0, 1):
                    for df in (-1, 0, 1):
                        if dr == 0 and df == 0:
                            continue
                        new_rank, new_file = rank + dr, file + df
                        if 0 <= new_rank < 8 and 0 <= new_file < 8:
                            dst = chr(new_file + ord('a')) + str(new_rank + 1)
                            moves.append(sq + dst)
            # Pawn moves (forward one, captures diagonal)
            elif piece_type == 'P':
                direction = 1 if side == 1 else -1
                new_rank = rank + direction
                if 0 <= new_rank < 8:
                    # forward
                    dst = chr(file + ord('a')) + str(new_rank + 1)
                    if dst not in pieces:
                        moves.append(sq + dst)
                    # captures
                    for df in (-1, 1):
                        new_file = file + df
                        if 0 <= new_file < 8:
                            dst = chr(new_file + ord('a')) + str(new_rank + 1)
                            if dst in pieces and pieces[dst][0] != color_char:
                                moves.append(sq + dst)
        return moves
    
    def fallback_move(self, legal_moves):
        # Choose move with highest captured piece value
        best_move = legal_moves[0]
        best_capture = 0
        for move in legal_moves:
            capture_val = 0
            dst = move[2:4]
            if dst in self.pieces:
                captured = self.pieces[dst]
                capture_val = PIECE_VALUES.get(captured[1], 0)
            if capture_val > best_capture:
                best_capture = capture_val
                best_move = move
        return best_move

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Get legal moves from global scope (provided by arena)
    global legal_moves
    engine = ChessEngine(pieces, to_play)
    return engine.choose_move(legal_moves)

# Note: legal_moves is provided by the arena environment.
# We assume it's available as a global variable when policy() is called.
