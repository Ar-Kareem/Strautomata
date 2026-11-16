
import copy
import math
import time
from collections import defaultdict

def policy(pieces: dict[str, str], to_play: str) -> str:
    """Main policy function that selects the best move."""
    # Convert board representation
    board = ChessBoard(pieces, to_play)
    
    # Time management: allocate 0.95 seconds max
    start_time = time.time()
    time_limit = 0.95
    
    # Iterative deepening
    best_move = None
    best_score = -float('inf')
    
    # Generate all legal moves first
    legal_moves = board.generate_legal_moves()
    if not legal_moves:
        return ""  # Should not happen in valid positions
    
    # Simple fallback: just return first move if very few options
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Order moves for better alpha-beta performance
    ordered_moves = order_moves(board, legal_moves)
    
    # Search with increasing depth
    for depth in range(1, 5):  # Up to depth 4 (plies)
        if time.time() - start_time > time_limit * 0.7:
            break
            
        alpha = -float('inf')
        beta = float('inf')
        current_best = None
        current_score = -float('inf')
        
        for move in ordered_moves:
            board_copy = board.copy()
            board_copy.make_move(move)
            
            # Principal variation search
            score = -alpha_beta(board_copy, depth-1, -beta, -alpha, start_time, time_limit)
            
            if time.time() - start_time > time_limit:
                break
                
            if score > current_score:
                current_score = score
                current_best = move
                alpha = max(alpha, score)
        
        if current_best and (not best_move or current_score > best_score):
            best_move = current_best
            best_score = current_score
            
        # If found checkmate, play it immediately
        if current_score > 99999:
            break
    
    # Fallback: pick move with highest immediate evaluation
    if not best_move:
        best_move = max(legal_moves, key=lambda m: quick_evaluate(board, m))
    
    return best_move if best_move else legal_moves[0]


def order_moves(board, moves):
    """Order moves for better alpha-beta pruning."""
    scored_moves = []
    for move in moves:
        score = 0
        
        # Check captures (MVV-LVA)
        if board.is_capture(move):
            victim_val = piece_value(board.get_piece_at(move[2:4])[1])
            attacker_val = piece_value(board.get_piece_at(move[0:2])[1])
            score = 1000 + victim_val - attacker_val//10
        
        # Check promotions
        if len(move) > 4:
            score += 900  # Queen promotion
        
        # Check checks
        board_copy = board.copy()
        board_copy.make_move(move)
        if board_copy.in_check(not board.turn):
            score += 200
        
        # Killer move heuristic (simplified)
        if hasattr(board, 'killer_moves') and move in board.killer_moves:
            score += 100
        
        scored_moves.append((score, move))
    
    scored_moves.sort(reverse=True)
    return [m for _, m in scored_moves]


def alpha_beta(board, depth, alpha, beta, start_time, time_limit):
    """Alpha-beta pruning search with quiescence."""
    # Time check
    if time.time() - start_time > time_limit:
        return evaluate(board)
    
    # Check for terminal states
    if board.is_checkmate():
        return -100000 + (100 - depth)  # Prefer faster checkmates
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    # Quiescence search at leaf nodes
    if depth <= 0:
        return quiescence(board, alpha, beta, start_time, time_limit)
    
    # Generate and order moves
    moves = order_moves(board, board.generate_legal_moves())
    if not moves:
        return evaluate(board)
    
    for move in moves:
        board_copy = board.copy()
        board_copy.make_move(move)
        score = -alpha_beta(board_copy, depth-1, -beta, -alpha, start_time, time_limit)
        
        if score >= beta:
            return beta
        
        alpha = max(alpha, score)
    
    return alpha


