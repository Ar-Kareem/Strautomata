
# Chess AI Policy with Minimax Search and Alpha-Beta Pruning
import itertools

def policy(pieces: dict[str, str], to_play: str) -> str:
    """
    Select the best move using alpha-beta search with a strong evaluation function.
    
    Args:
        pieces: Dictionary mapping squares to piece codes (e.g., {'e1': 'bK', 'f3': 'wR'})
        to_play: 'white' or 'black'
    
    Returns:
        A UCI move string (e.g., 'e2e4', 'a7a8q')
    """
    # Convert pieces to board representation
    board = parse_board(pieces)
    
    # Generate all legal moves
    legal_moves = generate_all_moves(board, to_play)
    
    if not legal_moves:
        # No legal moves - return empty string (shouldn't happen if we generate correctly)
        return ''
    
    # Check for checkmate - if any move gives checkmate, take it
    for move in legal_moves:
        if is_checkmate(board, move, to_play):
            return move
    
    # Use iterative deepening with alpha-beta search
    depth = 1
    best_move = legal_moves[0]  # Default to first move
    
    import time
    start_time = time.time()
    time_limit = 0.9  # Leave some buffer
    
    while time.time() - start_time < time_limit:
        try:
            _, best_move = alpha_beta_search(board, depth, -float('inf'), float('inf'), 
                                           to_play, True, legal_moves, start_time, time_limit)
        except TimeoutError:
            break
        depth += 1
    
    return best_move


