
import numpy as np
from typing import Dict, List, Tuple, Optional

def policy(pieces: Dict[str, str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    # Convert to_play to color code
    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'
    
    # Piece values (Queen=9, Rook=5, Bishop=3, Knight=3, Pawn=1)
    piece_values = {
        'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1,
        'q': 9, 'r': 5, 'b': 3, 'n': 3, 'p': 1
    }
    
    # Center squares
    center_squares = {'d4', 'd5', 'e4', 'e5'}
    
    # Helper to get square from algebraic notation
    def square_to_coords(square):
        return (ord(square[0]) - ord('a'), int(square[1]) - 1)
    
    def coords_to_square(row, col):
        return chr(ord('a') + row) + str(col + 1)
    
    # Get all legal moves (simplified approach - just list all valid moves)
    # In a real implementation, we'd have a move generator
    
    # Generate all possible moves just for evaluation
    legal_moves = []
    for square, piece in pieces.items():
        if piece[0] != color:
            continue
        piece_type = piece[1]
        row, col = square_to_coords(square)
        
        # For simplicity, just simulate potential moves based on piece type
        # In practice, you'd have full move generation logic
        if piece_type == 'P':  # Pawn
            # Forward moves
            if color == 'w':
                if col < 7:
                    new_square = coords_to_square(row, col + 1)
                    if new_square not in pieces:
                        legal_moves.append(square + new_square)
                        # Promotion
                        if col + 1 == 7:
                            legal_moves.append(square + new_square + 'q')
                            legal_moves.append(square + new_square + 'r')
                            legal_moves.append(square + new_square + 'b')
                            legal_moves.append(square + new_square + 'n')
            else:
                if col > 0:
                    new_square = coords_to_square(row, col - 1)
                    if new_square not in pieces:
                        legal_moves.append(square + new_square)
                        # Promotion
                        if col - 1 == 0:
                            legal_moves.append(square + new_square + 'q')
                            legal_moves.append(square + new_square + 'r')
                            legal_moves.append(square + new_square + 'b')
                            legal_moves.append(square + new_square + 'n')
                    
        elif piece_type == 'N':  # Knight
            for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    new_square = coords_to_square(new_row, new_col)
                    legal_moves.append(square + new_square)
        elif piece_type == 'B':  # Bishop
            for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                for i in range(1, 8):
                    new_row, new_col = row + dr*i, col + dc*i
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    new_square = coords_to_square(new_row, new_col)
                    if new_square not in pieces:
                        legal_moves.append(square + new_square)
                    else:
                        if pieces[new_square][0] == opp_color:
                            legal_moves.append(square + new_square)
                        break
        elif piece_type == 'R':  # Rook
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                for i in range(1, 8):
                    new_row, new_col = row + dr*i, col + dc*i
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    new_square = coords_to_square(new_row, new_col)
                    if new_square not in pieces:
                        legal_moves.append(square + new_square)
                    else:
                        if pieces[new_square][0] == opp_color:
                            legal_moves.append(square + new_square)
                        break
        elif piece_type == 'Q':  # Queen
            for dr, dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                for i in range(1, 8):
                    new_row, new_col = row + dr*i, col + dc*i
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    new_square = coords_to_square(new_row, new_col)
                    if new_square not in pieces:
                        legal_moves.append(square + new_square)
                    else:
                        if pieces[new_square][0] == opp_color:
                            legal_moves.append(square + new_square)
                        break
        elif piece_type == 'K':  # King
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        new_square = coords_to_square(new_row, new_col)
                        legal_moves.append(square + new_square)
    
    # Score moves
    move_scores = []
    for move in legal_moves:
        score = 0
        from_square = move[:2]
        to_square = move[2:4]
        
        # Check if capture and calculate material gain
        if to_square in pieces:
            captured_piece = pieces[to_square]
            score += piece_values[captured_piece[1]]
        
        # Prefer center squares
        if to_square in center_squares:
            score += 2
            
        # Prefer pawn advancement (particularly for forward movement)
        if piece_type == 'P':
            if color == 'w':
                if int(to_square[1]) > int(from_square[1]):
                    score += 3
            else:
                if int(to_square[1]) < int(from_square[1]):
                    score += 3
                    
        # Prefer to keep pieces not under immediate threat
        # (this is a simplified check)
        score += 1  # Default preference
        
        # Prefer promotions when possible
        if len(move) > 4:
            score += 10  # Good promotion
            
        move_scores.append((score, move))
        
    # Find best move
    if not move_scores:
        # Fallback to first available move
        return (legal_moves[0] if legal_moves else "", memory)
    
    # Return move with highest score
    best_move = max(move_scores, key=lambda x: x[0])[1]
    return (best_move, memory)
