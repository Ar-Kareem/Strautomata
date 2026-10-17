
import numpy as np
from collections import deque

def get_all_moves(my_men, my_kings, opp_men, opp_kings, color):
    """Generate all possible moves for the current player"""
    moves = []
    # All pieces (men and kings) that can move
    all_pieces = my_men + my_kings
    
    # For each piece, find all valid moves
    for piece_row, piece_col in all_pieces:
        piece_type = 'king' if (piece_row, piece_col) in my_kings else 'men'
        
        # Determine movement direction based on color and piece type
        if piece_type == 'men':
            if color == 'b':
                # Black men move down (row decreases)
                directions = [(-1, -1), (-1, 1)]
            else:
                # White men move up (row increases)
                directions = [(1, -1), (1, 1)]
        else:
            # Kings move in all diagonal directions
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        # Check all possible moves from this piece
        for dr, dc in directions:
            # Simple move (one square)
            new_row, new_col = piece_row + dr, piece_col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if (new_row, new_col) not in my_men and (new_row, new_col) not in my_kings:
                    # Check if it's a dark square
                    if (new_row + new_col) % 2 == 0:
                        moves.append(((piece_row, piece_col), (new_row, new_col)))
            
            # Jump/capture move (two squares in same direction)
            jump_row, jump_col = piece_row + 2 * dr, piece_col + 2 * dc
            if 0 <= jump_row < 8 and 0 <= jump_col < 8:
                # Check if there's an opponent piece to jump over
                mid_row, mid_col = piece_row + dr, piece_col + dc
                if (mid_row, mid_col) in opp_men or (mid_row, mid_col) in opp_kings:
                    # Check if jump destination is free and is dark square
                    if (jump_row, jump_col) not in my_men and (jump_row, jump_col) not in my_kings:
                        if (jump_row + jump_col) % 2 == 0:
                            moves.append(((piece_row, piece_col), (jump_row, jump_col)))
    
    return moves

def get_capture_moves(my_men, my_kings, opp_men, opp_kings, color):
    """Get all capture moves (mandatory)"""
    all_moves = get_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    capture_moves = [move for move in all_moves if abs(move[1][0] - move[0][0]) == 2]
    return capture_moves

def can_capture(my_men, my_kings, opp_men, opp_kings, color):
    """Check if there are any capture moves available"""
    return len(get_capture_moves(my_men, my_kings, opp_men, opp_kings, color)) > 0

