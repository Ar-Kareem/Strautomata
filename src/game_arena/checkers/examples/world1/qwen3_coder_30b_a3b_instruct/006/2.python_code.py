
import random
from typing import Tuple, List

def policy(my_men: List[Tuple[int, int]], 
           my_kings: List[Tuple[int, int]], 
           opp_men: List[Tuple[int, int]], 
           opp_kings: List[Tuple[int, int]], 
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    
    # Convert lists to sets for faster lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    # All pieces
    my_pieces = my_men_set.union(my_kings_set)
    opp_pieces = opp_men_set.union(opp_kings_set)
    
    # Create a helper function to check if a square is on the board
    def is_on_board(row, col):
        return 0 <= row < 8 and 0 <= col < 8
    
    # Create a helper function to check if a square is dark
    def is_dark_square(row, col):
        return (row + col) % 2 == 1
    
    # Create a helper function to check if a square is valid (dark square on the board)
    def is_valid_square(row, col):
        return is_on_board(row, col) and is_dark_square(row, col)
    
    # Get all legal moves for a piece at (row, col) in the current position
    def get_legal_moves(row, col):
        moves = []
        # Define movement directions
        directions = []
        if color == 'b':
            directions = [(-1, -1), (-1, 1)]  # Black moves down
        else:
            directions = [(1, -1), (1, 1)]  # White moves up
            
        # For kings, add all diagonal directions
        if (row, col) in my_kings_set:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            # Simple move (one step)
            new_row, new_col = row + dr, col + dc
            if is_valid_square(new_row, new_col) and (new_row, new_col) not in my_pieces and (new_row, new_col) not in opp_pieces:
                moves.append(((row, col), (new_row, new_col)))
                
            # Jump/capture
            jump_row, jump_col = row + 2*dr, col + 2*dc
            # Check if can jump over opponent piece
            mid_row, mid_col = row + dr, col + dc
            if is_valid_square(jump_row, jump_col) and (jump_row, jump_col) not in my_pieces and (jump_row, jump_col) not in opp_pieces and (mid_row, mid_col) in opp_pieces:
                moves.append(((row, col), (jump_row, jump_col)))

        return moves
    
    # Assessment function for a move
    def evaluate_move(from_pos, to_pos):
        # Get piece type
        piece_type = "man"
        if from_pos in my_kings_set:
            piece_type = "king"
            
        score = 0
        
        # Prefer captures
        if abs(to_pos[0] - from_pos[0]) == 2:
            score += 1000
            
        # Prefer moves that promote pieces to kings
        if piece_type == "man":
            if (color == 'b' and to_pos[0] == 0) or (color == 'w' and to_pos[0] == 7):
                score += 500
                
        # Prefer center control
        center_rows = [3, 4]
        center_cols = [3, 4]
        if to_pos[0] in center_rows and to_pos[1] in center_cols:
            score += 10
            
        # Avoid moving pieces to corners (unless they're king)
        if piece_type == "man":
            corner_squares = [(0, 0), (0, 7), (7, 0), (7, 7)]
            if to_pos in corner_squares:
                score -= 50
                
        # Prefer attacking positions (if not a capture, fewer pieces in the way)
        if abs(to_pos[0] - from_pos[0]) == 1:
            # Simple move, check if it moves towards center or gives safety
            if (color == 'b' and to_pos[0] < from_pos[0]) or (color == 'w' and to_pos[0] > from_pos[0]):
                score += 20  # Moving in the right direction
            else:
                score -= 5
                
        return score
    
    # Get all possible moves for current position
    all_moves = []
    for piece in my_pieces:
        moves = get_legal_moves(piece[0], piece[1])
        all_moves.extend(moves)
    
    # If there are captures, we must make one
    capture_moves = [move for move in all_moves if abs(move[1][0] - move[0][0]) == 2]
    
    if capture_moves:
        # Evaluate captures and pick the best
        best_capture = None
        best_score = float('-inf')
        for move in capture_moves:
            score = evaluate_move(move[0], move[1])
            if score > best_score:
                best_score = score
                best_capture = move
        return best_capture
    else:
        # No captures available, so play a good non-capture move
        if all_moves:
            # Evaluate all non-capture moves
            best_move = None
            best_score = float('-inf')
            for move in all_moves:
                # Make sure all moves are non-capture (our check already excludes captures)
                score = evaluate_move(move[0], move[1])
                if score > best_score:
                    best_score = score
                    best_move = move
            return best_move if best_move else all_moves[0]
        else:
            # If no moves, return a random one (should not happen)
            return random.choice(all_moves) if all_moves else ((0, 0), (1, 1))

    # If all else fails, return any, probably an invalid move
    return ((0, 0), (1, 1))
