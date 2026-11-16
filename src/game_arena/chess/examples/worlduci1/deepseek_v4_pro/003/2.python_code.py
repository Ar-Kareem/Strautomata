
import numpy as np
from typing import Dict, List, Tuple, Optional

# Piece values
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece square tables (from white's perspective, will flip for black)
# Pawn table
PAWN_TABLE = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0]
])

# Knight table
KNIGHT_TABLE = np.array([
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50]
])

# Bishop table
BISHOP_TABLE = np.array([
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20]
])

# Rook table
ROOK_TABLE = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0]
])

# Queen table
QUEEN_TABLE = np.array([
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20]
])

# King middle game table
KING_MG_TABLE = np.array([
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20]
])

# King end game table
KING_EG_TABLE = np.array([
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10, 0, 0, -10, -20, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -30, 0, 0, 0, 0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50]
])

PIECE_TABLES = {
    'P': PAWN_TABLE,
    'N': KNIGHT_TABLE,
    'B': BISHOP_TABLE,
    'R': ROOK_TABLE,
    'Q': QUEEN_TABLE,
    'K': KING_MG_TABLE
}

def square_to_coords(square: str) -> Tuple[int, int]:
    """Convert algebraic notation to (row, col) from white's perspective bottom-left is (0,0)"""
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return (rank, file)

def coord_to_square(rank: int, file: int) -> str:
    """Convert (row, col) to algebraic notation"""
    return chr(file + ord('a')) + str(rank + 1)

