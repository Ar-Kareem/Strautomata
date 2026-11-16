
import random
from typing import Dict, List

PIECE_VALUES = {
    'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1,
    'q': -9, 'r': -5, 'b': -3, 'n': -3, 'p': -1
}

CENTER_SQUARES = {'d4', 'e4', 'd5', 'e5'}

def policy(pieces: Dict[str, str], to_play: str) -> str:
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    # Generate all legal moves
    legal_moves = get_legal_moves(pieces, color)
    if not legal_moves:
        return ''  # should never happen as we're called only with legal moves
    
    # Check for checkmate moves first
    for move in legal_moves:
        new_pieces = simulate_move(pieces, move, color)
        if is_checkmate(new_pieces, opponent_color):
            return move
    
    # Evaluate all legal moves
    scored_moves = []
    for move in legal_moves:
        score = evaluate_move(pieces, move, color)
        scored_moves.append((score, move))
    
    # Find the best score
    max_score = max(score for score, _ in scored_moves)
    best_moves = [move for score, move in scored_moves if score == max_score]
    
    # Return random among best moves
    return random.choice(best_moves)

def evaluate_move(pieces: Dict[str, str], move: str, color: str) -> float:
    """Evaluate a move based on material, position, and other factors."""
    score = 0.0
    
    # Material gain
    new_pieces = simulate_move(pieces, move, color)
    material_diff = calculate_material(new_pieces, color) - calculate_material(pieces, color)
    score += material_diff * 10  # prioritize material gains
    
    # Positional bonuses
    dest = move[2:4]
    if dest in CENTER_SQUARES:
        score += 0.5
    
    # King safety (penalize moving king unless castling)
    piece_moved = pieces.get(move[:2])
    if piece_moved and piece_moved[1] == 'K':
        if abs(ord(move[0]) - ord(move[2])) <= 1:  # not castling
            score -= 1
    
    # Development bonus for moving pieces from starting squares
    if piece_moved:
        start_rank = '1' if color == 'w' else '8'
        if move[1] == start_rank:
            score += 0.3
    
    return score

def simulate_move(pieces: Dict[str, str], move: str, color: str) -> Dict[str, str]:
    """Return new pieces dict after making the move."""
    new_pieces = pieces.copy()
    src, dest = move[:2], move[2:4]
    
    # Handle promotion
    promotion = move[4] if len(move) > 4 else None
    piece = pieces[src]
    
    # Remove captured piece if any
    if dest in new_pieces:
        del new_pieces[dest]
    
    # Move the piece
    del new_pieces[src]
    if promotion:
        new_pieces[dest] = color + promotion.upper()
    else:
        new_pieces[dest] = piece
    
    return new_pieces

def calculate_material(pieces: Dict[str, str], color: str) -> int:
    """Calculate total material for given color."""
    total = 0
    for piece in pieces.values():
        if piece[0] == color:
            total += PIECE_VALUES.get(piece[1], 0)
    return total

def is_checkmate(pieces: Dict[str, str], opponent_color: str) -> bool:
    """Check if the opponent is in checkmate."""
    # Simplified check - in a real implementation this would need to verify:
    # 1. King is in check
    # 2. No legal moves exist
    # For this simplified version, we'll just check if king is captured
    king_exists = any(p[1] == 'K' and p[0] == opponent_color for p in pieces.values())
    return not king_exists

def get_legal_moves(pieces: Dict[str, str], color: str) -> List[str]:
    """Generate all legal moves for the given color."""
    # In a real implementation, this would generate all possible legal moves
    # For this example, we'll return a simplified set of pseudo-legal moves
    moves = []
    for square, piece in pieces.items():
        if piece[0] != color:
            continue
            
        piece_type = piece[1]
        x, y = ord(square[0]) - ord('a'), int(square[1]) - 1
        
        if piece_type == 'P':  # Pawn
            # Forward moves
            direction = 1 if color == 'w' else -1
            new_y = y + direction
            if 0 <= new_y < 8:
                new_square = f"{chr(x + ord('a'))}{new_y + 1}"
                if new_square not in pieces:
                    moves.append(f"{square}{new_square}")
                    # Double move from starting position
                    if (color == 'w' and y == 1) or (color == 'b' and y == 6):
                        new_y2 = y + 2 * direction
                        new_square2 = f"{chr(x + ord('a'))}{new_y2 + 1}"
                        if new_square2 not in pieces:
                            moves.append(f"{square}{new_square2}")
                
                # Captures
                for dx in [-1, 1]:
                    new_x = x + dx
                    if 0 <= new_x < 8:
                        new_square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                        if new_square in pieces and pieces[new_square][0] != color:
                            moves.append(f"{square}{new_square}")
        
        elif piece_type == 'N':  # Knight
            for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    new_square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                    if new_square not in pieces or pieces[new_square][0] != color:
                        moves.append(f"{square}{new_square}")
        
        # Add similar logic for other pieces (omitted for brevity)
        # In a real implementation, this would include all piece movement rules
        
    return moves
