
import random
from typing import Dict, List, Tuple, Optional

# Piece values
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables (from white's perspective, will be flipped for black)
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MIDDLE_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

KING_END_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

PSQ_TABLES = {
    'P': PAWN_TABLE,
    'N': KNIGHT_TABLE,
    'B': BISHOP_TABLE,
    'R': ROOK_TABLE,
    'Q': QUEEN_TABLE,
    'K': KING_MIDDLE_TABLE
}

def square_to_index(square: str) -> int:
    file_idx = ord(square[0]) - ord('a')
    rank_idx = int(square[1]) - 1
    return rank_idx * 8 + file_idx

class Board:
    def __init__(self, pieces: Dict[str, str]):
        self.board = {}
        for sq, piece in pieces.items():
            self.board[sq] = piece
        self.castling_rights = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.ep_square = None
        
    def get_piece(self, square: str) -> Optional[str]:
        return self.board.get(square)
    
    def remove_piece(self, square: str):
        if square in self.board:
            del self.board[square]
    
    def set_piece(self, square: str, piece: str):
        self.board[square] = piece
    
    def is_square_attacked(self, square: str, attacker_color: str) -> bool:
        # Check for attacks from all directions
        r, f = int(square[1]), square[0]
        
        # Knight attacks
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, df in knight_moves:
            nr, nf = r + dr, chr(ord(f) + df)
            if 1 <= nr <= 8 and 'a' <= nf <= 'h':
                target = nf + str(nr)
                piece = self.get_piece(target)
                if piece and piece[0] == attacker_color[0] and piece[1] == 'N':
                    return True
        
        # Sliding pieces (bishop, rook, queen)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for i, (dr, df) in enumerate(directions):
            for step in range(1, 8):
                nr, nf = r + dr * step, chr(ord(f) + df * step)
                if not (1 <= nr <= 8 and 'a' <= nf <= 'h'):
                    break
                target = nf + str(nr)
                piece = self.get_piece(target)
                if piece:
                    if piece[0] == attacker_color[0]:
                        if i < 4 and piece[1] in ['R', 'Q']:  # Orthogonal
                            return True
                        if i >= 4 and piece[1] in ['B', 'Q']:  # Diagonal
                            return True
                    break
        
        # Pawn attacks
        pawn_dir = 1 if attacker_color[0] == 'b' else -1
        for df in [-1, 1]:
            nf = chr(ord(f) + df)
            if 'a' <= nf <= 'h':
                nr = r + pawn_dir
                if 1 <= nr <= 8:
                    target = nf + str(nr)
                    piece = self.get_piece(target)
                    if piece and piece[0] == attacker_color[0] and piece[1] == 'P':
                        return True
        
        # King attacks
        for dr in [-1, 0, 1]:
            for df in [-1, 0, 1]:
                if dr == 0 and df == 0:
                    continue
                nr, nf = r + dr, chr(ord(f) + df)
                if 1 <= nr <= 8 and 'a' <= nf <= 'h':
                    target = nf + str(nr)
                    piece = self.get_piece(target)
                    if piece and piece[0] == attacker_color[0] and piece[1] == 'K':
                        return True
        
        return False
    
    def get_king_square(self, color: str) -> Optional[str]:
        for sq, piece in self.board.items():
            if piece == color[0] + 'K':
                return sq
        return None
    
    def is_check(self, color: str) -> bool:
        king_sq = self.get_king_square(color)
        if not king_sq:
            return False
        opponent = 'b' if color[0] == 'w' else 'w'
        return self.is_square_attacked(king_sq, opponent)
    
    def make_move(self, move_str: str) -> 'Board':
        new_board = Board(dict(self.board))
        new_board.castling_rights = dict(self.castling_rights)
        
        from_sq = move_str[0:2]
        to_sq = move_str[2:4]
        piece = new_board.get_piece(from_sq)
        
        if not piece:
            return new_board
            
        # Handle castling
        if piece[1] == 'K':
            color = piece[0]
            if from_sq == 'e1' and to_sq == 'g1':
                new_board.remove_piece('h1')
                new_board.set_piece('f1', 'wR')
                new_board.castling_rights['wK'] = False
                new_board.castling_rights['wQ'] = False
            elif from_sq == 'e1' and to_sq == 'c1':
                new_board.remove_piece('a1')
                new_board.set_piece('d1', 'wR')
                new_board.castling_rights['wK'] = False
                new_board.castling_rights['wQ'] = False
            elif from_sq == 'e8' and to_sq == 'g8':
                new_board.remove_piece('h8')
                new_board.set_piece('f8', 'bR')
                new_board.castling_rights['bK'] = False
                new_board.castling_rights['bQ'] = False
            elif from_sq == 'e8' and to_sq == 'c8':
                new_board.remove_piece('a8')
                new_board.set_piece('d8', 'bR')
                new_board.castling_rights['bK'] = False
                new_board.castling_rights['bQ'] = False
        
        # Update castling rights
        if piece == 'wK':
            new_board.castling_rights['wK'] = False
            new_board.castling_rights['wQ'] = False
        elif piece == 'bK':
            new_board.castling_rights['bK'] = False
            new_board.castling_rights['bQ'] = False
        elif piece == 'wR':
            if from_sq == 'a1':
                new_board.castling_rights['wQ'] = False
            elif from_sq == 'h1':
                new_board.castling_rights['wK'] = False
        elif piece == 'bR':
            if from_sq == 'a8':
                new_board.castling_rights['bQ'] = False
            elif from_sq == 'h8':
                new_board.castling_rights['bK'] = False
        
        # Handle promotion
        if len(move_str) > 4:
            promo_piece = move_str[4].upper()
            new_board.set_piece(to_sq, piece[0] + promo_piece)
        else:
            new_board.set_piece(to_sq, piece)
        new_board.remove_piece(from_sq)
        
        return new_board
    
    def generate_legal_moves(self, color: str) -> List[str]:
        moves = []
        color_char = color[0]
        opponent_char = 'b' if color_char == 'w' else 'w'
        
        for from_sq, piece in list(self.board.items()):
            if piece[0] != color_char:
                continue
            
            piece_type = piece[1]
            r = int(from_sq[1])
            f = from_sq[0]
            
            if piece_type == 'P':
                direction = 1 if color_char == 'w' else -1
                start_rank = 2 if color_char == 'w' else 7
                
                # Forward move
                to_sq = f + str(r + direction)
                if 1 <= r + direction <= 8 and not self.get_piece(to_sq):
                    if r + direction == 8 or r + direction == 1:
                        for promo in ['q', 'r', 'b', 'n']:
                            test_move = from_sq + to_sq + promo
                            test_board = self.make_move(test_move)
                            if not test_board.is_check(color):
                                moves.append(test_move)
                    else:
                        test_move = from_sq + to_sq
                        test_board = self.make_move(test_move)
                        if not test_board.is_check(color):
                            moves.append(test_move)
                    
                    # Double forward move
                    if r == start_rank:
                        to_sq2 = f + str(r + 2 * direction)
                        if not self.get_piece(to_sq2):
                            test_move = from_sq + to_sq2
                            test_board = self.make_move(test_move)
                            if not test_board.is_check(color):
                                moves.append(test_move)
                
                # Captures
                for df in [-1, 1]:
                    nf = chr(ord(f) + df)
                    if 'a' <= nf <= 'h':
                        nr = r + direction
                        if 1 <= nr <= 8:
                            to_sq = nf + str(nr)
                            target = self.get_piece(to_sq)
                            if target and target[0] == opponent_char:
                                if nr == 8 or nr == 1:
                                    for promo in ['q', 'r', 'b', 'n']:
                                        test_move = from_sq + to_sq + promo
                                        test_board = self.make_move(test_move)
                                        if not test_board.is_check(color):
                                            moves.append(test_move)
                                else:
                                    test_move = from_sq + to_sq
                                    test_board = self.make_move(test_move)
                                    if not test_board.is_check(color):
                                        moves.append(test_move)
            
            elif piece_type == 'N':
                knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
                for dr, df in knight_moves:
                    nr, nf = r + dr, chr(ord(f) + df)
                    if 1 <= nr <= 8 and 'a' <= nf <= 'h':
                        to_sq = nf + str(nr)
                        target = self.get_piece(to_sq)
                        if not target or target[0] == opponent_char:
                            test_move = from_sq + to_sq
                            test_board = self.make_move(test_move)
                            if not test_board.is_check(color):
                                moves.append(test_move)
            
            elif piece_type in ['B', 'R', 'Q']:
                if piece_type == 'B' or piece_type == 'Q':
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                    for dr, df in directions:
                        for step in range(1, 8):
                            nr, nf = r + dr * step, chr(ord(f) + df * step)
                            if not (1 <= nr <= 8 and 'a' <= nf <= 'h'):
                                break
                            to_sq = nf + str(nr)
                            target = self.get_piece(to_sq)
                            if target:
                                if target[0] == opponent_char:
                                    test_move = from_sq + to_sq
                                    test_board = self.make_move(test_move)
                                    if not test_board.is_check(color):
                                        moves.append(test_move)
                                break
                            test_move = from_sq + to_sq
                            test_board = self.make_move(test_move)
                            if not test_board.is_check(color):
                                moves.append(test_move)
                
                if piece_type == 'R' or piece_type == 'Q':
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dr, df in directions:
                        for step in range(1, 8):
                            nr, nf = r + dr * step, chr(ord(f) + df * step)
                            if not (1 <= nr <= 8 and 'a' <= nf <= 'h'):
                                break
                            to_sq = nf + str(nr)
                            target = self.get_piece(to_sq)
                            if target:
                                if target[0] == opponent_char:
                                    test_move = from_sq + to_sq
                                    test_board = self.make_move(test_move)
                                    if not test_board.is_check(color):
                                        moves.append(test_move)
                                break
                            test_move = from_sq + to_sq
                            test_board = self.make_move(test_move)
                            if not test_board.is_check(color):
                                moves.append(test_move)
            
            elif piece_type == 'K':
                for dr in [-1, 0, 1]:
                    for df in [-1, 0, 1]:
                        if dr == 0 and df == 0:
                            continue
                        nr, nf = r + dr, chr(ord(f) + df)
                        if 1 <= nr <= 8 and 'a' <= nf <= 'h':
                            to_sq = nf + str(nr)
                            target = self.get_piece(to_sq)
                            if not target or target[0] == opponent_char:
                                test_move = from_sq + to_sq
                                test_board = self.make_move(test_move)
                                if not test_board.is_check(color):
                                    moves.append(test_move)
                
                # Castling
                if color_char == 'w' and from_sq == 'e1':
                    if self.castling_rights.get('wK', False):
                        if not self.get_piece('f1') and not self.get_piece('g1'):
                            if not self.is_square_attacked('e1', 'b') and not self.is_square_attacked('f1', 'b') and not self.is_square_attacked('g1', 'b'):
                                test_move = 'e1g1'
                                test_board = self.make_move(test_move)
                                if not test_board.is_check('white'):
                                    moves.append(test_move)
                    if self.castling_rights.get('wQ', False):
                        if not self.get_piece('d1') and not self.get_piece('c1') and not self.get_piece('b1'):
                            if not self.is_square_attacked('e1', 'b') and not self.is_square_attacked('d1', 'b') and not self.is_square_attacked('c1', 'b'):
                                test_move = 'e1c1'
                                test_board = self.make_move(test_move)
                                if not test_board.is_check('white'):
                                    moves.append(test_move)
                elif color_char == 'b' and from_sq == 'e8':
                    if self.castling_rights.get('bK', False):
                        if not self.get_piece('f8') and not self.get_piece('g8'):
                            if not self.is_square_attacked('e8', 'w') and not self.is_square_attacked('f8', 'w') and not self.is_square_attacked('g8', 'w'):
                                test_move = 'e8g8'
                                test_board = self.make_move(test_move)
                                if not test_board.is_check('black'):
                                    moves.append(test_move)
                    if self.castling_rights.get('bQ', False):
                        if not self.get_piece('d8') and not self.get_piece('c8') and not self.get_piece('b8'):
                            if not self.is_square_attacked('e8', 'w') and not self.is_square_attacked('d8', 'w') and not self.is_square_attacked('c8', 'w'):
                                test_move = 'e8c8'
                                test_board = self.make_move(test_move)
                                if not test_board.is_check('black'):
                                    moves.append(test_move)
        
        return moves

def evaluate_board(board: Board, color: str) -> int:
    """Evaluate the board from the perspective of the given color."""
    color_char = color[0]
    opponent_char = 'b' if color_char == 'w' else 'w'
    
    score = 0
    total_pieces = len(board.board)
    is_endgame = total_pieces <= 12
    
    for sq, piece in board.board.items():
        piece_color = piece[0]
        piece_type = piece[1]
        sq_idx = square_to_index(sq)
        
        # Material value
        material = PIECE_VALUES[piece_type]
        
        # Positional value
        if piece_type == 'K':
            psq_table = KING_END_TABLE if is_endgame else KING_MIDDLE_TABLE
        else:
            psq_table = PSQ_TABLES.get(piece_type, [0] * 64)
        
        # Flip tables for black
        if piece_color == 'w':
            positional = psq_table[63 - sq_idx]
        else:
            positional = psq_table[sq_idx]
        
        total_val = material + positional
        
        if piece_color == color_char:
            score += total_val
        else:
            score -= total_val
    
    # Bonus for mobility (number of legal moves)
    if is_endgame:
        board_copy = Board(dict(board.board))
        board_copy.castling_rights = dict(board.castling_rights)
        mobility = len(board.generate_legal_moves(color))
        opponent_mobility = len(board.generate_legal_moves('white' if color == 'black' else 'black'))
        score += (mobility - opponent_mobility) * 5
    
    return score

def order_moves(moves: List[str], board: Board, color: str) -> List[str]:
    """Order moves for better pruning: captures/promotions first."""
    scored_moves = []
    for move in moves:
        from_sq = move[:2]
        to_sq = move[2:4]
        piece = board.get_piece(from_sq)
        target = board.get_piece(to_sq)
        
        score = 0
        # Captures: value of captured piece minus value of capturing piece
        if target:
            score += PIECE_VALUES[target[1]] * 10 - PIECE_VALUES[piece[1]] if piece else 0
        # Promotions
        if len(move) > 4:
            promo_piece = move[4].upper()
            score += PIECE_VALUES[promo_piece] * 10
        # Check moves
        new_board = board.make_move(move)
        opponent_color = 'white' if color == 'black' else 'black'
        if new_board.is_check(opponent_color):
            score += PIECE_VALUES['K'] // 2
        
        scored_moves.append((score, move))
    
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    return [move for _, move in scored_moves]

def minimax(board: Board, depth: int, alpha: int, beta: int, maximizing: bool, color: str) -> Tuple[int, Optional[str]]:
    """Minimax with alpha-beta pruning. Returns (score, best_move)."""
    if depth == 0:
        return evaluate_board(board, color), None
    
    opponent_color = 'white' if color == 'black' else 'black'
    current_color = color if maximizing else opponent_color
    
    moves = board.generate_legal_moves(current_color)
    if not moves:
        if board.is_check(current_color):
            # Checkmate
            return (-100000 + (4 - depth) * 1000 if maximizing else 100000 - (4 - depth) * 1000), None
        else:
            # Stalemate
            return 0, None
    
    moves = order_moves(moves, board, current_color)
    best_move = None
    
    if maximizing:
        max_eval = -float('inf')
        for move in moves:
            new_board = board.make_move(move)
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False, color)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = board.make_move(move)
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True, color)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(pieces: Dict[str, str], to_play: str) -> str:
    board = Board(pieces)
    
    # Determine search depth based on number of pieces
    total_pieces = len(pieces)
    if total_pieces > 20:
        depth = 3
    elif total_pieces > 10:
        depth = 4
    else:
        depth = 5
    
    legal_moves = board.generate_legal_moves(to_play)
    if not legal_moves:
        return ""  # Should not happen
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Check for immediate checkmate
    opponent_color = 'white' if to_play == 'black' else 'black'
    for move in legal_moves:
        new_board = board.make_move(move)
        if new_board.is_check(opponent_color):
            opponent_moves = new_board.generate_legal_moves(opponent_color)
            if not opponent_moves:
                return move  # Checkmate
    
    # Use minimax to find best move
    _, best_move = minimax(board, depth, -float('inf'), float('inf'), True, to_play)
    
    if best_move is None:
        best_move = legal_moves[0]
    
    return best_move
