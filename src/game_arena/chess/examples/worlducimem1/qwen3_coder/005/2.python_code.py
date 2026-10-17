
import numpy as np

# Piece values
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables (simplified)
PAWN_TABLE = np.array([
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
])

KNIGHT_TABLE = np.array([
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
])

BISHOP_TABLE = np.array([
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
])

ROOK_TABLE = np.array([
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
])

QUEEN_TABLE = np.array([
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
])

KING_TABLE = np.array([
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
])

def square_to_index(square):
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return rank * 8 + file

def get_piece_value(piece):
    return PIECE_VALUES.get(piece[1], 0)

def evaluate_position(pieces, player_color):
    score = 0
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        value = get_piece_value(piece)
        
        # Determine if the piece belongs to the player
        if color == ('w' if player_color == 'white' else 'b'):
            score += value
        else:
            score -= value
            
        # Add piece-square table bonus
        index = square_to_index(square)
        if piece_type == 'P':
            table = PAWN_TABLE if color == 'w' else PAWN_TABLE[::-1]
            score += table[index] if color == 'w' else -table[index]
        elif piece_type == 'N':
            score += KNIGHT_TABLE[index] if color == 'w' else -KNIGHT_TABLE[index]
        elif piece_type == 'B':
            score += BISHOP_TABLE[index] if color == 'w' else -BISHOP_TABLE[index]
        elif piece_type == 'R':
            score += ROOK_TABLE[index] if color == 'w' else -ROOK_TABLE[index]
        elif piece_type == 'Q':
            score += QUEEN_TABLE[index] if color == 'w' else -QUEEN_TABLE[index]
        elif piece_type == 'K':
            score += KING_TABLE[index] if color == 'w' else -KING_TABLE[index]
            
    return score

def is_in_check(pieces, player_color):
    # Simplified check detection - not fully implemented but can be extended
    return False

def minimax(pieces, depth, alpha, beta, maximizing_player, player_color, legal_moves):
    if depth == 0:
        return evaluate_position(pieces, player_color), None
    
    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        for move in legal_moves:
            new_pieces = make_move(pieces, move)
            eval_score, _ = minimax(new_pieces, depth - 1, alpha, beta, False, player_color, get_legal_moves(new_pieces, 'black' if player_color == 'white' else 'white'))
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
        for move in legal_moves:
            new_pieces = make_move(pieces, move)
            eval_score, _ = minimax(new_pieces, depth - 1, alpha, beta, True, player_color, get_legal_moves(new_pieces, 'black' if player_color == 'white' else 'white'))
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def make_move(pieces, move):
    new_pieces = pieces.copy()
    from_square = move[:2]
    to_square = move[2:4]
    if from_square in new_pieces:
        piece = new_pieces[from_square]
        del new_pieces[from_square]
        # Handle promotion
        if len(move) > 4:
            promoted_piece = move[4].upper()
            new_pieces[to_square] = piece[0] + promoted_piece
        else:
            new_pieces[to_square] = piece
    return new_pieces

def get_legal_moves(pieces, player_color):
    # In a real implementation, this would generate all legal moves
    # For this simplified version, we'll just return a placeholder
    # But in the actual policy function, we'll use the provided legal_moves list
    return []

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Get legal moves from memory (assuming they are stored there by the game engine)
    legal_moves = memory.get('legal_moves', [])
    
    if not legal_moves:
        # Fallback: return a random move if no legal moves are provided
        return 'e2e4', {}
    
    # If only one legal move, return it
    if len(legal_moves) == 1:
        return legal_moves[0], memory
    
    # Evaluate each move using minimax
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        new_pieces = make_move(pieces, move)
        # Evaluate the position after the move
        score = evaluate_position(new_pieces, to_play)
        # Prefer captures
        if move[2:4] in pieces:
            captured_piece_value = get_piece_value(pieces[move[2:4]])
            score += captured_piece_value * 0.5  # Encourage captures
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # If we found a good move, return it
    if best_move:
        return best_move, memory
    
    # Fallback to first legal move
    return legal_moves[0], memory
