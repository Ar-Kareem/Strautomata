
import random
import numpy as np

# Material values
MATERIAL_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables (from white's perspective)
# Positive values are good for white, negative for black
PAWN_TABLE = np.array([
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [ 50,  50,  50,  50,  50,  50,  50,  50],
    [ 10,  10,  20,  30,  30,  20,  10,  10],
    [  5,   5,  10,  25,  25,  10,   5,   5],
    [  0,   0,   0,  20,  20,   0,   0,   0],
    [  5,  -5, -10,   0,   0, -10,  -5,   5],
    [  5,  10,  10, -20, -20,  10,  10,   5],
    [  0,   0,   0,   0,   0,   0,   0,   0]
])

KNIGHT_TABLE = np.array([
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50]
])

BISHOP_TABLE = np.array([
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20]
])

ROOK_TABLE = np.array([
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [  5,  10,  10,  10,  10,  10,  10,   5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [  0,   0,   0,   5,   5,   0,   0,   0]
])

QUEEN_TABLE = np.array([
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [ -5,   0,   5,   5,   5,   5,   0,  -5],
    [  0,   0,   5,   5,   5,   5,   0,  -5],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [-10,   0,   5,   0,   0,   0,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20]
])

KING_TABLE = np.array([
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [ 20,  20,   0,   0,   0,   0,  20,  20],
    [ 20,  30,  10,   0,   0,  10,  30,  20]
])

KING_ENDGAME_TABLE = np.array([
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10,   0,   0, -10, -20, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -30,   0,   0,   0,   0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50]
])

def get_piece_value(piece_code):
    """Get the material value of a piece."""
    if not piece_code:
        return 0
    return MATERIAL_VALUES[piece_code[1]]

def get_piece_table_value(piece_code, square):
    """Get the piece-square table value for a piece on a square."""
    if not piece_code:
        return 0
    
    color = piece_code[0]
    piece_type = piece_code[1]
    
    # Convert square to coordinates
    file_idx = ord(square[0]) - ord('a')
    rank_idx = int(square[1]) - 1
    
    # Get the appropriate table
    if piece_type == 'P':
        table = PAWN_TABLE
    elif piece_type == 'N':
        table = KNIGHT_TABLE
    elif piece_type == 'B':
        table = BISHOP_TABLE
    elif piece_type == 'R':
        table = ROOK_TABLE
    elif piece_type == 'Q':
        table = QUEEN_TABLE
    elif piece_type == 'K':
        # Use different tables for endgame
        table = KING_TABLE if count_material(pieces) > 1200 else KING_ENDGAME_TABLE
    
    # Adjust for color
    if color == 'b':
        value = table[7-rank_idx][7-file_idx]
    else:
        value = table[rank_idx][file_idx]
    
    return value

def count_material(pieces):
    """Count total material on the board."""
    total = 0
    for piece in pieces.values():
        total += get_piece_value(piece)
    return total

def evaluate_position(pieces, to_play):
    """Evaluate the position from white's perspective."""
    score = 0
    
    # Material evaluation
    for square, piece in pieces.items():
        if piece[0] == 'w':
            score += get_piece_value(piece)
        else:
            score -= get_piece_value(piece)
    
    # Positional evaluation
    for square, piece in pieces.items():
        if piece[0] == 'w':
            score += get_piece_table_value(piece, square)
        else:
            score -= get_piece_table_value(piece, square)
    
    # Simple king safety
    # Penalize exposed kings
    w_king = find_king(pieces, 'w')
    b_king = find_king(pieces, 'b')
    
    # Simple mobility evaluation - count legal moves
    # This is a very rough approximation
    mobility_score = len(get_legal_moves(pieces, 'white', [])) - len(get_legal_moves(pieces, 'black', []))
    score += mobility_score
    
    return score

def find_king(pieces, color):
    """Find the king for the given color."""
    for square, piece in pieces.items():
        if piece == f'{color}K':
            return square
    return None

def get_legal_moves(pieces, color, legal_moves):
    """Get legal moves for the given color.
    This is a simplified version that just returns the provided legal_moves list.
    In a real implementation, we would need to generate all legal moves and validate them.
    """
    # Filter moves to only include those for the given color
    moves = []
    for move in legal_moves:
        from_square = move[:2]
        if from_square in pieces and pieces[from_square][0] == ('w' if color == 'white' else 'b'):
            moves.append(move)
    return moves

def apply_move(pieces, move):
    """Apply a move to the pieces dictionary and return the new state."""
    new_pieces = pieces.copy()
    from_square = move[:2]
    to_square = move[2:4]
    
    # Handle promotion
    if len(move) > 4:
        promotion_piece = move[4]
        piece = new_pieces[from_square][0] + promotion_piece.upper()
    else:
        piece = new_pieces[from_square]
    
    # Move the piece
    new_pieces[to_square] = piece
    del new_pieces[from_square]
    
    # Handle capture
    if to_square in new_pieces and new_pieces[to_square][0] != piece[0]:
        del new_pieces[to_square]
    
    return new_pieces

def minimax(pieces, depth, alpha, beta, maximizing_player, to_play, legal_moves):
    """Minimax search with alpha-beta pruning."""
    if depth == 0:
        return evaluate_position(pieces, to_play)
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in legal_moves:
            new_pieces = apply_move(pieces, move)
            new_legal_moves = get_legal_moves(new_pieces, 'white' if to_play == 'black' else 'black', [])
            eval_val = minimax(new_pieces, depth - 1, alpha, beta, False, 'black' if to_play == 'white' else 'white', new_legal_moves)
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            new_pieces = apply_move(pieces, move)
            new_legal_moves = get_legal_moves(new_pieces, 'white' if to_play == 'black' else 'black', [])
            eval_val = minimax(new_pieces, depth - 1, alpha, beta, True, 'black' if to_play == 'white' else 'white', new_legal_moves)
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    """Main policy function."""
    
    # Get legal moves for the current player
    legal_moves = memory.get('legal_moves', [])
    if not legal_moves:
        # If no legal moves provided, return a random move
        # This shouldn't happen in the arena, but just in case
        all_moves = list(memory.get('all_moves', []))
        if all_moves:
            return random.choice(all_moves), memory
        else:
            # Fallback - return a random move from the dictionary keys
            return random.choice(list(pieces.keys())), memory
    
    # Check for checkmate or stalemate
    if not legal_moves:
        return random.choice(list(pieces.keys())), memory
    
    # If there's only one legal move, return it
    if len(legal_moves) == 1:
        return legal_moves[0], memory
    
    # Determine search depth based on material
    material = count_material(pieces)
    if material > 1200:  # Opening/middlegame
        depth = 2
    else:  # Endgame
        depth = 3
    
    # Use minimax to find the best move
    best_move = None
    best_value = float('-inf') if to_play == 'white' else float('inf')
    
    for move in legal_moves:
        new_pieces = apply_move(pieces, move)
        new_legal_moves = get_legal_moves(new_pieces, 'black' if to_play == 'white' else 'white', [])
        move_value = minimax(new_pieces, depth, float('-inf'), float('inf'), 
                           to_play == 'white', 'black' if to_play == 'white' else 'white', new_legal_moves)
        
        if to_play == 'white':
            if move_value > best_value:
                best_value = move_value
                best_move = move
        else:
            if move_value < best_value:
                best_value = move_value
                best_move = move
    
    # Fallback to random move if no best move found
    if best_move is None:
        best_move = random.choice(legal_moves)
    
    return best_move, memory