def quiescence(board, alpha, beta, start_time, time_limit):
    """Quiescence search to evaluate quiet positions."""
    stand_pat = evaluate(board)
    
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat
    
    # Only consider captures and promotions
    moves = [m for m in board.generate_legal_moves() 
             if board.is_capture(m) or len(m) > 4]
    
    for move in moves:
        if time.time() - start_time > time_limit:
            break
            
        board_copy = board.copy()
        board_copy.make_move(move)
        score = -quiescence(board_copy, -beta, -alpha, start_time, time_limit)
        
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    
    return alpha


def quick_evaluate(board, move):
    """Quick evaluation for move ordering."""
    score = 0
    # Capture
    if board.is_capture(move):
        victim = board.get_piece_at(move[2:4])
        if victim:
            score += piece_value(victim[1])
    # Check
    board_copy = board.copy()
    board_copy.make_move(move)
    if board_copy.in_check(not board.turn):
        score += 50
    # Center control
    if move[2:4] in ['d4', 'e4', 'd5', 'e5']:
        score += 10
    return score


def evaluate(board):
    """Comprehensive evaluation function."""
    if board.is_checkmate():
        return -100000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    score = 0
    
    # Material balance
    for square, piece in board.pieces.items():
        value = piece_value(piece[1])
        if piece[0] == board.color_to_char(board.turn):
            score += value
        else:
            score -= value
        
        # Piece-square tables
        psqt_score = piece_square_value(piece, square, board.game_phase())
        if piece[0] == board.color_to_char(board.turn):
            score += psqt_score
        else:
            score -= psqt_score
    
    # Positional factors
    score += mobility_score(board) * 0.1
    score += pawn_structure_score(board) * 0.5
    score += king_safety_score(board) * 0.8
    score += center_control_score(board) * 0.3
    
    # Tempo
    if board.turn == (to_play == 'white'):
        score += 10  # Side to move advantage
    
    return score


def piece_value(piece_type):
    """Standard piece values."""
    values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    return values.get(piece_type, 0)


def piece_square_value(piece, square, phase):
    """Piece-square tables for different phases."""
    file_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    rank_map = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7}
    
    x = file_map[square[0]]
    y = rank_map[square[1]]
    
    # Flip for black pieces
    if piece[0] == 'b':
        y = 7 - y
    
    # Simplified piece-square tables
    if piece[1] == 'P':
        table = [0, 0, 0, 0, 0, 0, 0, 0,
                50, 50, 50, 50, 50, 50, 50, 50,
                10, 10, 20, 30, 30, 20, 10, 10,
                5, 5, 10, 25, 25, 10, 5, 5,
                0, 0, 0, 20, 20, 0, 0, 0,
                5, -5, -10, 0, 0, -10, -5, 5,
                5, 10, 10, -20, -20, 10, 10, 5,
                0, 0, 0, 0, 0, 0, 0, 0]
        return table[y*8 + x]
    
    elif piece[1] == 'N':
        table = [-50, -40, -30, -30, -30, -30, -40, -50,
                -40, -20, 0, 0, 0, 0, -20, -40,
                -30, 0, 10, 15, 15, 10, 0, -30,
                -30, 5, 15, 20, 20, 15, 5, -30,
                -30, 0, 15, 20, 20, 15, 0, -30,
                -30, 5, 10, 15, 15, 10, 5, -30,
                -40, -20, 0, 5, 5, 0, -20, -40,
                -50, -40, -30, -30, -30, -30, -40, -50]
        return table[y*8 + x]
    
    elif piece[1] == 'B':
        table = [-20, -10, -10, -10, -10, -10, -10, -20,
                -10, 0, 0, 0, 0, 0, 0, -10,
                -10, 0, 5, 10, 10, 5, 0, -10,
                -10, 5, 5, 10, 10, 5, 5, -10,
                -10, 0, 10, 10, 10, 10, 0, -10,
                -10, 10, 10, 10, 10, 10, 10, -10,
                -10, 5, 0, 0, 0, 0, 5, -10,
                -20, -10, -10, -10, -10, -10, -10, -20]
        return table[y*8 + x]
    
    elif piece[1] == 'R':
        table = [0, 0, 0, 0, 0, 0, 0, 0,
                5, 10, 10, 10, 10, 10, 10, 5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                0, 0, 0, 5, 5, 0, 0, 0]
        return table[y*8 + x]
    
    elif piece[1] == 'Q':
        table = [-20, -10, -10, -5, -5, -10, -10, -20,
                -10, 0, 0, 0, 0, 0, 0, -10,
                -10, 0, 5, 5, 5, 5, 0, -10,
                -5, 0, 5, 5, 5, 5, 0, -5,
                0, 0, 5, 5, 5, 5, 0, -5,
                -10, 5, 5, 5, 5, 5, 0, -10,
                -10, 0, 5, 0, 0, 0, 0, -10,
                -20, -10, -10, -5, -5, -10, -10, -20]
        return table[y*8 + x]
    
    elif piece[1] == 'K':
        if phase == 'endgame':
            table = [-50, -40, -30, -20, -20, -30, -40, -50,
                    -30, -20, -10, 0, 0, -10, -20, -30,
                    -30, -10, 20, 30, 30, 20, -10, -30,
                    -30, -10, 30, 40, 40, 30, -10, -30,
                    -30, -10, 30, 40, 40, 30, -10, -30,
                    -30, -10, 20, 30, 30, 20, -10, -30,
                    -30, -30, 0, 0, 0, 0, -30, -30,
                    -50, -30, -30, -30, -30, -30, -30, -50]
        else:
            table = [-30, -40, -40, -50, -50, -40, -40, -30,
                    -30, -40, -40, -50, -50, -40, -40, -30,
                    -30, -40, -40, -50, -50, -40, -40, -30,
                    -30, -40, -40, -50, -50, -40, -40, -30,
                    -20, -30, -30, -40, -40, -30, -30, -20,
                    -10, -20, -20, -20, -20, -20, -20, -10,
                    20, 20, 0, 0, 0, 0, 20, 20,
                    20, 30, 10, 0, 0, 10, 30, 20]
        return table[y*8 + x]
    
    return 0


