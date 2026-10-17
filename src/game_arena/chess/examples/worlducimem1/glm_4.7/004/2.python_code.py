
import random
from typing import Dict, List, Tuple, Optional

# Piece values for evaluation
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

# Position tables (from white's perspective, mirrored for black)
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

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

def square_to_idx(square: str) -> int:
    file = ord(square[0]) - ord('a')
    rank = 8 - int(square[1])
    return rank * 8 + file

def idx_to_square(idx: int) -> str:
    rank = 8 - idx // 8
    file = chr(ord('a') + idx % 8)
    return f"{file}{rank}"

def get_piece_color(piece: str) -> str:
    return piece[0]

def get_piece_type(piece: str) -> str:
    return piece[1]

def opponent_color(color: str) -> str:
    return 'b' if color == 'w' else 'w'

def is_on_board(idx: int) -> bool:
    return 0 <= idx < 64

class ChessEngine:
    def __init__(self):
        self.pieces = {}
        self.to_play = 'w'
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant_square = None
    
    def set_position(self, pieces: Dict[str, str], to_play: str):
        self.pieces = pieces.copy()
        self.to_play = 'w' if to_play == 'white' else 'b'
        self.castling_rights = {
            'K': pieces.get('e1') == 'wK' and pieces.get('h1') == 'wR',
            'Q': pieces.get('e1') == 'wK' and pieces.get('a1') == 'wR',
            'k': pieces.get('e8') == 'bK' and pieces.get('h8') == 'bR',
            'q': pieces.get('e8') == 'bK' and pieces.get('a8') == 'bR',
        }
        self.en_passant_square = None
    
    def get_piece_at(self, square: str) -> Optional[str]:
        return self.pieces.get(square)
    
    def get_piece_at_idx(self, idx: int) -> Optional[str]:
        return self.get_piece_at(idx_to_square(idx))
    
    def is_empty(self, square: str) -> bool:
        return square not in self.pieces
    
    def is_enemy(self, square: str, color: str) -> bool:
        piece = self.get_piece_at(square)
        return piece is not None and get_piece_color(piece) != color
    
    def find_king(self, color: str) -> Optional[str]:
        king_piece = color + 'K'
        for square, piece in self.pieces.items():
            if piece == king_piece:
                return square
        return None
    
    def is_square_attacked(self, square: str, by_color: str) -> bool:
        idx = square_to_idx(square)
        
        pawn_dir = -1 if by_color == 'w' else 1
        for df in [-1, 1]:
            pawn_rank = idx // 8 + pawn_dir
            pawn_file = idx % 8 + df
            if 0 <= pawn_rank < 8 and 0 <= pawn_file < 8:
                pawn_idx = pawn_rank * 8 + pawn_file
                piece = self.get_piece_at_idx(pawn_idx)
                if piece and get_piece_color(piece) == by_color and get_piece_type(piece) == 'P':
                    return True
        
        for offset in [-17, -15, -10, -6, 6, 10, 15, 17]:
            new_idx = idx + offset
            if is_on_board(new_idx):
                old_file = idx % 8
                new_file = new_idx % 8
                if abs(old_file - new_file) <= 2:
                    piece = self.get_piece_at_idx(new_idx)
                    if piece and get_piece_color(piece) == by_color and get_piece_type(piece) == 'N':
                        return True
        
        for offset in [-9, -8, -7, -1, 1, 7, 8, 9]:
            new_idx = idx + offset
            if is_on_board(new_idx):
                old_file = idx % 8
                new_file = new_idx % 8
                if abs(old_file - new_file) <= 1:
                    piece = self.get_piece_at_idx(new_idx)
                    if piece and get_piece_color(piece) == by_color and get_piece_type(piece) == 'K':
                        return True
        
        for dr, df in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for dist in range(1, 8):
                new_rank = idx // 8 + dr * dist
                new_file = idx % 8 + df * dist
                if 0 <= new_rank < 8 and 0 <= new_file < 8:
                    new_idx = new_rank * 8 + new_file
                    piece = self.get_piece_at_idx(new_idx)
                    if piece:
                        if get_piece_color(piece) == by_color and get_piece_type(piece) in ['R', 'Q']:
                            return True
                        break
                else:
                    break
        
        for dr, df in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            for dist in range(1, 8):
                new_rank = idx // 8 + dr * dist
                new_file = idx % 8 + df * dist
                if 0 <= new_rank < 8 and 0 <= new_file < 8:
                    new_idx = new_rank * 8 + new_file
                    piece = self.get_piece_at_idx(new_idx)
                    if piece:
                        if get_piece_color(piece) == by_color and get_piece_type(piece) in ['B', 'Q']:
                            return True
                        break
                else:
                    break
        
        return False
    
    def in_check(self, color: str) -> bool:
        king_square = self.find_king(color)
        if king_square is None:
            return False
        return self.is_square_attacked(king_square, opponent_color(color))
    
    def generate_pseudo_legal_moves(self, color: str) -> List[str]:
        moves = []
        for square, piece in self.pieces.items():
            if get_piece_color(piece) == color:
                piece_type = get_piece_type(piece)
                if piece_type == 'P':
                    moves.extend(self._pawn_moves(square, piece))
                elif piece_type == 'N':
                    moves.extend(self._knight_moves(square, piece))
                elif piece_type == 'B':
                    moves.extend(self._bishop_moves(square, piece))
                elif piece_type == 'R':
                    moves.extend(self._rook_moves(square, piece))
                elif piece_type == 'Q':
                    moves.extend(self._queen_moves(square, piece))
                elif piece_type == 'K':
                    moves.extend(self._king_moves(square, piece))
        return moves
    
    def _pawn_moves(self, square: str, piece: str) -> List[str]:
        moves = []
        color = get_piece_color(piece)
        idx = square_to_idx(square)
        rank = idx // 8
        file = idx % 8
        direction = -1 if color == 'w' else 1
        start_rank = 6 if color == 'w' else 1
        promotion_rank = 0 if color == 'w' else 7
        
        new_rank = rank + direction
        if 0 <= new_rank <= 7:
            new_idx = new_rank * 8 + file
            new_square = idx_to_square(new_idx)
            if self.is_empty(new_square):
                if new_rank == promotion_rank:
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(square + new_square + promo)
                else:
                    moves.append(square + new_square)
                    if rank == start_rank:
                        new_rank2 = rank + 2 * direction
                        new_idx2 = new_rank2 * 8 + file
                        new_square2 = idx_to_square(new_idx2)
                        if self.is_empty(new_square2):
                            moves.append(square + new_square2)
        
        for df in [-1, 1]:
            new_file = file + df
            if 0 <= new_file <= 7:
                new_idx = new_rank * 8 + new_file
                new_square = idx_to_square(new_idx)
                if self.is_enemy(new_square, color):
                    if new_rank == promotion_rank:
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append(square + new_square + promo)
                    else:
                        moves.append(square + new_square)
                elif self.en_passant_square == new_square:
                    moves.append(square + new_square)
        
        return moves
    
    def _knight_moves(self, square: str, piece: str) -> List[str]:
        moves = []
        color = get_piece_color(piece)
        idx = square_to_idx(square)
        
        for offset in [-17, -15, -10, -6, 6, 10, 15, 17]:
            new_idx = idx + offset
            if is_on_board(new_idx):
                old_file = idx % 8
                new_file = new_idx % 8
                if abs(old_file - new_file) <= 2:
                    new_square = idx_to_square(new_idx)
                    if self.is_empty(new_square) or self.is_enemy(new_square, color):
                        moves.append(square + new_square)
        
        return moves
    
    def _sliding_moves(self, square: str, piece: str, directions: List[Tuple[int, int]]) -> List[str]:
        moves = []
        color = get_piece_color(piece)
        idx = square_to_idx(square)
        
        for dr, df in directions:
            for dist in range(1, 8):
                new_rank = (idx // 8) + dr * dist
                new_file = (idx % 8) + df * dist
                if 0 <= new_rank < 8 and 0 <= new_file < 8:
                    new_idx = new_rank * 8 + new_file
                    new_square = idx_to_square(new_idx)
                    if self.is_empty(new_square):
                        moves.append(square + new_square)
                    elif self.is_enemy(new_square, color):
                        moves.append(square + new_square)
                        break
                    else:
                        break
                else:
                    break
        
        return moves
    
    def _bishop_moves(self, square: str, piece: str) -> List[str]:
        return self._sliding_moves(square, piece, [(-1, -1), (-1, 1), (1, -1), (1, 1)])
    
    def _rook_moves(self, square: str, piece: str) -> List[str]:
        return self._sliding_moves(square, piece, [(-1, 0), (1, 0), (0, -1), (0, 1)])
    
    def _queen_moves(self, square: str, piece: str) -> List[str]:
        return self._sliding_moves(square, piece, [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)])
    
    def _king_moves(self, square: str, piece: str) -> List[str]:
        moves = []
        color = get_piece_color(piece)
        idx = square_to_idx(square)
        
        for dr, df in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_rank = (idx // 8) + dr
            new_file = (idx % 8) + df
            if 0 <= new_rank < 8 and 0 <= new_file < 8:
                new_idx = new_rank * 8 + new_file
                new_square = idx_to_square(new_idx)
                if self.is_empty(new_square) or self.is_enemy(new_square, color):
                    moves.append(square + new_square)
        
        if color == 'w' and square == 'e1' and not self.in_check('w'):
            if self.castling_rights['K'] and self.is_empty('f1') and self.is_empty('g1'):
                if not self.is_square_attacked('f1', 'b') and not self.is_square_attacked('g1', 'b'):
                    moves.append('e1g1')
            if self.castling_rights['Q'] and self.is_empty('d1') and self.is_empty('c1') and self.is_empty('b1'):
                if not self.is_square_attacked('d1', 'b') and not self.is_square_attacked('c1', 'b'):
                    moves.append('e1c1')
        elif color == 'b' and square == 'e8' and not self.in_check('b'):
            if self.castling_rights['k'] and self.is_empty('f8') and self.is_empty('g8'):
                if not self.is_square_attacked('f8', 'w') and not self.is_square_attacked('g8', 'w'):
                    moves.append('e8g8')
            if self.castling_rights['q'] and self.is_empty('d8') and self.is_empty('c8') and self.is_empty('b8'):
                if not self.is_square_attacked('d8', 'w') and not self.is_square_attacked('c8', 'w'):
                    moves.append('e8c8')
        
        return moves
    
    def generate_legal_moves(self) -> List[str]:
        pseudo_moves = self.generate_pseudo_legal_moves(self.to_play)
        legal_moves = []
        
        for move in pseudo_moves:
            if self._is_move_legal(move):
                legal_moves.append(move)
        
        return legal_moves
    
    def _is_move_legal(self, move: str) -> bool:
        saved_state = self._save_state()
        self._make_move(move)
        in_check_after = self.in_check(self.to_play)
        self._restore_state(saved_state)
        return not in_check_after
    
    def _save_state(self) -> dict:
        return {
            'pieces': self.pieces.copy(),
            'castling_rights': self.castling_rights.copy(),
            'en_passant_square': self.en_passant_square,
            'to_play': self.to_play,
        }
    
    def _restore_state(self, state: dict):
        self.pieces = state['pieces']
        self.castling_rights = state['castling_rights']
        self.en_passant_square = state['en_passant_square']
        self.to_play = state['to_play']
    
    def _make_move(self, move: str):
        from_square = move[:2]
        to_square = move[2:4]
        piece = self.pieces[from_square]
        color = get_piece_color(piece)
        piece_type = get_piece_type(piece)
        
        if piece_type == 'P' and to_square == self.en_passant_square:
            direction = -1 if color == 'w' else 1
            captured_square = idx_to_square(square_to_idx(to_square) - direction * 8)
            del self.pieces[captured_square]
        
        if piece_type == 'K' and abs(square_to_idx(from_square) - square_to_idx(to_square)) == 2:
            if to_square == 'g1':
                self.pieces['f1'] = self.pieces['h1']
                del self.pieces['h1']
            elif to_square == 'c1':
                self.pieces['d1'] = self.pieces['a1']
                del self.pieces['a1']
            elif to_square == 'g8':
                self.pieces['f8'] = self.pieces['h8']
                del self.pieces['h8']
            elif to_square == 'c8':
                self.pieces['d8'] = self.pieces['a8']
                del self.pieces['a8']
        
        del self.pieces[from_square]
        
        if len(move) > 4:
            new_piece = color + move[4].upper()
        else:
            new_piece = piece
        
        self.pieces[to_square] = new_piece
        
        if from_square == 'e1':
            self.castling_rights['K'] = False
            self.castling_rights['Q'] = False
        elif from_square == 'e8':
            self.castling_rights['k'] = False
            self.castling_rights['q'] = False
        elif from_square == 'a1':
            self.castling_rights['Q'] = False
        elif from_square == 'h1':
            self.castling_rights['K'] = False
        elif from_square == 'a8':
            self.castling_rights['q'] = False
        elif from_square == 'h8':
            self.castling_rights['k'] = False
        
        if to_square == 'a1':
            self.castling_rights['Q'] = False
        elif to_square == 'h1':
            self.castling_rights['K'] = False
        elif to_square == 'a8':
            self.castling_rights['q'] = False
        elif to_square == 'h8':
            self.castling_rights['k'] = False
        
        self.en_passant_square = None
        if piece_type == 'P' and abs(square_to_idx(from_square) - square_to_idx(to_square)) == 16:
            self.en_passant_square = idx_to_square((square_to_idx(from_square) + square_to_idx(to_square)) // 2)
        
        self.to_play = opponent_color(self.to_play)
    
    def evaluate(self) -> int:
        score = 0
        
        for square, piece in self.pieces.items():
            piece_type = get_piece_type(piece)
            piece_color = get_piece_color(piece)
            idx = square_to_idx(square)
            
            value = PIECE_VALUES[piece_type]
            
            pos_value = 0
            if piece_type == 'P':
                pos_value = PAWN_TABLE[idx] if piece_color == 'w' else PAWN_TABLE[63 - idx]
            elif piece_type == 'N':
                pos_value = KNIGHT_TABLE[idx] if piece_color == 'w' else KNIGHT_TABLE[63 - idx]
            elif piece_type == 'B':
                pos_value = BISHOP_TABLE[idx] if piece_color == 'w' else BISHOP_TABLE[63 - idx]
            elif piece_type == 'R':
                pos_value = ROOK_TABLE[idx] if piece_color == 'w' else ROOK_TABLE[63 - idx]
            elif piece_type == 'Q':
                pos_value = QUEEN_TABLE[idx] if piece_color == 'w' else QUEEN_TABLE[63 - idx]
            elif piece_type == 'K':
                pos_value = KING_TABLE[idx] if piece_color == 'w' else KING_TABLE[63 - idx]
            
            total = value + pos_value
            
            if piece_color == self.to_play:
                score += total
            else:
                score -= total
        
        return score
    
    def alpha_beta(self, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[str]]:
        if depth == 0:
            return self.evaluate(), None
        
        moves = self.generate_legal_moves()
        
        if not moves:
            if self.in_check(self.to_play):
                return -20000 + depth, None
            return 0, None
        
        def move_sort_key(move):
            to_square = move[2:4]
            target = self.get_piece_at(to_square)
            if target:
                return -PIECE_VALUES[get_piece_type(target)]
            return 0
        
        moves.sort(key=move_sort_key)
        
        best_move = moves[0]
        best_score = -float('inf')
        
        for move in moves:
            saved_state = self._save_state()
            self._make_move(move)
            
            score, _ = self.alpha_beta(depth - 1, -beta, -alpha)
            score = -score
            
            self._restore_state(saved_state)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            if score > alpha:
                alpha = score
            
            if alpha >= beta:
                break
        
        return best_score, best_move
    
    def get_best_move(self, max_depth: int = 3) -> str:
        moves = self.generate_legal_moves()
        
        if not moves:
            return None
        
        if len(moves) == 1:
            return moves[0]
        
        best_move = moves[0]
        for depth in range(1, max_depth + 1):
            score, move = self.alpha_beta(depth, -float('inf'), float('inf'))
            if move:
                best_move = move
        
        return best_move


def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    engine = ChessEngine()
    engine.set_position(pieces, to_play)
    
    piece_count = len(pieces)
    if piece_count > 28:
        depth = 2
    elif piece_count > 20:
        depth = 3
    else:
        depth = 4
    
    best_move = engine.get_best_move(depth)
    
    if best_move is None:
        engine.to_play = 'w' if to_play == 'white' else 'b'
        pseudo_moves = engine.generate_pseudo_legal_moves(engine.to_play)
        if pseudo_moves:
            best_move = pseudo_moves[0]
        else:
            best_move = 'a1a1'
    
    return best_move, memory