def evaluate_position(my_men, my_kings, opp_men, opp_kings, color):
    """Evaluate the current position"""
    score = 0
    
    # Material advantage
    score += len(my_men) * 10
    score += len(my_kings) * 25
    
    # Opponent material
    score -= len(opp_men) * 10
    score -= len(opp_kings) * 25
    
    # King advantage (kings are worth more than men)
    score += len(my_kings) * 100
    
    # Center control (pieces in the center are generally better)
    center_control = 0
    for row, col in my_men:
        if 2 <= row <= 5 and 2 <= col <= 5:
            center_control += 10
    for row, col in my_kings:
        if 2 <= row <= 5 and 2 <= col <= 5:
            center_control += 15
    score += center_control
    
    # Advance advantage (pieces that are more forward)
    advancement = 0
    for row, col in my_men:
        if color == 'b':
            advancement += row  # More advanced = more row number
        else:
            advancement += (7 - row)  # More advanced = less row number
    score += advancement * 5
    
    # King advancement (kings should be advanced)
    king_advancement = 0
    for row, col in my_kings:
        if color == 'b':
            king_advancement += row
        else:
            king_advancement += (7 - row)
    score += king_advancement * 7
    
    # Mobility - number of possible moves
    total_moves = len(get_all_moves(my_men, my_kings, opp_men, opp_kings, color))
    score += total_moves * 2
    
    # Safety - avoid pieces that are easily captured
    for row, col in my_men:
        if color == 'b' and row >= 6:
            score += 5  # Encourage promoting
        elif color == 'w' and row <= 1:
            score += 5
    
    return score

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Check if there are mandatory captures
    capture_moves = get_capture_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if capture_moves:
        # Prioritize moves that capture the most pieces (maximize captures)
        best_move = capture_moves[0]
        max_captured = 0
        
        # For simplicity, we'll use a greedy approach - choose move that captures
        # the most opponent pieces, but also consider safety and board control
        best_capture = None
        max_captured = 0
        
        for move in capture_moves:
            from_row, from_col = move[0]  
            to_row, to_col = move[1]
            
            # Calculate potential captures in this move (simple case)
            captured_count = 1  # Always one captured in a capture move
            
            # Prefer moves that are safer and promote pieces
            if captured_count > max_captured:
                max_captured = captured_count
                best_capture = move
            elif captured_count == max_captured:
                # If equal, prefer moves that advance pieces or keep kings safe
                if (color == 'b' and to_row > from_row) or (color == 'w' and to_row < from_row):
                    # Prefer advancing
                    if best_capture is None or (to_row > best_capture[1][0] if color == 'b' else to_row < best_capture[1][0]):
                        best_capture = move
        
        if best_capture:
            return best_capture
    
    # If no captures, find a good regular move
    all_moves = get_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not all_moves:
        # Fallback - should not happen in a valid game state
        return ((0, 0), (0, 0))
    
    # Prefer moves that:
    # 1. Promote men to kings when possible
    # 2. Get closer to opponent's side
    # 3. Avoid being captured easily
    
    best_move = None
    best_score = -float('inf')
    
    for move in all_moves:
        from_row, from_col = move[0]
        to_row, to_col = move[1]
        
        # Apply move to temporary board state to evaluate
        new_my_men = my_men.copy()
        new_my_kings = my_kings.copy()
        new_opp_men = opp_men.copy()
        new_opp_kings = opp_kings.copy()
        
        # Remove the moved piece from its old position
        if (from_row, from_col) in new_my_men:
            new_my_men.remove((from_row, from_col))
        if (from_row, from_col) in new_my_kings:
            new_my_kings.remove((from_row, from_col))
        
        # Add the moved piece to new position
        if (from_row, from_col) in my_men:
            new_my_men.append((to_row, to_col))
        if (from_row, from_col) in my_kings:
            new_my_kings.append((to_row, to_col))
        
        # Handle captures
        if abs(to_row - from_row) == 2:
            mid_row = (from_row + to_row) // 2
            mid_col = (from_col + to_col) // 2
            
            # Remove captured piece
            captured_pos = (mid_row, mid_col)
            if captured_pos in opp_men:
                new_opp_men.remove(captured_pos)
            elif captured_pos in opp_kings:
                new_opp_kings.remove(captured_pos)
        
        # Promotion check
        if (to_row, to_col) not in new_my_men and (to_row, to_col) not in new_my_kings:
            if (to_row, to_col) not in new_my_men and (to_row, to_col) not in new_my_kings:
                # Might be promotion
                if color == 'b' and to_row == 0:
                    new_my_kings.append((to_row, to_col))  
                    new_my_men.remove((from_row, from_col))
                elif color == 'w' and to_row == 7:
                    new_my_kings.append((to_row, to_col))
                    new_my_men.remove((from_row, from_col))
        
        # Evaluate the new board position
        move_score = evaluate_position(new_my_men, new_my_kings, new_opp_men, new_opp_kings, color)
        
        # Preference for pieces that are promoted, control center, or advance piece
        if (to_row, to_col) in new_my_kings:
            move_score += 200  # Extra bonus for kings
        if 2 <= to_row <= 5 and 2 <= to_col <= 5:
            move_score += 50  # Bonus for center control
        
        # Prefer advancement
        if color == 'b' and to_row < from_row:
            move_score += 10  # Prefer advancing forward
        elif color == 'w' and to_row > from_row:
            move_score += 10
        
        # Consider existing king movements
        if (from_row, from_col) in my_kings:
            move_score += 50  # Kings get bonus for movement
        
        if move_score > best_score:
            best_score = move_score
            best_move = move
            
    # If no good move found, fallback to simple move
    if best_move is None:
        best_move = all_moves[0]
        
    return best_move
