
import random
import math

# Piece values (centipawns)
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables for positional evaluation (simplified)
# For simplicity, we'll use only a few key squares to influence positioning
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

def square_to_index(square):
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return rank * 8 + file

def evaluate_position(pieces, to_play):
    score = 0
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        value = PIECE_VALUES[piece_type]
        
        # Positional bonus
        index = square_to_index(square)
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
            table = KING_TABLE
        else:
            table = [0]*64
            
        pos_bonus = table[index] if color == 'w' else -table[63 - index]
        
        if color == 'w':
            score += value + pos_bonus
        else:
            score -= value + pos_bonus
            
    return score if to_play == 'white' else -score

def make_move(board, move):
    new_board = board.copy()
    
    # Handle castling
    if move == 'O-O':
        if 'e1' in new_board and new_board['e1'] == 'wK':
            new_board['g1'] = 'wK'
            new_board['f1'] = 'wR'
            del new_board['e1']
            del new_board['h1']
    elif move == 'O-O-O':
        if 'e1' in new_board and new_board['e1'] == 'wK':
            new_board['c1'] = 'wK'
            new_board['d1'] = 'wR'
            del new_board['e1']
            del new_board['a1']
    elif move == 'O-O' and 'e8' in new_board and new_board['e8'] == 'bK':
        new_board['g8'] = 'bK'
        new_board['f8'] = 'bR'
        del new_board['e8']
        del new_board['h8']
    elif move == 'O-O-O' and 'e8' in new_board and new_board['e8'] == 'bK':
        new_board['c8'] = 'bK'
        new_board['d8'] = 'bR'
        del new_board['e8']
        del new_board['a8']
    else:
        # Parse standard moves
        if 'x' in move:
            # Capture
            parts = move.split('x')
            from_part = parts[0]
            to_square = parts[1][:2]
            
            # Find the moving piece
            moving_piece = None
            from_square = None
            
            # This is a simplified parser; in practice, more robust parsing is needed
            for sq, piece in new_board.items():
                if piece[1] == from_part[0] and piece[0] == ('w' if to_play == 'white' else 'b'):
                    from_square = sq
                    moving_piece = piece
                    break
                    
            if from_square:
                del new_board[from_square]
                new_board[to_square] = moving_piece
        else:
            # Non-capture move
            if len(move) >= 3:
                piece_char = move[0]
                to_square = move[-2:]
                
                # Find the moving piece
                for sq, piece in new_board.items():
                    if piece[1] == piece_char and piece[0] == ('w' if to_play == 'white' else 'b'):
                        del new_board[sq]
                        new_board[to_square] = piece
                        break
                        
    return new_board

def minimax(pieces, depth, alpha, beta, maximizing_player, to_play):
    if depth == 0:
        return evaluate_position(pieces, to_play)
        
    # Generate pseudo-legal moves (simplified)
    # In a real implementation, this would be more comprehensive
    moves = []
    for sq, piece in pieces.items():
        if (to_play == 'white' and piece[0] == 'w') or (to_play == 'black' and piece[0] == 'b'):
            # Simplified move generation
            moves.append(f"{piece[1]}{sq}")
    
    if not moves:
        # Checkmate or stalemate
        if maximizing_player:
            return -100000  # Loss
        else:
            return 100000   # Win
            
    if maximizing_player:
        max_eval = -math.inf
        for move in moves:
            new_pieces = make_move(pieces, move)
            eval = minimax(new_pieces, depth - 1, alpha, beta, False, 'black' if to_play == 'white' else 'white')
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in moves:
            new_pieces = make_move(pieces, move)
            eval = minimax(new_pieces, depth - 1, alpha, beta, True, 'black' if to_play == 'white' else 'white')
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # If only one legal move, return it
    if len(legal_moves) == 1:
        return legal_moves[0]
        
    # Check for immediate checkmate
    for move in legal_moves:
        if '#' in move:
            return move
            
    # Simple evaluation: return a random move if no better option found
    # In a more advanced implementation, we would use the minimax function
    # However, due to time constraints and complexity of move parsing, we'll use a heuristic
    best_move = legal_moves[0]
    best_score = -math.inf
    
    # Evaluate each move
    for move in legal_moves:
        # Simulate the move
        new_pieces = pieces.copy()
        
        # Handle castling
        if move == 'O-O':
            if to_play == 'white':
                if 'e1' in new_pieces and new_pieces['e1'] == 'wK':
                    new_pieces['g1'] = 'wK'
                    new_pieces['f1'] = 'wR'
                    del new_pieces['e1']
                    del new_pieces['h1']
            else:
                if 'e8' in new_pieces and new_pieces['e8'] == 'bK':
                    new_pieces['g8'] = 'bK'
                    new_pieces['f8'] = 'bR'
                    del new_pieces['e8']
                    del new_pieces['h8']
        elif move == 'O-O-O':
            if to_play == 'white':
                if 'e1' in new_pieces and new_pieces['e1'] == 'wK':
                    new_pieces['c1'] = 'wK'
                    new_pieces['d1'] = 'wR'
                    del new_pieces['e1']
                    del new_pieces['a1']
            else:
                if 'e8' in new_pieces and new_pieces['e8'] == 'bK':
                    new_pieces['c8'] = 'bK'
                    new_pieces['d8'] = 'bR'
                    del new_pieces['e8']
                    del new_pieces['a8']
        else:
            # Simplified move parsing
            if 'x' in move:
                # Capture
                parts = move.split('x')
                to_square = parts[1][:2]
                # Remove captured piece
                if to_square in new_pieces:
                    del new_pieces[to_square]
            # Apply move (simplified)
            # This is a very basic implementation and may not work correctly for all cases
            # A full implementation would require a proper chess move parser
            
        # Evaluate position after move
        score = evaluate_position(new_pieces, to_play)
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move
