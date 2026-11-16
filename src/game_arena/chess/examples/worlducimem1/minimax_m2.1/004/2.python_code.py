
from typing import Dict, List, Tuple, Optional
import copy

# Piece values
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Pawn position tables (white perspective)
PAWN_TABLE_WHITE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

PAWN_TABLE_BLACK = list(reversed(PAWN_TABLE_WHITE))

# Knight position tables
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

# Bishop position tables
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

# Rook position tables
ROOK_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0,  5,
    0,  0,  0,  5,  5,  0,  0,  0
]

# Queen position tables
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

# King position tables (middlegame)
KING_TABLE_MIDDLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

# King position tables (endgame)
KING_TABLE_END = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]


def parse_square(square: str) -> Tuple[int, int]:
    """Convert algebraic notation to (file, rank) coordinates (0-7)"""
    file_char = square[0]
    rank_char = square[1]
    file_idx = ord(file_char) - ord('a')
    rank_idx = int(rank_char) - 1
    return (file_idx, rank_idx)


def square_to_index(square: str) -> int:
    """Convert algebraic notation to 0-63 index"""
    file_idx, rank_idx = parse_square(square)
    return rank_idx * 8 + file_idx


def index_to_square(idx: int) -> str:
    """Convert 0-63 index to algebraic notation"""
    file_idx = idx % 8
    rank_idx = idx // 8
    return chr(ord('a') + file_idx) + str(rank_idx + 1)


def get_piece_info(piece_code: str) -> Tuple[str, str]:
    """Extract color and type from piece code"""
    color = piece_code[0]  # 'w' or 'b'
    piece_type = piece_code[1]  # 'P', 'N', 'B', 'R', 'Q', 'K'
    return (color, piece_type)


def get_positional_bonus(piece_type: str, color: str, square: str) -> int:
    """Get positional bonus for a piece on a given square"""
    idx = square_to_index(square)
    
    if color == 'b':
        # Mirror for black pieces
        if piece_type == 'P':
            return PAWN_TABLE_BLACK[idx]
        elif piece_type in ['N', 'B']:
            # Mirror the knight/bishop table
            row, col = idx // 8, idx % 8
            mirrored_idx = row * 8 + (7 - col)
            if piece_type == 'N':
                return KNIGHT_TABLE[mirrored_idx]
            else:
                return BISHOP_TABLE[mirrored_idx]
        elif piece_type == 'R':
            row, col = idx // 8, idx % 8
            mirrored_idx = row * 8 + (7 - col)
            return ROOK_TABLE[mirrored_idx]
        elif piece_type == 'Q':
            row, col = idx // 8, idx % 8
            mirrored_idx = row * 8 + (7 - col)
            return QUEEN_TABLE[mirrored_idx]
        elif piece_type == 'K':
            # Determine if endgame based on material
            return KING_TABLE_MIDDLE[idx]  # Simplified
    else:
        if piece_type == 'P':
            return PAWN_TABLE_WHITE[idx]
        elif piece_type == 'N':
            return KNIGHT_TABLE[idx]
        elif piece_type == 'B':
            return BISHOP_TABLE[idx]
        elif piece_type == 'R':
            return ROOK_TABLE[idx]
        elif piece_type == 'Q':
            return QUEEN_TABLE[idx]
        elif piece_type == 'K':
            return KING_TABLE_MIDDLE[idx]
    
    return 0


def get_positional_bonus_endgame(piece_type: str, color: str, square: str) -> int:
    """Get endgame positional bonus for a piece on a given square"""
    idx = square_to_index(square)
    
    if color == 'b':
        row, col = idx // 8, idx % 8
        mirrored_idx = row * 8 + (7 - col)
        return KING_TABLE_END[mirrored_idx]
    else:
        return KING_TABLE_END[idx]


