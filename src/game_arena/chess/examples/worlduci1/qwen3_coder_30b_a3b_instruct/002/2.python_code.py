
import random
from typing import Dict, List

def policy(pieces: Dict[str, str], to_play: str) -> str:
    # Extract legal moves from the board state (simplified approach)
    # In a complete implementation, this would be provided by a chess library
    # For now, we'll return a move based on a simple heuristic
    
    # If we're playing as white, to_play is 'white', otherwise 'black'
    # For simplicity, we'll prioritize moves that capture high-value pieces
    # and avoid leaving king exposed
    
    # Get all pieces for our side
    my_pieces = {square: piece for square, piece in pieces.items() if piece[0] == to_play[0]}
    
    # Get all opponent pieces
    opponent_pieces = {square: piece for square, piece in pieces.items() if piece[0] != to_play[0]}
    
    # Simple scoring function
    def score_move(move: str) -> int:
        # Default score
        score = 0
        
        # Extract from and to squares
        from_square = move[:2]
        to_square = move[2:4]
        
        # Check if this move captures anything
        if to_square in pieces:
            captured_piece = pieces[to_square]
            piece_value = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}.get(captured_piece[1], 0)
            score += piece_value * 10  # Weight capturing by piece value
            
        # Simple positional scoring (basic)
        # Center control is generally good 
        center_squares = ['d4', 'd5', 'e4', 'e5']
        if to_square in center_squares:
            score += 5
        if from_square in center_squares:
            score -= 2  # Moving piece away from center is slightly bad
            
        # Avoid putting king in danger
        # Simplified: avoid moves to squares that are attacked by opponent
        # (Not complete, but basic idea)
        
        return score
    
    # For now, return a random legal move (since we don't have a proper legal moves list)
    # In a real implementation you'd have access to legal moves list
    
    # Simplified: prioritize moves that capture high-value pieces or are in center
    # Since we're not provided with legal moves, let's simulate with some basic moves
    
    # Generate some possible moves for demo
    possible_moves = []
    
    # Get all positions where we have pieces
    my_positions = list(my_pieces.keys())
    
    # Generate a couple moves for demo
    for pos in my_positions:
        # Simplified move generation
        file = pos[0]
        rank = pos[1]
        
        # Try moving one square forward or capturing diagonally
        if to_play == 'white':
            # Move forward
            new_rank = str(int(rank) + 1)
            if new_rank in '12345678':
                possible_moves.append(pos + file + new_rank)
            
            # Captures (simplified)
            if ord(file) > ord('a'):
                new_file = chr(ord(file) - 1)
                possible_moves.append(pos + new_file + new_rank)
            if ord(file) < ord('h'):
                new_file = chr(ord(file) + 1)
                possible_moves.append(pos + new_file + new_rank)
        else:  # Black
            new_rank = str(int(rank) - 1)
            if new_rank in '12345678':
                possible_moves.append(pos + file + new_rank)
            
            # Captures (simplified)
            if ord(file) > ord('a'):
                new_file = chr(ord(file) - 1)
                possible_moves.append(pos + new_file + new_rank)
            if ord(file) < ord('h'):
                new_file = chr(ord(file) + 1)
                possible_moves.append(pos + new_file + new_rank)
    
    # If there's a checkmate or capture move, use it
    # Simple heuristic for demo
    if possible_moves:
        # Score all possible moves
        move_scores = [(move, score_move(move)) for move in possible_moves]
        
        # Sort by score descending
        move_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Just pick one of the top moves
        return move_scores[0][0]
    
    # If no good move, just return a random one
    return random.choice(['e2e4', 'd2d4', 'f1c4', 'g1f3', 'b1c3', 'c1f4'] if to_play == 'white' else ['e7e5', 'd7d5', 'f8c5', 'g8f6', 'b8c6', 'c8f5'])