def mobility_score(board):
    """Calculate mobility score."""
    mobility = 0
    for square, piece in board.pieces.items():
        if piece[0] == board.color_to_char(board.turn):
            # Count number of squares attacked
            moves = board.get_pseudo_legal_moves(square)
            mobility += len(moves)
    return mobility


def pawn_structure_score(board):
    """Evaluate pawn structure."""
    score = 0
    pawns = {sq: pc for sq, pc in board.pieces.items() if pc[1] == 'P'}
    
    for square, piece in pawns.items():
        file = square[0]
        rank = int(square[1])
        
        # Doubled pawns
        same_file = [sq for sq in pawns.keys() if sq[0] == file]
        if len(same_file) > 1:
            score -= 20
        
        # Isolated pawns
        adjacent_files = [chr(ord(file)-1), chr(ord(file)+1)]
        has_friendly_adjacent = False
        for adj_file in adjacent_files:
            if 'a' <= adj_file <= 'h':
                if any(sq[0] == adj_file and pawns[sq][0] == piece[0] 
                       for sq in pawns.keys()):
                    has_friendly_adjacent = True
                    break
        if not has_friendly_adjacent:
            score -= 15
    
    return score


def king_safety_score(board):
    """Evaluate king safety."""
    score = 0
    king_square = None
    
    # Find king
    for square, piece in board.pieces.items():
        if piece[1] == 'K' and piece[0] == board.color_to_char(board.turn):
            king_square = square
            break
    
    if not king_square:
        return 0
    
    file_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    rank_map = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7}
    
    kx = file_map[king_square[0]]
    ky = rank_map[king_square[1]]
    
    # Penalize king in center during opening/middlegame
    if board.game_phase() != 'endgame':
        center_distance = max(abs(kx - 3.5), abs(ky - 3.5))
        score -= center_distance * 10
    
    # Pawn shield
    pawn_shield = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = kx + dx, ky + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                square = chr(ord('a') + nx) + str(ny + 1)
                piece = board.pieces.get(square)
                if piece and piece[1] == 'P' and piece[0] == board.color_to_char(board.turn):
                    pawn_shield += 1
    
    score += pawn_shield * 15
    
    return score


