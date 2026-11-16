
import numpy as np
from typing import List, Dict, Tuple

def get_piece_value(piece: str) -> int:
    """Get material value of a piece."""
    if not piece:
        return 0
    piece_type = piece[1]
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    return values.get(piece_type, 0)

def is_king_in_check(pieces: Dict[str, str], to_play: str) -> bool:
    """Basic check for whether king is in check."""
    king_pos = None
    king_color = 'w' if to_play == 'white' else 'b'
    for pos, piece in pieces.items():
        if piece[0] == king_color and piece[1] == 'K':
            king_pos = pos
            break
            
    if not king_pos:
        return False
        
    # Find opponent pieces and check if they can attack the king
    opponent_color = 'b' if to_play == 'white' else 'w'
    
    # Very simplified check - just see if any opponent piece can directly attack king
    for pos, piece in pieces.items():
        if piece[0] == opponent_color:
            if is_valid_move(pos, king_pos, piece, pieces):
                return True
    return False

def is_valid_move(from_pos: str, to_pos: str, piece: str, pieces: Dict[str, str]) -> bool:
    """Basic validation of whether a move is valid (not used but can be extended)."""
    # This is a stub implementation - in full implementation would validate move legality
    # For now we just return True for any move to simplify evaluation
    return True

def policy(pieces: Dict[str, str], to_play: str) -> str:
    """Select the best move based on simple heuristics."""
    
    # Get legal moves - in a real implementation we'd calculate these
    # For now we'll get them from the piece state and make a move
    
    # If we're in check, prioritize escape moves
    if is_king_in_check(pieces, to_play):
        # Try to find a move that gets king out of check
        # Simplified approach - find any legal move that doesn't put king in check
        pass
    
    # Get all possible moves from current position
    # Simplified: look for captures and make one that wins material
    
    # Get list of our pieces (our color)
    my_color = 'w' if to_play == 'white' else 'b'
    my_pieces = {pos: piece for pos, piece in pieces.items() if piece[0] == my_color}
    
    # Simple scoring function
    def score_move(from_pos: str, to_pos: str) -> int:
        piece_moved = pieces.get(from_pos, '')
        piece_captured = pieces.get(to_pos, '')
        
        # Basic capture value
        capture_value = get_piece_value(piece_captured)
        moved_value = get_piece_value(piece_moved)
        
        # Pawn promotion gives bonus
        promotion_bonus = 0
        if piece_moved[1] == 'P' and (to_pos[1] == '8' or to_pos[1] == '1'):
            promotion_bonus = 9  # Queen value
            
        return capture_value - moved_value + promotion_bonus
    
    # Simplified legal move generation - just check adjacent squares for simple pieces
    legal_moves = []
    for pos, piece in pieces.items():
        if piece[0] != my_color:
            continue
        # Simplified: generate moves for each piece in simple fashion
        # In a real implementation, we'd use proper chess rules
        if piece[1] == 'P':
            # Pawn moves - forward 1 or 2, captures diagonally
            rank = int(pos[1])
            file = pos[0]
            if my_color == 'w':
                # White pawn moves up
                # Move forward
                forward1 = f"{file}{rank + 1}"
                if forward1 in pieces and pieces[forward1] == '':
                    legal_moves.append(pos + forward1)
                # Move forward 2 (from rank 2)
                if rank == 2:
                    forward2 = f"{file}{rank + 2}"
                    if forward2 in pieces and pieces[forward2] == '':
                        legal_moves.append(pos + forward2)
                # Captures
                for offset in [-1, 1]:
                    capture_file = chr(ord(file) + offset)
                    if 'a' <= capture_file <= 'h':
                        capture_pos = f"{capture_file}{rank + 1}"
                        if capture_pos in pieces and pieces[capture_pos] != '':
                            legal_moves.append(pos + capture_pos)
            else:
                # Black pawn moves down
                forward1 = f"{file}{rank - 1}"
                if forward1 in pieces and pieces[forward1] == '':
                    legal_moves.append(pos + forward1)
                if rank == 7:
                    forward2 = f"{file}{rank - 2}"
                    if forward2 in pieces and pieces[forward2] == '':
                        legal_moves.append(pos + forward2)
                # Captures
                for offset in [-1, 1]:
                    capture_file = chr(ord(file) + offset)
                    if 'a' <= capture_file <= 'h':
                        capture_pos = f"{capture_file}{rank - 1}"
                        if capture_pos in pieces and pieces[capture_pos] != '':
                            legal_moves.append(pos + capture_pos)
        elif piece[1] == 'K':
            # King moves one square in any direction
            file = pos[0]
            rank = int(pos[1])
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    new_file = chr(ord(file) + df)
                    new_rank = rank + dr
                    if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                        new_pos = f"{new_file}{new_rank}"
                        legal_moves.append(pos + new_pos)
    
    # For simplification, if no proper generation, generate some moves
    if not legal_moves:
        # Generate any possible move for demo (in practice would do proper legal moves)
        for pos, piece in pieces.items():
            if piece[0] == my_color:
                for other_pos, other_piece in pieces.items():
                    if other_pos != pos:
                        legal_moves.append(pos + other_pos)
    
    # If no legal moves at all, return first one (shouldn't happen)
    if not legal_moves:
        legal_moves = ['e2e4', 'd2d4']
    
    # Find the best move among legal moves
    best_move = None
    best_score = -float('inf')
    
    # Try a few moves from the available ones
    # Prioritize captures and checkmate-like moves
    captures = []
    other_moves = []
    
    for move in legal_moves[:10]:  # Limit for speed
        if len(move) >= 4:
            from_pos = move[:2]
            to_pos = move[2:4]
            piece_moved = pieces.get(from_pos, '')
            piece_captured = pieces.get(to_pos, '')
            
            if piece_captured != '' and piece_captured[0] != my_color:
                captures.append(move)
            else:
                other_moves.append(move)
    
    # Prioritize captures
    if captures:
        # Score captures and pick the best one
        for move in captures:
            score = score_move(move[:2], move[2:4])
            if score > best_score:
                best_score = score
                best_move = move
        if best_move:
            return best_move
                
    # If not captures, pick best from other moves
    for move in other_moves[:10]:
        if len(move) >= 4:
            from_pos = move[:2]
            to_pos = move[2:4]
            score = score_move(from_pos, to_pos) + np.random.randint(0, 2) # Small randomness
            if score > best_score:
                best_score = score
                best_move = move
                
    # Fallback to one of the first moves
    if best_move:
        return best_move
    else:
        return legal_moves[0] if legal_moves else 'e2e4'