class BoardState:
    """Internal board representation"""
    
    def __init__(self, pieces: Dict[str, str]):
        self.board = {}  # (file, rank) -> piece_code
        self.pieces_by_color = {'white': {}, 'black': {}}
        
        for square, piece_code in pieces.items():
            file_idx, rank_idx = parse_square(square)
            self.board[(file_idx, rank_idx)] = piece_code
            
            color, ptype = get_piece_info(piece_code)
            color_name = 'white' if color == 'w' else 'black'
            self.pieces_by_color[color_name][square] = piece_code
    
    def get_piece(self, file_idx: int, rank_idx: int) -> Optional[str]:
        """Get piece at given coordinates"""
        return self.board.get((file_idx, rank_idx))
    
    def is_empty(self, file_idx: int, rank_idx: int) -> bool:
        """Check if square is empty"""
        return (file_idx, rank_idx) not in self.board
    
    def is_enemy(self, file_idx: int, rank_idx: int, my_color: str) -> bool:
        """Check if square contains enemy piece"""
        piece = self.get_piece(file_idx, rank_idx)
        if piece is None:
            return False
        piece_color, _ = get_piece_info(piece)
        return piece_color != my_color
    
    def is_friendly(self, file_idx: int, rank_idx: int, my_color: str) -> bool:
        """Check if square contains friendly piece"""
        piece = self.get_piece(file_idx, rank_idx)
        if piece is None:
            return False
        piece_color, _ = get_piece_info(piece)
        return piece_color == my_color
    
    def find_king(self, color: str) -> Optional[str]:
        """Find the square of the king of given color"""
        king_code = 'wK' if color == 'white' else 'bK'
        for square, piece in self.pieces_by_color[color].items():
            if piece == king_code:
                return square
        return None
    
    def is_square_attacked(self, square: str, by_color: str) -> bool:
        """Check if a square is attacked by a given color"""
        target_file, target_rank = parse_square(square)
        
        # Check pawn attacks
        pawn_dir = 1 if by_color == 'white' else -1
        for pawn_file in [target_file - 1, target_file + 1]:
            if 0 <= pawn_file <= 7:
                pawn_rank = target_rank - pawn_dir
                if 0 <= pawn_rank <= 7:
                    piece = self.get_piece(pawn_file, pawn_rank)
                    if piece == ('wP' if by_color == 'white' else 'bP'):
                        return True
        
        # Check knight attacks
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for df, dr in knight_moves:
            knight_file, knight_rank = target_file + df, target_rank + dr
            if 0 <= knight_file <= 7 and 0 <= knight_rank <= 7:
                piece = self.get_piece(knight_file, knight_rank)
                if piece == ('wN' if by_color == 'white' else 'bN'):
                    return True
        
        # Check king attacks
        king_moves = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1),  (1, 0), (1, 1)
        ]
        for df, dr in king_moves:
            king_file, king_rank = target_file + df, target_rank + dr
            if 0 <= king_file <= 7 and 0 <= king_rank <= 7:
                piece = self.get_piece(king_file, king_rank)
                if piece == ('wK' if by_color == 'white' else 'bK'):
                    return True
        
        # Check sliding attacks (rook/queen)
        rook_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for df, dr in rook_dirs:
            curr_file, curr_rank = target_file + df, target_rank + dr
            while 0 <= curr_file <= 7 and 0 <= curr_rank <= 7:
                piece = self.get_piece(curr_file, curr_rank)
                if piece is not None:
                    ptype = piece[1]
                    if ptype in ['R', 'Q']:
                        piece_color = piece[0]
                        if (piece_color == 'w') == (by_color == 'white'):
                            return True
                    break
                curr_file += df
                curr_rank += dr
        
        # Check sliding attacks (bishop/queen)
        bishop_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for df, dr in bishop_dirs:
            curr_file, curr_rank = target_file + df, target_rank + dr
            while 0 <= curr_file <= 7 and 0 <= curr_rank <= 7:
                piece = self.get_piece(curr_file, curr_rank)
                if piece is not None:
                    ptype = piece[1]
                    if ptype in ['B', 'Q']:
                        piece_color = piece[0]
                        if (piece_color == 'w') == (by_color == 'white'):
                            return True
                    break
                curr_file += df
                curr_rank += dr
        
        return False
    
    def is_in_check(self, color: str) -> bool:
        """Check if the king of given color is in check"""
        king_square = self.find_king(color)
        if king_square is None:
            return False
        enemy_color = 'black' if color == 'white' else 'white'
        return self.is_square_attacked(king_square, enemy_color)
    
    def make_move(self, move: str) -> 'BoardState':
        """Create a new board state after making a move"""
        new_pieces = copy.deepcopy(self.pieces_by_color)
        
        from_square = move[:2]
        to_square = move[2:4]
        promotion = move[4] if len(move) > 4 else None
        
        # Get piece info
        piece = new_pieces['white' if self.pieces_by_color['white'].get(from_square) else 'black'][from_square]
        
        # Remove from old square
        color = 'white' if piece[0] == 'w' else 'black'
        del new_pieces[color][from_square]
        
        # Handle capture
        enemy_color = 'black' if color == 'white' else 'white'
        if to_square in new_pieces[enemy_color]:
            del new_pieces[enemy_color][to_square]
        
        # Handle promotion
        if promotion and piece[1] == 'P':
            piece = piece[0] + promotion
        
        # Place on new square
        new_pieces[color][to_square] = piece
        
        # Handle castling (move rook)
        if piece[1] == 'K' and abs(ord(from_square[0]) - ord(to_square[0])) == 2:
            if to_square == 'g1':  # White kingside
                rook = new_pieces['white']['h1']
                del new_pieces['white']['h1']
                new_pieces['white']['f1'] = rook
            elif to_square == 'c1':  # White queenside
                rook = new_pieces['white']['a1']
                del new_pieces['white']['a1']
                new_pieces['white']['d1'] = rook
            elif to_square == 'g8':  # Black kingside
                rook = new_pieces['black']['h8']
                del new_pieces['black']['h8']
                new_pieces['black']['f8'] = rook
            elif to_square == 'c8':  # Black queenside
                rook = new_pieces['black']['a8']
                del new_pieces['black']['a8']
                new_pieces['black']['d8'] = rook
        
        # Build pieces dict
        pieces_dict = {}
        for color_name in ['white', 'black']:
            prefix = 'w' if color_name == 'white' else 'b'
            for square, piece_code in new_pieces[color_name].items():
                pieces_dict[square] = piece_code
        
        return BoardState(pieces_dict)