def center_control_score(board):
    """Evaluate center control."""
    score = 0
    center_squares = ['d4', 'e4', 'd5', 'e5']
    
    for square in center_squares:
        piece = board.pieces.get(square)
        if piece:
            if piece[0] == board.color_to_char(board.turn):
                score += 30
            else:
                score -= 30
    
    return score


class ChessBoard:
    """Internal board representation and move generation."""
    
    def __init__(self, pieces, to_play):
        self.pieces = pieces.copy()
        self.turn = (to_play == 'white')
        self.move_history = []
        self.killer_moves = set()
    
    def copy(self):
        new_board = ChessBoard(self.pieces, 'white' if self.turn else 'black')
        new_board.turn = self.turn
        new_board.move_history = self.move_history.copy()
        new_board.killer_moves = self.killer_moves.copy()
        return new_board
    
    def color_to_char(self, is_white):
        return 'w' if is_white else 'b'
    
    def char_to_color(self, char):
        return char == 'w'
    
    def get_piece_at(self, square):
        return self.pieces.get(square)
    
    def is_capture(self, move):
        return move[2:4] in self.pieces
    
    def generate_legal_moves(self):
        """Generate all legal moves for current position."""
        moves = []
        for square, piece in self.pieces.items():
            if self.char_to_color(piece[0]) == self.turn:
                moves.extend(self.get_pseudo_legal_moves(square))
        
        # Filter moves that leave king in check
        legal_moves = []
        for move in moves:
            board_copy = self.copy()
            board_copy.make_move(move)
            if not board_copy.in_check(self.turn):
                legal_moves.append(move)
        
        return legal_moves
    
    def get_pseudo_legal_moves(self, square):
        """Generate pseudo-legal moves from a square."""
        piece = self.pieces.get(square)
        if not piece:
            return []
        
        moves = []
        color, ptype = piece[0], piece[1]
        file, rank = square[0], int(square[1])
        
        if ptype == 'P':
            # Pawn moves
            direction = 1 if color == 'w' else -1
            start_rank = 2 if color == 'w' else 7
            
            # Single move forward
            new_rank = rank + direction
            if 1 <= new_rank <= 8:
                new_square = file + str(new_rank)
                if new_square not in self.pieces:
                    if new_rank in [1, 8]:
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append(square + new_square + promo)
                    else:
                        moves.append(square + new_square)
                    
                    # Double move from starting rank
                    if rank == start_rank:
                        new_rank2 = rank + 2 * direction
                        new_square2 = file + str(new_rank2)
                        if new_square2 not in self.pieces:
                            moves.append(square + new_square2)
            
            # Captures
            for df in [-1, 1]:
                new_file = chr(ord(file) + df)
                if 'a' <= new_file <= 'h':
                    new_rank = rank + direction
                    if 1 <= new_rank <= 8:
                        new_square = new_file + str(new_rank)
                        target = self.pieces.get(new_square)
                        if target and self.char_to_color(target[0]) != self.turn:
                            if new_rank in [1, 8]:
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(square + new_square + promo)
                            else:
                                moves.append(square + new_square)
        
        elif ptype == 'N':
            # Knight moves
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                           (1, -2), (1, 2), (2, -1), (2, 1)]
            for df, dr in knight_moves:
                new_file = chr(ord(file) + df)
                new_rank = rank + dr
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    new_square = new_file + str(new_rank)
                    target = self.pieces.get(new_square)
                    if not target or self.char_to_color(target[0]) != self.turn:
                        moves.append(square + new_square)
        
        elif ptype == 'B':
            # Bishop moves
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            moves.extend(self._slide_moves(square, directions))
        
        elif ptype == 'R':
            # Rook moves
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            moves.extend(self._slide_moves(square, directions))
        
        elif ptype == 'Q':
            # Queen moves
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),
                         (-1, 0), (1, 0), (0, -1), (0, 1)]
            moves.extend(self._slide_moves(square, directions))
        
        elif ptype == 'K':
            # King moves
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    new_file = chr(ord(file) + df)
                    new_rank = rank + dr
                    if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                        new_square = new_file + str(new_rank)
                        target = self.pieces.get(new_square)
                        if not target or self.char_to_color(target[0]) != self.turn:
                            moves.append(square + new_square)
            
            # Castling (simplified - assume available if squares empty)
            if square == ('e1' if color == 'w' else 'e8'):
                # Kingside
                if not any(self.pieces.get(sq) for sq in 
                          [('f' + square[1]), ('g' + square[1])]):
                    moves.append(square + ('g' + square[1]))
                # Queenside
                if not any(self.pieces.get(sq) for sq in 
                          [('d' + square[1]), ('c' + square[1]), ('b' + square[1])]):
                    moves.append(square + ('c' + square[1]))
        
        return moves
    
    def _slide_moves(self, square, directions):
        """Helper for sliding piece moves."""
        moves = []
        file, rank = square[0], int(square[1])
        
        for df, dr in directions:
            for step in range(1, 8):
                new_file = chr(ord(file) + df * step)
                new_rank = rank + dr * step
                
                if not ('a' <= new_file <= 'h' and 1 <= new_rank <= 8):
                    break
                
                new_square = new_file + str(new_rank)
                target = self.pieces.get(new_square)
                
                if not target:
                    moves.append(square + new_square)
                else:
                    if self.char_to_color(target[0]) != self.turn:
                        moves.append(square + new_square)
                    break
        
        return moves
    
    def make_move(self, move):
        """Apply a move to the board."""
        src, dst = move[0:2], move[2:4]
        piece = self.pieces.pop(src)
        
        # Handle promotion
        if len(move) > 4:
            piece = piece[0] + move[4].upper()
        
        self.pieces[dst] = piece
        
        # Remove captured piece
        self.move_history.append(move)
        self.turn = not self.turn
    
    def in_check(self, color):
        """Check if king of given color is in check."""
        king_square = None
        
        # Find king
        for square, piece in self.pieces.items():
            if piece[1] == 'K' and self.char_to_color(piece[0]) == color:
                king_square = square
                break
        
        if not king_square:
            return False
        
        # Check if any opponent piece attacks the king
        for square, piece in self.pieces.items():
            if self.char_to_color(piece[0]) != color:
                moves = self.get_pseudo_legal_moves(square)
                if any(move[2:4] == king_square for move in moves):
                    return True
        
        return False
    
    def is_checkmate(self):
        """Check if current player is checkmated."""
        if not self.in_check(self.turn):
            return False
        return len(self.generate_legal_moves()) == 0
    
    def is_stalemate(self):
        """Check if current position is stalemate."""
        if self.in_check(self.turn):
            return False
        return len(self.generate_legal_moves()) == 0
    
    def is_insufficient_material(self):
        """Check for insufficient material."""
        pieces = list(self.pieces.values())
        
        # Only kings
        if len(pieces) == 2:
            return True
        
        # King + bishop vs king or king + knight vs king
        if len(pieces) == 3:
            piece_types = [p[1] for p in pieces]
            if 'B' in piece_types or 'N' in piece_types:
                return True
        
        return False
    
    def game_phase(self):
        """Determine game phase for evaluation."""
        total_material = 0
        for piece in self.pieces.values():
            total_material += piece_value(piece[1])
        
        if total_material < 2000:  # Approximate endgame threshold
            return 'endgame'
        else:
            return 'middlegame'