class ChessState:
    def __init__(self, pieces: Dict[str, str], to_play: str):
        self.pieces = pieces.copy()
        self.to_play = 'white' if to_play == 'white' else 'black'
        # Build board representation for faster lookup
        self.board = np.zeros((8, 8), dtype=object)
        for sq, piece in pieces.items():
            r, c = square_to_coords(sq)
            self.board[r, c] = piece
        
    def is_white_turn(self) -> bool:
        return self.to_play == 'white'
    
    def get_piece_color(self, piece: str) -> str:
        return 'w' if piece[0] == 'w' else 'b'
    
    def get_piece_type(self, piece: str) -> str:
        return piece[1]
    
    def is_endgame(self) -> bool:
        """Check if we're in an endgame position (few pieces)"""
        queens = 0
        minor_and_rook = 0
        for piece in self.pieces.values():
            if piece[1] == 'Q':
                queens += 1
            elif piece[1] in ['R', 'B', 'N']:
                minor_and_rook += 1
        return queens == 0 or (queens == 1 and minor_and_rook <= 2)
    
    def is_in_check(self, color: str) -> bool:
        """Check if the king of the given color is in check"""
        # Find king
        king_sq = None
        for sq, piece in self.pieces.items():
            if piece == f'{color}K':
                king_sq = sq
                break
        if king_sq is None:
            return True  # King captured
        
        # Check if any opponent piece can capture the king
        opponent_color = 'b' if color == 'w' else 'w'
        return self.is_square_attacked(king_sq, opponent_color)
    
    def is_square_attacked(self, square: str, attacker_color: str) -> bool:
        """Check if a square is attacked by any piece of the given color"""
        r, c = square_to_coords(square)
        
        # Knight attacks
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), 
                        (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in knight_moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                piece = self.board[nr, nc]
                if piece and self.get_piece_color(piece) == attacker_color and self.get_piece_type(piece) == 'N':
                    return True
        
        # Pawn attacks
        pawn_direction = -1 if attacker_color == 'w' else 1
        for dc in [-1, 1]:
            nr, nc = r + pawn_direction, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                piece = self.board[nr, nc]
                if piece and self.get_piece_color(piece) == attacker_color and self.get_piece_type(piece) == 'P':
                    return True
        
        # King attacks
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in king_moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                piece = self.board[nr, nc]
                if piece and self.get_piece_color(piece) == attacker_color and self.get_piece_type(piece) == 'K':
                    return True
        
        # Sliding pieces (bishop, rook, queen)
        directions = {
            'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
            'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
            'Q': [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        }
        
        for piece_type, dirs in directions.items():
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    piece = self.board[nr, nc]
                    if piece:
                        if (self.get_piece_color(piece) == attacker_color and 
                            self.get_piece_type(piece) in [piece_type, 'Q']):
                            return True
                        break
                    nr += dr
                    nc += dc
        
        return False
    
    def make_move(self, move: str) -> 'ChessState':
        """Make a move and return a new state"""
        new_pieces = self.pieces.copy()
        
        from_sq = move[0:2]
        to_sq = move[2:4]
        
        # Handle promotion
        if len(move) == 5:
            promotion_piece = move[4].upper()
            player_color = 'w' if self.is_white_turn() else 'b'
            new_pieces.pop(from_sq)
            new_pieces[to_sq] = f'{player_color}{promotion_piece}'
        else:
            # Regular move
            piece = new_pieces.pop(from_sq)
            new_pieces[to_sq] = piece
        
        next_turn = 'black' if self.is_white_turn() else 'white'
        return ChessState(new_pieces, next_turn)
    
    def generate_moves(self) -> List[str]:
        """Generate all legal moves for the current player"""
        moves = []
        player_color = 'w' if self.is_white_turn() else 'w'
        opponent_color = 'b' if self.is_white_turn() else 'b'
        to_play_color = 'w' if self.is_white_turn() else 'b'
        
        for sq, piece in self.pieces.items():
            if self.get_piece_color(piece) != to_play_color:
                continue
            
            piece_type = self.get_piece_type(piece)
            r, c = square_to_coords(sq)
            
            if piece_type == 'P':
                # Pawn moves
                direction = 1 if self.is_white_turn() else -1
                start_rank = 1 if self.is_white_turn() else 6
                promotion_rank = 7 if self.is_white_turn() else 0
                
                # Forward one
                nr = r + direction
                if 0 <= nr < 8:
                    if not self.board[nr, c]:
                        if nr == promotion_rank:
                            # Promotion
                            for prom_piece in ['q', 'r', 'b', 'n']:
                                moves.append(sq + coord_to_square(nr, c) + prom_piece)
                        else:
                            moves.append(sq + coord_to_square(nr, c))
                        
                        # Forward two from start
                        if r == start_rank and not self.board[r + 2*direction, c]:
                            moves.append(sq + coord_to_square(r + 2*direction, c))
                
                # Captures
                for dc in [-1, 1]:
                    nc = c + dc
                    if 0 <= nc < 8:
                        nr = r + direction
                        if 0 <= nr < 8:
                            target = self.board[nr, nc]
                            if target and self.get_piece_color(target) == opponent_color:
                                if nr == promotion_rank:
                                    for prom_piece in ['q', 'r', 'b', 'n']:
                                        moves.append(sq + coord_to_square(nr, nc) + prom_piece)
                                else:
                                    moves.append(sq + coord_to_square(nr, nc))
            
            elif piece_type == 'N':
                knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), 
                                (1, -2), (1, 2), (2, -1), (2, 1)]
                for dr, dc in knight_moves:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        target = self.board[nr, nc]
                        if not target or self.get_piece_color(target) == opponent_color:
                            moves.append(sq + coord_to_square(nr, nc))
            
            elif piece_type in ['B', 'R', 'Q']:
                directions = {
                    'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
                    'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
                    'Q': [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                }
                for dr, dc in directions[piece_type]:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 8 and 0 <= nc < 8:
                        target = self.board[nr, nc]
                        if not target:
                            moves.append(sq + coord_to_square(nr, nc))
                        else:
                            if self.get_piece_color(target) == opponent_color:
                                moves.append(sq + coord_to_square(nr, nc))
                            break
                        nr += dr
                        nc += dc
            
            elif piece_type == 'K':
                king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                for dr, dc in king_moves:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        target = self.board[nr, nc]
                        if not target or self.get_piece_color(target) == opponent_color:
                            moves.append(sq + coord_to_square(nr, nc))
        
        # Filter out illegal moves (moves that leave the king in check)
        legal_moves = []
        for move in moves:
            new_state = self.make_move(move)
            if not new_state.is_in_check(to_play_color):
                legal_moves.append(move)
        
        return legal_moves

def evaluate_state(state: ChessState) -> float:
    """Evaluate the position from the perspective of the side to move"""
    score = 0
    is_endgame = state.is_endgame()
    player_color = 'w' if state.is_white_turn() else 'b'
    opponent_color = 'b' if state.is_white_turn() else 'w'
    
    # Check for checkmate
    legal_moves = state.generate_moves()
    if len(legal_moves) == 0:
        if state.is_in_check(player_color):
            return -99999  # Checkmate, losing
        else:
            return 0  # Stalemate
    
    # Material and positional evaluation
    for sq, piece in state.pieces.items():
        piece_color = state.get_piece_color(piece)
        piece_type = state.get_piece_type(piece)
        r, c = square_to_coords(sq)
        
        # Material value
        value = PIECE_VALUES[piece_type]
        
        # Positional value from piece-square tables
        if piece_type == 'K':
            if is_endgame:
                pos_value = KING_EG_TABLE[r, c]
            else:
                pos_value = KING_MG_TABLE[r, c]
        else:
            table = PIECE_TABLES[piece_type]
            # Flip table for black pieces
            if piece_color == 'w':
                pos_value = table[7 - r, c]  # Flip rank for white perspective
            else:
                pos_value = -table[r, c]  # Flip for black
        
        total_piece_value = value + pos_value
        
        if piece_color == player_color:
            score += total_piece_value
        else:
            score -= total_piece_value
    
    # Add bonus for mobility (having more legal moves)
    mobility = len(legal_moves)
    score += mobility * 0.5
    
    # King safety: penalize if king is exposed
    player_king_sq = None
    for sq, piece in state.pieces.items():
        if piece == f'{player_color}K':
            player_king_sq = sq
            break
    
    if player_king_sq and not is_endgame:
        # Count pawns around king
        kr, kc = square_to_coords(player_king_sq)
        pawn_shield = 0
        pawn_shield_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in pawn_shield_offsets:
            nr, nc = kr + dr, kc + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                piece = state.board[nr, nc]
                if piece and state.get_piece_color(piece) == player_color and state.get_piece_type(piece) == 'P':
                    pawn_shield += 10
        score += pawn_shield
    
    return score

def minimax(state: ChessState, depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[float, Optional[str]]:
    """Minimax with alpha-beta pruning"""
    if depth == 0:
        return evaluate_state(state), None
    
    legal_moves = state.generate_moves()
    
    if len(legal_moves) == 0:
        if state.is_in_check('w' if state.is_white_turn() else 'b'):
            return (-99999 if maximizing else 99999), None
        return 0, None
    
    if maximizing:
        max_eval = -float('inf')
        best_move = legal_moves[0]
        for move in legal_moves:
            new_state = state.make_move(move)
            eval_score, _ = minimax(new_state, depth - 1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = legal_moves[0]
        for move in legal_moves:
            new_state = state.make_move(move)
            eval_score, _ = minimax(new_state, depth - 1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(pieces: Dict[str, str], to_play: str) -> str:
    """Select the best move"""
    state = ChessState(pieces, to_play)
    legal_moves = state.generate_moves()
    
    if len(legal_moves) == 0:
        # Should not happen, but return a dummy move
        return list(pieces.keys())[0] + list(pieces.keys())[0]
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Check for immediate checkmate
    for move in legal_moves:
        new_state = state.make_move(move)
        opponent_moves = new_state.generate_moves()
        if len(opponent_moves) == 0 and new_state.is_in_check('b' if state.is_white_turn() else 'w'):
            return move
    
    # Determine search depth based on number of pieces
    num_pieces = len(pieces)
    if num_pieces <= 6:
        depth = 6
    elif num_pieces <= 12:
        depth = 4
    elif num_pieces <= 20:
        depth = 3
    else:
        depth = 2
    
    # Iterative deepening for better time management
    best_move = legal_moves[0]
    for current_depth in range(1, depth + 1):
        _, move = minimax(state, current_depth, -float('inf'), float('inf'), True)
        if move is not None:
            best_move = move
    
    return best_move