def generate_pseudo_legal_moves(board: BoardState, color: str) -> List[str]:
    """Generate all pseudo-legal moves for the given color"""
    moves = []
    my_color = 'w' if color == 'white' else 'b'
    
    # Get all pieces of this color
    pieces = board.pieces_by_color[color]
    
    for square, piece_code in pieces.items():
        piece_type = piece_code[1]
        file_idx, rank_idx = parse_square(square)
        
        if piece_type == 'P':
            moves.extend(generate_pawn_moves(board, square, file_idx, rank_idx, my_color))
        elif piece_type == 'N':
            moves.extend(generate_knight_moves(board, square, file_idx, rank_idx, my_color))
        elif piece_type == 'B':
            moves.extend(generate_sliding_moves(board, square, file_idx, rank_idx, my_color, [(1, 1), (1, -1), (-1, 1), (-1, -1)]))
        elif piece_type == 'R':
            moves.extend(generate_sliding_moves(board, square, file_idx, rank_idx, my_color, [(1, 0), (-1, 0), (0, 1), (0, -1)]))
        elif piece_type == 'Q':
            moves.extend(generate_sliding_moves(board, square, file_idx, rank_idx, my_color, [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]))
        elif piece_type == 'K':
            moves.extend(generate_king_moves(board, square, file_idx, rank_idx, my_color))
    
    return moves


def generate_pawn_moves(board: BoardState, square: str, file_idx: int, rank_idx: int, color: str) -> List[str]:
    """Generate pawn moves"""
    moves = []
    direction = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    
    # Forward move
    new_rank = rank_idx + direction
    if 0 <= new_rank <= 7 and board.is_empty(file_idx, new_rank):
        # Check for promotion
        if new_rank == 0 or new_rank == 7:
            for promo in ['q', 'r', 'b', 'n']:
                moves.append(f"{square}{chr(ord('a') + file_idx)}{new_rank + 1}{promo}")
        else:
            moves.append(f"{square}{chr(ord('a') + file_idx)}{new_rank + 1}")
        
        # Double move from start
        if rank_idx == start_rank:
            double_rank = rank_idx + 2 * direction
            if board.is_empty(file_idx, double_rank):
                moves.append(f"{square}{chr(ord('a') + file_idx)}{double_rank + 1}")
    
    # Captures
    for df in [-1, 1]:
        new_file = file_idx + df
        if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
            if board.is_enemy(new_file, new_rank, color):
                # Check for promotion
                if new_rank == 0 or new_rank == 7:
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(f"{square}{chr(ord('a') + new_file)}{new_rank + 1}{promo}")
                else:
                    moves.append(f"{square}{chr(ord('a') + new_file)}{new_rank + 1}")
    
    return moves


def generate_knight_moves(board: BoardState, square: str, file_idx: int, rank_idx: int, color: str) -> List[str]:
    """Generate knight moves"""
    moves = []
    knight_offsets = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1)
    ]
    
    for df, dr in knight_offsets:
        new_file, new_rank = file_idx + df, rank_idx + dr
        if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
            if not board.is_friendly(new_file, new_rank, color):
                moves.append(f"{square}{chr(ord('a') + new_file)}{new_rank + 1}")
    
    return moves


def generate_sliding_moves(board: BoardState, square: str, file_idx: int, rank_idx: int, color: str, directions: List[Tuple[int, int]]) -> List[str]:
    """Generate sliding moves for bishop, rook, queen"""
    moves = []
    
    for df, dr in directions:
        new_file, new_rank = file_idx + df, rank_idx + dr
        while 0 <= new_file <= 7 and 0 <= new_rank <= 7:
            if board.is_friendly(new_file, new_rank, color):
                break
            moves.append(f"{square}{chr(ord('a') + new_file)}{new_rank + 1}")
            if board.is_enemy(new_file, new_rank, color):
                break
            new_file += df
            new_rank += dr
    
    return moves


