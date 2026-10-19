
import numpy as np

def policy(pieces, to_play, memory):
    # Initialize piece values
    piece_values = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
    
    # Generate all possible moves
    legal_moves = generate_legal_moves(pieces, to_play)
    
    # First check for immediate checkmate
    for move in legal_moves:
        new_pieces = make_move(pieces, move, to_play)
        if is_checkmate(new_pieces, opposite_color(to_play)):
            return move, {}
    
    # If no checkmate, perform minimax search
    best_move = None
    best_eval = -np.inf
    opponent = opposite_color(to_play)
    
    for move in legal_moves:
        # Apply move
        new_pieces = make_move(pieces, move, to_play)
        
        # Get opponent's possible responses
        opponent_moves = generate_legal_moves(new_pieces, opponent)
        
        # Find opponent's best response
        worst_eval = np.inf
        for opp_move in opponent_moves:
            opp_pieces = make_move(new_pieces, opp_move, opponent)
            eval = evaluate_position(opp_pieces, to_play)
            if eval < worst_eval:
                worst_eval = eval
        
        # Update our best move
        if worst_eval > best_eval:
            best_eval = worst_eval
            best_move = move
    
    return best_move if best_move else legal_moves[0], {}

def generate_legal_moves(pieces, color):
    # This is a simplified legal move generator for the example
    # In a real implementation, you would need to properly generate all legal moves
    # considering checks, castling, en passant, etc.
    
    moves = []
    for square, piece in pieces.items():
        if piece[0] != color[0].lower():
            continue
            
        piece_type = piece[1]
        file, rank = square[0], int(square[1])
        
        if piece_type == 'P':
            # Pawn moves (simplified)
            direction = 1 if color == 'white' else -1
            new_rank = rank + direction
            if 1 <= new_rank <= 8:
                new_square = f"{file}{new_rank}"
                if new_square not in pieces:
                    moves.append(f"{square}{new_square}")
                # Captures
                for delta in [-1, 1]:
                    new_file = chr(ord(file) + delta)
                    if 'a' <= new_file <= 'h':
                        new_square = f"{new_file}{new_rank}"
                        if new_square in pieces and pieces[new_square][0] != color[0].lower():
                            moves.append(f"{square}{new_square}")
                
        elif piece_type == 'N':
            # Knight moves
            for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
                new_file = chr(ord(file) + dx)
                new_rank = rank + dy
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    new_square = f"{new_file}{new_rank}"
                    if new_square not in pieces or pieces[new_square][0] != color[0].lower():
                        moves.append(f"{square}{new_square}")
        
        # Similar logic for other pieces would go here
    
    return moves

def make_move(pieces, move, color):
    # Create a new pieces dictionary with the move applied
    new_pieces = pieces.copy()
    start = move[:2]
    end = move[2:4]
    
    # Handle promotion
    if len(move) > 4:
        promoted_piece = move[4]
        new_pieces[end] = color[0].lower() + promoted_piece.upper()
    else:
        new_pieces[end] = new_pieces[start]
    
    del new_pieces[start]
    return new_pieces

def opposite_color(color):
    return 'black' if color == 'white' else 'white'

def is_checkmate(pieces, color):
    # Simplified - should actually check if king is in check and no legal moves
    return False

def evaluate_position(pieces, color):
    # Basic evaluation function
    score = 0
    
    # Material
    for piece in pieces.values():
        value = piece_values[piece[1]]
        if piece[0] == color[0].lower():
            score += value
        else:
            score -= value
    
    # Count number of pieces (mobility bonus)
    our_pieces = sum(1 for p in pieces.values() if p[0] == color[0].lower())
    their_pieces = len(pieces) - our_pieces
    score += 0.1 * (our_pieces - their_pieces)
    
    return score
