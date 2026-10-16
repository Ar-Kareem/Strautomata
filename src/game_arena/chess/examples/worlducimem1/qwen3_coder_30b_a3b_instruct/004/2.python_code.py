
import random
from typing import Dict, List, Tuple, Optional
import re

def policy(pieces: Dict[str, str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    # Basic move selection policy with simple evaluation
    # Get legal moves from memory or generate empty list if not available
    legal_moves = memory.get('legal_moves', [])
    if not legal_moves and 'legal_moves' in memory:
        # If we have legal moves and it's an empty list, use provided moves
        legal_moves = memory['legal_moves']
    
    # Simplified move selection that prioritizes:
    # 1. Captures of high-value pieces
    # 2. Checkmate opportunities
    # 3. Pawn moves toward center
    # 4. King safety
    # 5. Piece development
    
    # Piece values: pawn=1, knight=3, bishop=3, rook=5, queen=9, king=1000
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 1000}
    
    # Helper function to get piece at square
    def get_piece_at(square):
        return pieces.get(square, None)
    
    # Helper function to get piece color
    def get_piece_color(piece):
        if piece:
            return piece[0]
        return None
    
    # Helper function to get piece type
    def get_piece_type(piece):
        if piece:
            return piece[1]
        return None
    
    # Function to evaluate if a move is a capture
    def is_capture(move_str):
        return len(move_str) == 4 and move_str[2:] in pieces
    
    # Function to evaluate if move is a pawn promotion
    def is_promotion(move_str):
        return len(move_str) > 4 and move_str[-1] in ['q', 'r', 'b', 'n']
    
    # Function to check if move results in checkmate (simple check)
    def is_checkmate(move_str):
        # For our simple policy, don't try to simulate full checkmate
        # Just evaluate captures of kings
        if len(move_str) == 4:
            target_square = move_str[2:4] 
            piece_at_target = get_piece_at(target_square)
            if piece_at_target and piece_at_target[1] == 'K':
                return True
        return False
    
    # Evaluate each move
    move_scores = []
    
    # If we have legal moves, score them
    if legal_moves:
        for move in legal_moves:
            score = 0
            
            # Check for checkmate or king capture
            if is_checkmate(move):
                score += 10000
            # Check for captures
            elif is_capture(move):
                target_square = move[2:4]
                captured_piece = get_piece_at(target_square)
                if captured_piece:
                    captured_type = get_piece_type(captured_piece)
                    captured_value = piece_values.get(captured_type, 0)
                    score += captured_value * 10
                    
            # Pawn promotion moves get a bonus
            if is_promotion(move):
                score += 50
                
            # Pawn moves toward center get some bonus
            if move[0] in 'defg' and move[2] in 'defg':
                score += 2
            
            # King safety considerations (avoid moves that expose king to checks)
            # Simplified - don't make moves that might expose king
            source_square = move[:2]
            target_square = move[2:4]
            
            piece = get_piece_at(source_square)
            
            # Prefer moves that don't move the king into danger
            if piece and piece[1] == 'K':
                score += 10
                
            # Prefer moves that develop knights and bishops
            if piece and piece[1] in ['N', 'B']:
                if move[2] in 'cd' or move[2] in 'ef':
                    score += 5
            
            # Prefer moves that are not just moving pieces to the same square
            if source_square != target_square:
                score += 1
                
            # Prefer moves in the center of the board when possible
            if move[0] in 'dfe' and move[2] in 'dfe':  
                if move[1] in '45' or move[3] in '45':
                    score += 2
                    
            move_scores.append((move, score))
    
    # Sort moves by score descending
    if move_scores:
        move_scores.sort(key=lambda x: x[1], reverse=True)
        best_move = move_scores[0][0]  # Select the best move
        return (best_move, memory)
    else:
        # Fallback: return a random legal move
        return (random.choice(legal_moves) if legal_moves else 'a1a1', memory)
