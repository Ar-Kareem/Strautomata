
import numpy as np
from collections import deque

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Convert inputs to sets for faster lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    # All pieces for current player
    my_pieces = my_men_set.union(my_kings_set)
    # All opponent pieces
    opp_pieces = opp_men_set.union(opp_kings_set)
    
    # Generate all possible moves
    moves = generate_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, color)
    
    if not moves:
        # If no moves available, return dummy move (but this shouldn't happen in valid game state)
        return ((0, 0), (0, 0))
    
    # Prioritize capture moves
    capture_moves = [move for move in moves if is_capture(move, my_men_set, my_kings_set, opp_men_set, opp_kings_set)]
    
    if capture_moves:
        # If captures available, prefer those
        moves = capture_moves
    
    # Evaluate all moves with a simple heuristic
    best_move = None
    best_score = -float('inf')
    
    for move in moves:
        # Evaluate the move
        score = evaluate_move(move, my_men_set, my_kings_set, opp_men_set, opp_kings_set, color)
        if score > best_score:
            best_score = score
            best_move = move
    
    # If no good move found, just return a random legal move
    return best_move if best_move else moves[0]

def is_capture(move, my_men_set, my_kings_set, opp_men_set, opp_kings_set):
    """Check if a move is a capture move"""
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    # A capture is when piece moves by 2 squares diagonally
    row_diff = abs(to_row - from_row)
    col_diff = abs(to_col - from_col)
    return row_diff == 2 and col_diff == 2

def generate_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, color):
    """Generate all legal moves for the current player"""
    moves = []
    all_my_pieces = my_men_set.union(my_kings_set)
    
    # For each piece, find valid moves
    for piece in all_my_pieces:
        row, col = piece
        piece_type = 'king' if piece in my_kings_set else 'man'
        
        # For each possible direction
        directions = []
        if piece_type == 'king' or color == 'b':  # black moves down
            directions.append((-1, -1))  # down-left
            directions.append((-1, 1))   # down-right
        if piece_type == 'king' or color == 'w':  # white moves up
            directions.append((1, -1))   # up-left
            directions.append((1, 1))    # up-right
            
        for dr, dc in directions:
            # Try single move
            new_row, new_col = row + dr, col + dc
            if is_valid_square(new_row, new_col) and (new_row, new_col) not in all_my_pieces:
                # Check if there's a piece to capture
                capture_row, capture_col = row + 2*dr, col + 2*dc
                if (is_valid_square(capture_row, capture_col) and 
                    (capture_row, capture_col) not in all_my_pieces and
                    (capture_row, capture_col) in opp_men_set or (capture_row, capture_col) in opp_kings_set):
                    # This is a capture move
                    moves.append(((row, col), (capture_row, capture_col)))
                elif not is_valid_square(capture_row, capture_col) or (capture_row, capture_col) in all_my_pieces:
                    # Regular move
                    moves.append(((row, col), (new_row, new_col)))
    
    # Filter only the moves that would capture if there are any captures available
    capture_moves = [move for move in moves if is_capture(move, my_men_set, my_kings_set, opp_men_set, opp_kings_set)]
    if capture_moves:
        # If any capture moves exist, return only those
        moves = capture_moves
    
    return moves if moves else []

def is_valid_square(row, col):
    """Check if the square is within the board range and is dark square"""
    return 0 <= row <= 7 and 0 <= col <= 7 and (row + col) % 2 == 1

def evaluate_move(move, my_men_set, my_kings_set, opp_men_set, opp_kings_set, color):
    """Simple heuristic evaluation of a move"""
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    
    score = 0
    
    # Piece advancement bonus (especially for kings)
    if color == 'b':
        advancement = from_row - to_row  # Black moves toward lower rows
    else:
        advancement = to_row - from_row  # White moves toward higher rows
    
    # Bonus for advancing (but not too much for early game)
    if advancement > 0:
        score += advancement * 10
    
    # Capture bonus
    if is_capture(move, my_men_set, my_kings_set, opp_men_set, opp_kings_set):
        score += 100  # Large bonus for captures
    
    # King promotion bonus (when we move to king row)
    if (from_row, from_col) in my_men_set:
        is_promoted = ((color == 'b' and to_row == 0) or (color == 'w' and to_row == 7))
        if is_promoted:
            score += 50
    
    # Center control bonus
    center_squares = {(3,3), (3,4), (4,3), (4,4)}
    if (to_row, to_col) in center_squares:
        score += 15
    
    # Edge control bonus (having a piece near center but toward the edge)
    if abs(to_col - 3.5) <= 2:  # Within 2 columns of center
        if abs(to_row - 3.5) <= 2:  # Within 2 rows of center
            score += 10
    
    # Mobility bonus (better if not about to get captured)
    # Simple check for immediate threat
    threat_score = 0
    for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
        threat_row, threat_col = to_row + dr, to_col + dc
        if (is_valid_square(threat_row, threat_col) and 
            (threat_row, threat_col) not in my_men_set and 
            (threat_row, threat_col) not in my_kings_set and 
            (threat_row, threat_col) in opp_men_set or (threat_row, threat_col) in opp_kings_set):
            threat_score -= 5  # Deduct for being exposed
    
    return score + threat_score