def generate_king_moves(board: BoardState, square: str, file_idx: int, rank_idx: int, color: str) -> List[str]:
    """Generate king moves including castling"""
    moves = []
    king_offsets = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)
    ]
    
    for df, dr in king_offsets:
        new_file, new_rank = file_idx + df, rank_idx + dr
        if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
            if not board.is_friendly(new_file, new_rank, color):
                moves.append(f"{square}{chr(ord('a') + new_file)}{new_rank + 1}")
    
    # Castling (simplified - doesn't check if king has moved or if squares are attacked)
    king_square = board.find_king('white' if color == 'w' else 'black')
    if king_square:
        fk, rk = parse_square(king_square)
        # Kingside
        if color == 'w':
            if board.get_piece(5, 0) is None and board.get_piece(6, 0) is None:
                if board.get_piece(7, 0) == 'wR':
                    moves.append("e1g1")
            # Queenside
            if board.get_piece(1, 0) is None and board.get_piece(2, 0) is None and board.get_piece(3, 0) is None:
                if board.get_piece(0, 0) == 'wR':
                    moves.append("e1c1")
        else:
            if board.get_piece(5, 7) is None and board.get_piece(6, 7) is None:
                if board.get_piece(7, 7) == 'bR':
                    moves.append("e8g8")
            if board.get_piece(1, 7) is None and board.get_piece(2, 7) is None and board.get_piece(3, 7) is None:
                if board.get_piece(0, 7) == 'bR':
                    moves.append("e8c8")
    
    return moves


def is_move_legal(board: BoardState, move: str, color: str) -> bool:
    """Check if a move is legal (doesn't leave king in check)"""
    new_board = board.make_move(move)
    return not new_board.is_in_check(color)


def evaluate_position(board: BoardState, color: str) -> float:
    """Evaluate position from the perspective of the given color"""
    score = 0
    enemy_color = 'black' if color == 'white' else 'white'
    my_color_code = 'w' if color == 'white' else 'b'
    enemy_color_code = 'b' if color == 'white' else 'w'
    
    # Count material and calculate positional score
    my_material = 0
    enemy_material = 0
    
    # Check for endgame (simplified: no queens or few pieces)
    total_pieces = len(board.pieces_by_color['white']) + len(board.pieces_by_color['black'])
    is_endgame = total_pieces <= 10 or ('Q' not in ''.join(board.pieces_by_color['white'].values()) and 
                                         'Q' not in ''.join(board.pieces_by_color['black'].values()))
    
    for square, piece_code in board.pieces_by_color[color].items():
        piece_type = piece_code[1]
        value = PIECE_VALUES[piece_type]
        
        # Add positional bonus
        if is_endgame and piece_type == 'K':
            value += get_positional_bonus_endgame(piece_type, my_color_code, square)
        else:
            value += get_positional_bonus(piece_type, my_color_code, square)
        
        my_material += value
    
    for square, piece_code in board.pieces_by_color[enemy_color].items():
        piece_type = piece_code[1]
        value = PIECE_VALUES[piece_type]
        
        # Add positional bonus (negative because it's enemy)
        if is_endgame and piece_type == 'K':
            value += get_positional_bonus_endgame(piece_type, enemy_color_code, square)
        else:
            value += get_positional_bonus(piece_type, enemy_color_code, square)
        
        enemy_material += value
    
    # Return score from color's perspective
    if color == 'white':
        return my_material - enemy_material
    else:
        return enemy_material - my_material


def policy(pieces: dict, to_play: str, memory: dict) -> Tuple[str, dict]:
    """
    Chess move selection policy
    
    Args:
        pieces: Dictionary mapping squares to piece codes
        to_play: 'white' or 'black'
        memory: Dictionary for storing state between calls
    
    Returns:
        Tuple of (best_move, updated_memory)
    """
    # Parse board state
    board = BoardState(pieces)
    
    # Generate all pseudo-legal moves
    pseudo_moves = generate_pseudo_moves(board, to_play)
    
    # Filter to get only legal moves
    legal_moves = [move for move in pseudo_moves if is_move_legal(board, move, to_play)]
    
    if not legal_moves:
        # No legal moves - should handle checkmate/stalemate
        return '', memory
    
    # Evaluate all legal moves
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        new_board = board.make_move(move)
        score = evaluate_position(new_board, to_play)
        
        # Add a small random factor to break ties
        score += 0.01
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory
