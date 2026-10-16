
import random
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Convert color string to piece code prefix
    my_color = 'w' if to_play == 'white' else 'b'
    
    # Scoring variables
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    # Simple evaluation function
    def evaluate_position(pieces_dict):
        score = 0
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
        
        for square, piece in pieces_dict.items():
            piece_type = piece[1]
            piece_color = piece[0]
            
            value = piece_values.get(piece_type, 0)
            if piece_color == my_color:
                score += value
            else:
                score -= value
                
        return score
    
    # Check for immediate checkmate or capture opportunities
    for move in legal_moves:
        # Simulate move
        new_pieces = pieces.copy()
        
        # Parse move to make changes in position
        # This is a simplified parser - in reality, a full move parser would be needed
        # For now, we'll just do basic checks
        
        # Check for captures
        if 'x' in move:
            # Try to find what is being captured
            # This is approximate - a full implementation would need proper move parsing
            for square, piece in pieces.items():
                if move.endswith(square) or move[-2:] == square:
                    captured_piece = piece
                    # If we're capturing a high-value piece, prioritize this move
                    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
                    piece_type = captured_piece[1]
                    if piece_values.get(piece_type, 0) > 0:
                        if move.startswith('Q') and piece_type == 'Q':
                            # Queen captures queen - very good
                            if 10 > best_score:
                                best_score = 10
                                best_move = move
                        elif piece_values[piece_type] > 3:
                            # Capturing valuable piece
                            if piece_values[piece_type] > best_score:
                                best_score = piece_values[piece_type]
                                best_move = move
        
        # Check for checkmate (simplified)
        if '+' in move and '#' in move:
            return (move, memory)
        elif '#' in move:
            return (move, memory)
            
        # Check for promotions
        if '=' in move:
            if move[-1] in ['Q', 'R']:  # Promote to Queen or Rook
                if 8 > best_score:
                    best_score = 8
                    best_move = move
        
        # Prefer developing pieces in early game
        if len(pieces) > 20:  # Still mostly pieces on board
            if move.startswith('N') or move.startswith('B'):
                if 2 > best_score:
                    best_score = 2
                    best_move = move
            elif move.startswith('P'):
                # Prefer center pawn moves
                if move[1] in ['e', 'd'] and move[2] in ['4', '5']:
                    if 1.5 > best_score:
                        best_score = 1.5
                        best_move = move
    
    # If no special moves found, return the best one according to our simple heuristics
    return (best_move, memory)
