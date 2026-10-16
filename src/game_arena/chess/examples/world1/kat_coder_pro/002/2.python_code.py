
import numpy as np

# Piece values
PIECE_VALUES = {
    'P': 100, 'N': 300, 'B': 300, 'R': 500, 'Q': 900, 'K': 2000
}

# Board size
BOARD_SIZE = 8

def get_piece_value(piece_code):
    """Get the value of a piece."""
    if piece_code == '':  # Empty square
        return 0
    return PIECE_VALUES[piece_code[1]]

def get_color(piece_code):
    """Get the color of a piece."""
    if piece_code == '':
        return None
    return piece_code[0]

def get_piece_type(piece_code):
    """Get the type of a piece."""
    if piece_code == '':
        return None
    return piece_code[1]

def is_valid_square(square):
    """Check if a square is valid."""
    file, rank = square[0], square[1]
    return 'a' <= file <= 'h' and '1' <= rank <= '8'

def get_directions(piece_type):
    """Get the movement directions for a piece type."""
    directions = {
        'P': [],  # Pawns have special movement rules
        'N': [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
        'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
        'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
        'Q': [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)],
        'K': [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    }
    return directions[piece_type]

def get_pawn_moves(square, color, pieces):
    """Get possible moves for a pawn."""
    file, rank = square[0], int(square[1])
    moves = []
    
    # Forward move
    forward_rank = rank + (1 if color == 'w' else -1)
    forward_square = f"{file}{forward_rank}"
    if is_valid_square(forward_square) and pieces.get(forward_square, '') == '':
        moves.append(forward_square)
        
        # Double move from starting position
        if (color == 'w' and rank == 2) or (color == 'b' and rank == 7):
            double_rank = rank + (2 if color == 'w' else -2)
            double_square = f"{file}{double_rank}"
            if is_valid_square(double_square) and pieces.get(double_square, '') == '':
                moves.append(double_square)
    
    # Captures
    for file_offset in [-1, 1]:
        capture_file = chr(ord(file) + file_offset)
        capture_rank = rank + (1 if color == 'w' else -1)
        capture_square = f"{capture_file}{capture_rank}"
        if is_valid_square(capture_square):
            target_piece = pieces.get(capture_square, '')
            if target_piece != '' and get_color(target_piece) != color:
                moves.append(capture_square)
    
    return moves

def get_knight_moves(square, pieces):
    """Get possible moves for a knight."""
    file, rank = square[0], int(square[1])
    moves = []
    
    for file_offset, rank_offset in get_directions('N'):
        new_file = chr(ord(file) + file_offset)
        new_rank = rank + rank_offset
        new_square = f"{new_file}{new_rank}"
        if is_valid_square(new_square):
            target_piece = pieces.get(new_square, '')
            if target_piece == '' or get_color(target_piece) != get_color(pieces[square]):
                moves.append(new_square)
    
    return moves

def get_sliding_moves(square, color, piece_type, pieces):
    """Get possible moves for sliding pieces (B, R, Q)."""
    file, rank = square[0], int(square[1])
    moves = []
    
    for file_offset, rank_offset in get_directions(piece_type):
        new_file, new_rank = file, rank
        while True:
            new_file = chr(ord(new_file) + file_offset)
            new_rank = new_rank + rank_offset
            new_square = f"{new_file}{new_rank}"
            if not is_valid_square(new_square):
                break
            
            target_piece = pieces.get(new_square, '')
            if target_piece == '':
                moves.append(new_square)
            elif get_color(target_piece) != color:
                moves.append(new_square)
                break
            else:
                break
    
    return moves

def get_king_moves(square, pieces):
    """Get possible moves for a king."""
    file, rank = square[0], int(square[1])
    moves = []
    
    for file_offset, rank_offset in get_directions('K'):
        new_file = chr(ord(file) + file_offset)
        new_rank = rank + rank_offset
        new_square = f"{new_file}{new_rank}"
        if is_valid_square(new_square):
            target_piece = pieces.get(new_square, '')
            if target_piece == '' or get_color(target_piece) != get_color(pieces[square]):
                moves.append(new_square)
    
    return moves

def get_piece_moves(square, pieces):
    """Get all possible moves for a piece on a given square."""
    piece_code = pieces[square]
    if piece_code == '':
        return []
    
    color = get_color(piece_code)
    piece_type = get_piece_type(piece_code)
    
    if piece_type == 'P':
        return get_pawn_moves(square, color, pieces)
    elif piece_type == 'N':
        return get_knight_moves(square, pieces)
    elif piece_type in ['B', 'R', 'Q']:
        return get_sliding_moves(square, color, piece_type, pieces)
    elif piece_type == 'K':
        return get_king_moves(square, pieces)
    else:
        return []

def is_in_check(pieces, color):
    """Check if the king of the given color is in check."""
    # Find the king
    king_square = None
    for square, piece in pieces.items():
        if piece == f"{color}K":
            king_square = square
            break
    
    if king_square is None:
        return False
    
    # Check if any opponent piece can attack the king
    opponent_color = 'w' if color == 'b' else 'b'
    for square, piece in pieces.items():
        if piece != '' and get_color(piece) == opponent_color:
            if king_square in get_piece_moves(square, pieces):
                return True
    
    return False

def evaluate_position(pieces, color):
    """Evaluate the position for the given color."""
    score = 0
    
    # Material score
    for piece in pieces.values():
        if piece != '':
            piece_value = get_piece_value(piece)
            if get_color(piece) == color:
                score += piece_value
            else:
                score -= piece_value
    
    # Piece activity
    opponent_color = 'w' if color == 'b' else 'b'
    for square, piece in pieces.items():
        if piece != '' and get_color(piece) == color:
            score += len(get_piece_moves(square, pieces))
        elif piece != '' and get_color(piece) == opponent_color:
            score -= len(get_piece_moves(square, pieces))
    
    # King safety
    if is_in_check(pieces, color):
        score -= 100
    if is_in_check(pieces, opponent_color):
        score += 100
    
    return score

def apply_move(pieces, move):
    """Apply a move to the board and return the new pieces dict."""
    # Simple move parsing - assumes standard algebraic notation
    # This is a simplified version and may not handle all chess move notations
    if 'x' in move:
        # Capture move
        source, target = move.split('x')
        if '=' in target:
            # Promotion
            target, promotion = target.split('=')
            pieces[target] = f"{get_color(pieces[source])}{promotion}"
        else:
            pieces[target] = pieces[source]
        del pieces[source]
    else:
        # Regular move
        if '=' in move:
            # Promotion
            source, target_promotion = move.split('=')
            target, promotion = target_promotion.split('')
            pieces[target] = f"{get_color(pieces[source])}{promotion}"
            del pieces[source]
        else:
            # Regular move
            source, target = move[:2], move[2:]
            pieces[target] = pieces[source]
            del pieces[source]
    
    return pieces

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """Select the best move based on position evaluation."""
    color = 'w' if to_play == 'white' else 'b'
    
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        # Apply the move to get the resulting position
        new_pieces = pieces.copy()
        new_pieces = apply_move(new_pieces, move)
        
        # Evaluate the resulting position
        score = evaluate_position(new_pieces, color)
        
        # Update best move if this score is better
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
