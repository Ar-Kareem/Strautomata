
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    A simple chess policy that evaluates moves based on material gain and positional factors.
    
    Args:
        pieces: Dictionary mapping squares to piece codes (e.g., {'e1': 'wK', 'e4': 'bP'})
        to_play: String indicating whose turn it is ('white' or 'black')
        legal_moves: List of legal move strings
        memory: Dictionary for storing information between calls
    
    Returns:
        Tuple of (move_string, updated_memory)
    """
    
    # Initialize memory if empty
    if not memory:
        memory['move_count'] = 0
        memory['side'] = to_play
    
    memory['move_count'] += 1
    
    # Piece values for material evaluation
    piece_values = {
        'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
    }
    
    # Center squares for positional evaluation
    center_squares = ['d4', 'd5', 'e4', 'e5']
    
    def evaluate_position():
        """Evaluate the current position from the perspective of the player to move"""
        score = 0
        for square, piece in pieces.items():
            if not piece:
                continue
                
            color, piece_type = piece[0], piece[1]
            value = piece_values[piece_type]
            
            # Material score (positive for our pieces, negative for opponent)
            if (color == 'w' and memory['side'] == 'white') or (color == 'b' and memory['side'] == 'black'):
                score += value
            else:
                score -= value
                
            # Center control bonus
            if square in center_squares and piece_type in ['N', 'B', 'P']:
                if (color == 'w' and memory['side'] == 'white') or (color == 'b' and memory['side'] == 'black'):
                    score += 10
                else:
                    score -= 10
        
        return score
    
    def evaluate_move(move):
        """Evaluate a move based on material gain and positional factors"""
        score = 0
        
        # Check for captures
        if 'x' in move:
            # Extract target square from capture move
            target_square = move.split('x')[1].split('+')[0].split('#')[0]
            if target_square in pieces:
                captured_piece = pieces[target_square]
                if captured_piece:
                    captured_value = piece_values[captured_piece[1]]
                    score += captured_value
        
        # Check for promotions
        if '=Q' in move or '=R' in move or '=B' in move or '=N' in move:
            score += 800  # Promotion bonus
        
        # Castling bonus
        if move in ['O-O', 'O-O-O']:
            score += 50
        
        # Check for checks
        if move.endswith('+'):
            score += 20
        
        # Check for mates
        if move.endswith('#'):
            score += 10000
        
        return score
    
    # Evaluate all moves
    move_scores = []
    for move in legal_moves:
        score = evaluate_move(move)
        move_scores.append((score, move))
    
    # Sort by score (highest first)
    move_scores.sort(reverse=True, key=lambda x: x[0])
    
    # If we have multiple moves with the same highest score, choose randomly
    # to add some variation
    max_score = move_scores[0][0]
    best_moves = [move for score, move in move_scores if score == max_score]
    
    selected_move = random.choice(best_moves)
    
    return selected_move, memory
