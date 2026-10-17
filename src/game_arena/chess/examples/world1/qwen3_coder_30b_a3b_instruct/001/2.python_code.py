
import random
from typing import Dict, List, Tuple

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 1000}
    
    # Map piece colors
    color_map = {'white': 'w', 'black': 'b'}
    my_color = color_map[to_play]
    opponent_color = 'b' if my_color == 'w' else 'w'
    
    # Look for checkmate moves first
    for move in legal_moves:
        if move.endswith('+') or move.endswith('#'):
            return move
    
    # Look for captures and prioritize them
    captures = []
    non_captures = []
    promotions = []
    
    for move in legal_moves:
        if 'x' in move:
            captures.append(move)
        elif '=' in move:
            promotions.append(move)
        else:
            non_captures.append(move)
    
    # Order captures by piece value captured (prefer higher value pieces)
    capture_scores = []
    for move in captures:
        # Find the captured piece
        if 'x' in move:
            captured_piece = None
            for square, piece in pieces.items():
                if piece.startswith(opponent_color) and square in move:
                    captured_piece = piece[1]
                    break
            if captured_piece:
                score = piece_values.get(captured_piece, 0)
            else:
                score = 0
        else:
            score = 0
        capture_scores.append((move, score))
    
    # Sort captures by value
    capture_scores.sort(key=lambda x: x[1], reverse=True)
    ordered_captures = [move for move, _ in capture_scores]
    
    # Prioritize promotions (especially to queen)
    queen_promotions = [move for move in promotions if '=Q' in move]
    other_promotions = [move for move in promotions if '=Q' not in move]
    
    # Build final move list: (checks + captures + promotions + others)
    final_moves = []
    
    # Checkmate moves already handled above
    
    # Add captures sorted by value
    final_moves.extend(ordered_captures)
    
    # Add queen promotions (strongest promotions)
    final_moves.extend(queen_promotions)
    
    # Add other promotions
    final_moves.extend(other_promotions)
    
    # Add non-capture moves
    final_moves.extend(non_captures)
    
    # Prefer moves that develop pieces toward center or control center
    # Prefer knight moves early and center control
    # Just pick the first in our ordered list for simplicity
    if final_moves:
        return final_moves[0]
    else:
        # Fallback: ensure we return a legal move
        return legal_moves[0]
