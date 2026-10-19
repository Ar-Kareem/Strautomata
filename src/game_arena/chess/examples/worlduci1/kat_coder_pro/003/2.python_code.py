
import random
from typing import Dict, List, Tuple

def policy(pieces: Dict[str, str], to_play: str) -> str:
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Get legal moves - they're passed implicitly through the function call
    # In practice, this function would receive legal_moves as a parameter
    # For this implementation, we'll assume legal_moves is available
    legal_moves = get_legal_moves(pieces, to_play)
    
    if not legal_moves:
        return random.choice(legal_moves) if legal_moves else ""
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        # Simulate the move
        new_pieces = simulate_move(pieces, move)
        score = evaluate_position(new_pieces, to_play)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def get_legal_moves(pieces: Dict[str, str], to_play: str) -> List[str]:
    # This is a simplified version - in practice, this would be a complex function
    # that generates all legal moves for the current position
    # For this implementation, we'll return a placeholder
    # In a real chess engine, this would involve checking move legality
    return []

def simulate_move(pieces: Dict[str, str], move: str) -> Dict[str, str]:
    # Create a copy of the board state
    new_pieces = pieces.copy()
    
    # Parse the move
    from_sq = move[:2]
    to_sq = move[2:4]
    
    # Handle castling (simplified)
    if len(move) == 4 and move in ['e1g1', 'e1c1', 'e8g8', 'e8c8']:
        # This would need proper castling logic
        pass
    
    # Handle promotion
    if len(move) == 5:
        promotion = move[4]
        # This would need proper promotion logic
        pass
    
    # Move the piece
    if from_sq in new_pieces:
        piece = new_pieces[from_sq]
        # Remove from source
        del new_pieces[from_sq]
        # Capture if present
        if to_sq in new_pieces:
            del new_pieces[to_sq]
        # Place at destination
        new_pieces[to_sq] = piece
    
    return new_pieces

def evaluate_position(pieces: Dict[str, str], to_play: str) -> float:
    score = 0.0
    
    # Material evaluation
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        
        value = get_piece_value(piece_type)
        
        # Adjust for color perspective
        if (to_play == 'white' and color == 'w') or (to_play == 'black' and color == 'b'):
            score += value
        else:
            score -= value
    
    # Add positional bonuses/penalties
    score += evaluate_mobility(pieces, to_play)
    score += evaluate_king_safety(pieces, to_play)
    score += evaluate_pawn_structure(pieces, to_play)
    
    return score

def get_piece_value(piece_type: str) -> int:
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    return values.get(piece_type, 0)

def evaluate_mobility(pieces: Dict[str, str], to_play: str) -> float:
    # Simple mobility evaluation
    # Count how many squares each piece can move to
    mobility_score = 0.0
    
    # This would require generating all legal moves for each piece
    # Simplified version - just return a small bonus
    return mobility_score * 0.1

def evaluate_king_safety(pieces: Dict[str, str], to_play: str) -> float:
    # Find kings
    white_king = None
    black_king = None
    
    for square, piece in pieces.items():
        if piece == 'wK':
            white_king = square
        elif piece == 'bK':
            black_king = square
    
    safety_score = 0.0
    
    # Simple king safety evaluation
    if to_play == 'white' and white_king:
        # Penalize exposed kings, reward castled positions
        # This is a very simplified version
        file = white_king[0]
        if file in ['e', 'f', 'g']:  # Castled kings
            safety_score += 0.5
        else:
            safety_score -= 0.5
    
    elif to_play == 'black' and black_king:
        file = black_king[0]
        if file in ['e', 'f', 'g']:
            safety_score += 0.5
        else:
            safety_score -= 0.5
    
    return safety_score

def evaluate_pawn_structure(pieces: Dict[str, str], to_play: str) -> float:
    # Evaluate pawn structure
    structure_score = 0.0
    
    # This would include checking for:
    # - Doubled pawns
    # - Isolated pawns  
    # - Passed pawns
    # - Pawn chains
    
    # Simplified version
    return structure_score