class Board:
    """Internal board representation for move generation and evaluation."""
    
    def __init__(self, pieces=None):
        # 8x8 board, None for empty, otherwise (color, piece_type)
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.to_move = 'white'
        self.castling_rights = {'white_kingside': True, 'white_queenside': True,
                               'black_kingside': True, 'black_queenside': True}
        self.en_passant_square = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        
        if pieces:
            self.set_from_pieces(pieces)
    
    def set_from_pieces(self, pieces):
        """Initialize board from pieces dictionary."""
        for square, piece_code in pieces.items():
            file_idx = ord(square[0]) - ord('a')
            rank_idx = int(square[1]) - 1
            color = 'white' if piece_code[0] == 'w' else 'black'
            piece_type = piece_code[1]
            self.board[7 - rank_idx][file_idx] = (color, piece_type)
    
    def get_piece(self, row, col):
        """Get piece at row, col (0-indexed from white's perspective)."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def set_piece(self, row, col, piece):
        """Set piece at row, col."""
        if 0 <= row < 8 and 0 <= col < 8:
            self.board[row][col] = piece
    
    def find_king(self, color):
        """Find the king of the given color."""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece[0] == color and piece[1] == 'K':
                    return row, col
        return None
    
    def is_empty(self, row, col):
        """Check if square is empty."""
        return self.get_piece(row, col) is None
    
    def is_enemy(self, row, col, color):
        """Check if square contains enemy piece."""
        piece = self.get_piece(row, col)
        return piece and piece[0] != color


# Piece values for evaluation
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables (from white's perspective)
# Opening/middle game tables
PAWN_PST = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_PST = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_PST = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_PST = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_PST = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MIDDLEGAME_PST = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

KING_ENDGAME_PST = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

# Mirror tables for black (since we evaluate from white's perspective)
def mirror_table(table):
    """Mirror table for black pieces."""
    mirrored = [0] * 64
    for row in range(8):
        for col in range(8):
            idx = row * 8 + col
            mirrored_idx = (7 - row) * 8 + col
            mirrored[mirrored_idx] = table[idx]
    return mirrored

PAWN_PST_BLACK = mirror_table(PAWN_PST)
KNIGHT_PST_BLACK = mirror_table(KNIGHT_PST)
BISHOP_PST_BLACK = mirror_table(BISHOP_PST)
ROOK_PST_BLACK = mirror_table(ROOK_PST)
QUEEN_PST_BLACK = mirror_table(QUEEN_PST)
KING_MIDDLEGAME_PST_BLACK = mirror_table(KING_MIDDLEGAME_PST)
KING_ENDGAME_PST_BLACK = mirror_table(KING_ENDGAME_PST)


def parse_board(pieces):
    """Create a Board object from the pieces dictionary."""
    board = Board()
    board.set_from_pieces(pieces)
    return board


def generate_all_moves(board, to_play):
    """Generate all legal moves for the current player."""
    moves = []
    
    for row in range(8):
        for col in range(8):
            piece = board.get_piece(row, col)
            if piece and piece[0] == to_play:
                piece_moves = generate_moves_for_piece(board, row, col, piece[1], to_play)
                moves.extend(piece_moves)
    
    # Filter to only legal moves (moves that don't leave king in check)
    legal_moves = []
    for move in moves:
        if is_legal_move(board, move, to_play):
            legal_moves.append(move)
    
    return legal_moves


def generate_moves_for_piece(board, row, col, piece_type, color):
    """Generate pseudo-legal moves for a single piece."""
    moves = []
    
    if piece_type == 'P':
        moves.extend(generate_pawn_moves(board, row, col, color))
    elif piece_type == 'N':
        moves.extend(generate_knight_moves(board, row, col, color))
    elif piece_type == 'B':
        moves.extend(generate_sliding_moves(board, row, col, color, [(1, 1), (1, -1), (-1, 1), (-1, -1)]))
    elif piece_type == 'R':
        moves.extend(generate_sliding_moves(board, row, col, color, [(1, 0), (-1, 0), (0, 1), (0, -1)]))
    elif piece_type == 'Q':
        moves.extend(generate_sliding_moves(board, row, col, color, 
                                           [(1, 0), (-1, 0), (0, 1), (0, -1),
                                            (1, 1), (1, -1), (-1, 1), (-1, -1)]))
    elif piece_type == 'K':
        moves.extend(generate_king_moves(board, row, col, color))
    
    return moves


def generate_pawn_moves(board, row, col, color):
    """Generate pawn moves."""
    moves = []
    direction = -1 if color == 'white' else 1
    start_row = 6 if color == 'white' else 1
    
    # Forward move
    new_row = row + direction
    if 0 <= new_row < 8 and board.is_empty(new_row, col):
        moves.append(f"{sq_to_algebraic(row, col)}{sq_to_algebraic(new_row, col)}")
        
        # Double move from start
        if row == start_row:
            double_row = row + 2 * direction
            if board.is_empty(double_row, col):
                moves.append(f"{sq_to_algebraic(row, col)}{sq_to_algebraic(double_row, col)}")
        
        # Promotion
        if new_row == 0 or new_row == 7:
            for promo in ['q', 'r', 'b', 'n']:
                moves[-1] = moves[-1] + promo
    
    # Captures
    for dc in [-1, 1]:
        new_col = col + dc
        if 0 <= new_col < 8:
            new_row = row + direction
            if 0 <= new_row < 8 and board.is_enemy(new_row, new_col, color):
                move = f"{sq_to_algebraic(row, col)}{sq_to_algebraic(new_row, new_col)}"
                # Promotion
                if new_row == 0 or new_row == 7:
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(move + promo)
                else:
                    moves.append(move)
    
    return moves


def generate_knight_moves(board, row, col, color):
    """Generate knight moves."""
    moves = []
    offsets = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    
    for dr, dc in offsets:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board.is_empty(new_row, new_col) or board.is_enemy(new_row, new_col, color):
                moves.append(f"{sq_to_algebraic(row, col)}{sq_to_algebraic(new_row, new_col)}")
    
    return moves


def generate_sliding_moves(board, row, col, color, directions):
    """Generate sliding moves (bishop, rook, queen)."""
    moves = []
    
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        while 0 <= new_row < 8 and 0 <= new_col < 8:
            if board.is_empty(new_row, new_col):
                moves.append(f"{sq_to_algebraic(row, col)}{sq_to_algebraic(new_row, new_col)}")
            else:
                if board.is_enemy(new_row, new_col, color):
                    moves.append(f"{sq_to_algebraic(row, col)}{sq_to_algebraic(new_row, new_col)}")
                break
            new_row += dr
            new_col += dc
    
    return moves


def generate_king_moves(board, row, col, color):
    """Generate king moves including castling."""
    moves = []
    offsets = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    
    for dr, dc in offsets:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board.is_empty(new_row, new_col) or board.is_enemy(new_row, new_col, color):
                moves.append(f"{sq_to_algebraic(row, col)}{sq_to_algebraic(new_row, new_col)}")
    
    # Castling
    moves.extend(generate_castling_moves(board, row, col, color))
    
    return moves


def generate_castling_moves(board, row, col, color):
    """Generate castling moves."""
    moves = []
    
    # Check king position
    if color == 'white':
        if row != 7 or col != 4:
            return moves
        # Kingside
        if board.castling_rights.get('white_kingside', False):
            if (board.is_empty(7, 5) and board.is_empty(7, 6) and
                not is_square_attacked(board, 7, 4, 'black') and
                not is_square_attacked(board, 7, 5, 'black') and
                not is_square_attacked(board, 7, 6, 'black')):
                moves.append('e1g1')
        # Queenside
        if board.castling_rights.get('white_queenside', False):
            if (board.is_empty(7, 1) and board.is_empty(7, 2) and board.is_empty(7, 3) and
                not is_square_attacked(board, 7, 4, 'black') and
                not is_square_attacked(board, 7, 2, 'black') and
                not is_square_attacked(board, 7, 3, 'black')):
                moves.append('e1c1')
    else:
        if row != 0 or col != 4:
            return moves
        # Kingside
        if board.castling_rights.get('black_kingside', False):
            if (board.is_empty(0, 5) and board.is_empty(0, 6) and
                not is_square_attacked(board, 0, 4, 'white') and
                not is_square_attacked(board, 0, 5, 'white') and
                not is_square_attacked(board, 0, 6, 'white')):
                moves.append('e8g8')
        # Queenside
        if board.castling_rights.get('black_queenside', False):
            if (board.is_empty(0, 1) and board.is_empty(0, 2) and board.is_empty(0, 3) and
                not is_square_attacked(board, 0, 4, 'white') and
                not is_square_attacked(board, 0, 2, 'white') and
                not is_square_attacked(board, 0, 3, 'white')):
                moves.append('e8c8')
    
    return moves


def is_square_attacked(board, row, col, by_color):
    """Check if a square is attacked by the given color."""
    enemy_color = 'white' if by_color == 'black' else 'black'
    
    # Check pawn attacks
    pawn_dir = -1 if by_color == 'white' else 1
    for dc in [-1, 1]:
        new_row, new_col = row + pawn_dir, col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            piece = board.get_piece(new_row, new_col)
            if piece and piece[0] == by_color and piece[1] == 'P':
                return True
    
    # Check knight attacks
    knight_offsets = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    for dr, dc in knight_offsets:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            piece = board.get_piece(new_row, new_col)
            if piece and piece[0] == by_color and piece[1] == 'N':
                return True
    
    # Check king attacks
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                piece = board.get_piece(new_row, new_col)
                if piece and piece[0] == by_color and piece[1] == 'K':
                    return True
    
    # Check sliding pieces (rook/queen for straight, bishop/queen for diagonal)
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        while 0 <= new_row < 8 and 0 <= new_col < 8:
            piece = board.get_piece(new_row, new_col)
            if piece:
                if piece[0] == by_color and piece[1] in ['R', 'Q']:
                    return True
                break
            new_row += dr
            new_col += dc
    
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        while 0 <= new_row < 8 and 0 <= new_col < 8:
            piece = board.get_piece(new_row, new_col)
            if piece:
                if piece[0] == by_color and piece[1] in ['B', 'Q']:
                    return True
                break
            new_row += dr
            new_col += dc
    
    return False


def is_in_check(board, color):
    """Check if the king of the given color is in check."""
    king_pos = board.find_king(color)
    if not king_pos:
        return False
    row, col = king_pos
    enemy_color = 'white' if color == 'black' else 'black'
    return is_square_attacked(board, row, col, enemy_color)


def is_legal_move(board, move, color):
    """Check if a move is legal (doesn't leave king in check)."""
    # Make temporary move
    temp_board = make_temp_move(board, move)
    return not is_in_check(temp_board, color)


def make_temp_move(board, move):
    """Make a temporary copy of the board with the move applied."""
    new_board = Board()
    new_board.board = [row[:] for row in board.board]
    new_board.to_move = 'black' if board.to_move == 'white' else 'white'
    new_board.castling_rights = board.castling_rights.copy()
    new_board.en_passant_square = board.en_passant_square
    new_board.halfmove_clock = board.halfmove_clock
    new_board.fullmove_number = board.fullmove_number
    
    # Parse move
    from_sq = algebraic_to_sq(move[:2])
    to_sq = algebraic_to_sq(move[2:4])
    
    from_row, from_col = from_sq
    to_row, to_col = to_sq
    
    piece = new_board.get_piece(from_row, from_col)
    
    # Handle promotion
    if len(move) > 4:
        promo_piece = move[4]
        piece = (piece[0], promo_piece.upper())
    
    # Handle en passant capture
    if piece[1] == 'P' and (to_row, to_col) == board.en_passant_square:
        capture_row = from_row
        capture_col = to_col
        new_board.set_piece(capture_row, capture_col, None)
    
    # Move piece
    new_board.set_piece(from_row, from_col, None)
    new_board.set_piece(to_row, to_col, piece)
    
    # Handle castling
    if piece[1] == 'K' and abs(from_col - to_col) == 2:
        if to_col == 6:  # Kingside
            rook_from = (from_row, 7)
            rook_to = (from_row, 5)
        else:  # Queenside
            rook_from = (from_row, 0)
            rook_to = (from_row, 3)
        
        rook = new_board.get_piece(rook_from[0], rook_from[1])
        new_board.set_piece(rook_from[0], rook_from[1], None)
        new_board.set_piece(rook_to[0], rook_to[1], rook)
    
    return new_board


def is_checkmate(board, move, color):
    """Check if a move results in checkmate."""
    temp_board = make_temp_move(board, move)
    enemy_color = 'black' if color == 'white' else 'white'
    
    if not is_in_check(temp_board, enemy_color):
        return False
    
    # Check if enemy has any legal moves
    enemy_moves = generate_all_moves(temp_board, enemy_color)
    return len(enemy_moves) == 0


def sq_to_algebraic(row, col):
    """Convert row, col to algebraic notation."""
    file_char = chr(ord('a') + col)
    rank_char = str(8 - row)
    return file_char + rank_char


def algebraic_to_sq(square):
    """Convert algebraic notation to row, col."""
    col = ord(square[0]) - ord('a')
    row = 8 - int(square[1])
    return row, col


def evaluate_board(board, to_move):
    """
    Evaluate the board from the perspective of the player to move.
    Positive values favor white, negative values favor black.
    """
    if to_move == 'white':
        perspective = 1
    else:
        perspective = -1
    
    # Check for checkmate
    if is_in_check(board, 'white') and not generate_all_moves(board, 'white'):
        return -20000 * perspective
    if is_in_check(board, 'black') and not generate_all_moves(board, 'black'):
        return 20000 * perspective
    
    # Count material and positioning
    white_material = 0
    black_material = 0
    white_positional = 0
    black_positional = 0
    
    # Determine game phase
    total_material = 0
    piece_counts = {'P': 0, 'N': 0, 'B': 0, 'R': 0, 'Q': 0}
    
    for row in range(8):
        for col in range(8):
            piece = board.get_piece(row, col)
            if piece:
                color, piece_type = piece
                value = PIECE_VALUES.get(piece_type, 0)
                total_material += value
                if piece_type in piece_counts:
                    piece_counts[piece_type] += 1
                
                if color == 'white':
                    white_material += value
                    white_positional += get_pst_value(piece_type, row, col, 'white', total_material)
                else:
                    black_material += value
                    black_positional += get_pst_value(piece_type, row, col, 'black', total_material)
    
    # Pawn structure evaluation
    white_pawn_eval = evaluate_pawn_structure(board, 'white')
    black_pawn_eval = evaluate_pawn_structure(board, 'black')
    
    # King safety evaluation
    white_king_safety = evaluate_king_safety(board, 'white', total_material)
    black_king_safety = evaluate_king_safety(board, 'black', total_material)
    
    # Combine evaluations
    material_diff = white_material - black_material
    positional_diff = white_positional - black_positional
    
    eval_score = material_diff + positional_diff
    eval_score += (white_pawn_eval - black_pawn_eval)
    eval_score += (white_king_safety - black_king_safety)
    
    # Adjust for side to move
    return eval_score * perspective


def get_pst_value(piece_type, row, col, color, total_material):
    """Get piece-square table value."""
    idx = row * 8 + col
    
    if color == 'white':
        if piece_type == 'P':
            return PAWN_PST[idx]
        elif piece_type == 'N':
            return KNIGHT_PST[idx]
        elif piece_type == 'B':
            return BISHOP_PST[idx]
        elif piece_type == 'R':
            return ROOK_PST[idx]
        elif piece_type == 'Q':
            return QUEEN_PST[idx]
        elif piece_type == 'K':
            if total_material > 3000:  # Middle game
                return KING_MIDDLEGAME_PST[idx]
            else:  # Endgame
                return KING_ENDGAME_PST[idx]
    else:
        if piece_type == 'P':
            return PAWN_PST_BLACK[idx]
        elif piece_type == 'N':
            return KNIGHT_PST_BLACK[idx]
        elif piece_type == 'B':
            return BISHOP_PST_BLACK[idx]
        elif piece_type == 'R':
            return ROOK_PST_BLACK[idx]
        elif piece_type == 'Q':
            return QUEEN_PST_BLACK[idx]
        elif piece_type == 'K':
            if total_material > 3000:
                return KING_MIDDLEGAME_PST_BLACK[idx]
            else:
                return KING_ENDGAME_PST_BLACK[idx]
    
    return 0


def evaluate_pawn_structure(board, color):
    """Evaluate pawn structure for a given color."""
    score = 0
    pawns = []
    
    # Find all pawns
    for row in range(8):
        for col in range(8):
            piece = board.get_piece(row, col)
            if piece and piece[0] == color and piece[1] == 'P':
                pawns.append((row, col))
    
    # Check for isolated pawns
    for row, col in pawns:
        has_support = False
        for dr in [-1, 1]:
            neighbor_col = col + dr
            for r in range(8):
                piece = board.get_piece(r, neighbor_col)
                if piece and piece[0] == color and piece[1] == 'P':
                    has_support = True
                    break
        
        if not has_support:
            score -= 20
    
    # Check for doubled pawns
    for col in range(8):
        pawns_in_file = [p for p in pawns if p[1] == col]
        if len(pawns_in_file) > 1:
            score -= 10 * (len(pawns_in_file) - 1)
    
    # Check for backward pawns
    for row, col in pawns:
        direction = -1 if color == 'white' else 1
        # Check if pawn can be supported
        can_be_supported = False
        for dc in [-1, 1]:
            check_row = row - direction
            check_col = col + dc
            if 0 <= check_row < 8 and 0 <= check_col < 8:
                piece = board.get_piece(check_row, check_col)
                if piece and piece[0] == color and piece[1] == 'P':
                    can_be_supported = True
                    break
        
        # Check if squares in front are attacked by enemy pawns
        pawn_attacked = False
        enemy_direction = 1 if color == 'white' else -1
        for dc in [-1, 1]:
            attack_row = row + enemy_direction
            attack_col = col + dc
            if 0 <= attack_row < 8 and 0 <= attack_col < 8:
                piece = board.get_piece(attack_row, attack_col)
                enemy_color = 'black' if color == 'white' else 'white'
                if piece and piece[0] == enemy_color and piece[1] == 'P':
                    pawn_attacked = True
                    break
        
        if not can_be_supported and pawn_attacked:
            score -= 15
    
    return score


def evaluate_king_safety(board, color, total_material):
    """Evaluate king safety."""
    king_pos = board.find_king(color)
    if not king_pos:
        return 0
    
    row, col = king_pos
    enemy_color = 'black' if color == 'white' else 'white'
    
    # Count attackers
    attackers = 0
    attack_value = 0
    
    # Check each direction for attackers
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    for dr, dc in directions:
        distance = 0
        new_row, new_col = row + dr, col + dc
        while 0 <= new_row < 8 and 0 <= new_col < 8:
            distance += 1
            piece = board.get_piece(new_row, new_col)
            if piece:
                if piece[0] == enemy_color:
                    if piece[1] in ['R', 'Q'] and distance <= 8:
                        attackers += 1
                        attack_value += 5
                    elif piece[1] in ['B', 'Q'] and distance <= 8:
                        attackers += 1
                        attack_value += 5
                    elif piece[1] == 'N' and distance <= 2:
                        attackers += 1
                        attack_value += 10
                break
            new_row += dr
            new_col += dc
    
    # Count protective pieces
    protectors = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                piece = board.get_piece(new_row, new_col)
                if piece and piece[0] == color and piece[1] in ['P', 'N', 'B', 'R', 'Q']:
                    protectors += 1
    
    # Calculate safety score
    safety_score = 0
    if attackers > 0:
        safety_score -= attack_value * (attackers - protectors)
    
    # Pawn shield evaluation
    pawn_shield = 0
    pawn_direction = -1 if color == 'white' else 1
    for dc in [-1, 0, 1]:
        shield_row = row + pawn_direction
        shield_col = col + dc
        if 0 <= shield_row < 8 and 0 <= shield_col < 8:
            piece = board.get_piece(shield_row, shield_col)
            if piece and piece[0] == color and piece[1] == 'P':
                pawn_shield += 5
    
    safety_score += pawn_shield
    
    return safety_score


class TimeoutError(Exception):
    pass


def alpha_beta_search(board, depth, alpha, beta, to_play, is_maximizing, 
                      legal_moves, start_time, time_limit):
    """
    Alpha-beta search with iterative deepening and time checking.
    """
    if time.time() - start_time > time_limit:
        raise TimeoutError()
    
    if depth == 0:
        return evaluate_board(board, to_play), None
    
    # Get moves for current position
    if is_maximizing:
        current_moves = generate_all_moves(board, to_play)
    else:
        enemy = 'black' if to_play == 'white' else 'white'
        current_moves = generate_all_moves(board, enemy)
    
    if not current_moves:
        # Check for checkmate or stalemate
        if is_in_check(board, to_play):
            return -20000 + depth, None  # Checkmate
        else:
            return 0, None  # Stalemate
    
    # Order moves for better pruning
    ordered_moves = order_moves(current_moves, board, to_play)
    
    if is_maximizing:
        best_move = None
        max_eval = -float('inf')
        for move in ordered_moves:
            new_board = make_temp_move(board, move)
            enemy = 'black' if to_play == 'white' else 'white'
            eval_score, _ = alpha_beta_search(new_board, depth - 1, alpha, beta, 
                                             enemy, False, legal_moves, start_time, time_limit)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for move in ordered_moves:
            new_board = make_temp_move(board, move)
            enemy = 'black' if to_play == 'white' else 'white'
            eval_score, _ = alpha_beta_search(new_board, depth - 1, alpha, beta, 
                                             enemy, True, legal_moves, start_time, time_limit)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        return min_eval, best_move


def order_moves(moves, board, to_play):
    """Order moves to improve alpha-beta pruning efficiency."""
    scored_moves = []
    
    for move in moves:
        score = 0
        
        # Capture moves get high priority
        from_sq = algebraic_to_sq(move[:2])
        to_sq = algebraic_to_sq(move[2:4])
        from_row, from_col = from_sq
        to_row, to_col = to_sq
        
        captured_piece = board.get_piece(to_row, to_col)
        moving_piece = board.get_piece(from_row, from_col)
        
        if captured_piece:
            capture_score = PIECE_VALUES.get(captured_piece[1], 0)
            moving_score = PIECE_VALUES.get(moving_piece[1], 0)
            score += capture_score * 10 - moving_score
        
        # Check moves get bonus
        temp_board = make_temp_move(board, move)
        enemy = 'black' if to_play == 'white' else 'white'
        if is_in_check(temp_board, enemy):
            score += 50
        
        # Promotion gets bonus
        if len(move) > 4:
            score += 100
        
        # Castling gets bonus
        if moving_piece and moving_piece[1] == 'K' and abs(from_col - to_col) == 2:
            score += 30
        
        scored_moves.append((score, move))
    
    # Sort by score descending
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    return [m[1] for m in scored_moves]


# For debugging and testing
if __name__ == "__main__":
    # Test with a simple position
    test_pieces = {
        'e1': 'wK', 'e8': 'bK', 'd4': 'wQ'
    }
    result = policy(test_pieces, 'white')
    print(f"Recommended move: {result}")
