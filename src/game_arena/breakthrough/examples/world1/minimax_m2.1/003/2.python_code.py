
from typing import List, Tuple, Set, Dict
import copy

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Breakthrough AI Policy
    
    Implements a heuristic evaluation-based strategy that balances:
    - Advancement toward opponent's home row (primary win condition)
    - Offensive capturing of opponent pieces
    - Maintaining piece mobility
    - Blocking opponent advancement paths
    - Controlling central board positions
    - Defensive protection of critical positions
    
    Args:
        me: List of (row, col) tuples representing my pieces
        opp: List of (row, col) tuples representing opponent pieces
        color: 'b' for black (moves downward), 'w' for white (moves upward)
    
    Returns:
        A tuple of ((from_row, from_col), (to_row, to_col)) representing the move
    """
    
    # Convert to sets for O(1) lookup
    my_pieces: Set[Tuple[int, int]] = set(me)
    opp_pieces: Set[Tuple[int, int]] = set(opp)
    
    # Determine direction of movement
    forward = -1 if color == 'b' else 1
    
    # Calculate opponent's home row (furthest row from us)
    opp_home_row = 7 if color == 'b' else 0
    
    # All possible moves with their evaluations
    moves: List[Tuple[Tuple[Tuple[int, int], Tuple[int, int]], float]] = []
    
    for piece_row, piece_col in me:
        # Get all possible moves for this piece
        for dc in [-1, 0, 1]:  # -1: left diagonal, 0: forward, 1: right diagonal
            new_row = piece_row + forward
            new_col = piece_col + dc
            
            # Check bounds
            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                continue
            
            target = (new_row, new_col)
            
            # Check if move is valid
            if dc == 0:
                # Forward move: target must be empty
                if target in my_pieces or target in opp_pieces:
                    continue
                move_type = "forward"
                is_capture = False
            else:
                # Diagonal move
                if target in my_pieces:
                    continue
                elif target in opp_pieces:
                    # Capture move
                    move_type = "capture"
                    is_capture = True
                else:
                    # Forward diagonal into empty space
                    move_type = "diagonal"
                    is_capture = False
            
            # Evaluate the move
            score = 0.0
            
            # 1. Win condition: reaching opponent's home row
            if new_row == opp_home_row:
                score += 10000  # Immediate win
            
            # 2. Advancement progress (closer to winning)
            advancement = abs(new_row - opp_home_row)
            score += (7 - advancement) * 100
            
            # 3. Capture priority
            if is_capture:
                score += 500
            
            # 4. Mobility: count available moves from new position
            mobility = 0
            for dc2 in [-1, 0, 1]:
                check_row = new_row + forward
                check_col = new_col + dc2
                if 0 <= check_row < 8 and 0 <= check_col < 8:
                    check_target = (check_row, check_col)
                    if check_target not in my_pieces:
                        mobility += 1
            score += mobility * 10
            
            # 5. Blocking opponent advancement paths
            blocking_score = 0
            for opp_row, opp_col in opp:
                opp_forward = 1 if color == 'b' else -1  # Opposite direction
                # Check if our move blocks opponent's forward path
                if (new_row == opp_row + opp_forward and new_col == opp_col):
                    blocking_score += 50
                # Check if we block opponent's diagonal moves
                elif (new_row == opp_row + opp_forward and 
                      new_col in [opp_col - 1, opp_col + 1]):
                    blocking_score += 30
            score += blocking_score
            
            # 6. Center column control (more strategic options)
            center_cols = [2, 3, 4, 5]
            if new_col in center_cols:
                score += 20
            
            # 7. Defensive consideration: avoid moves that leave pieces vulnerable
            # Check if new position has protection from other pieces
            protected = False
            for my_row, my_col in my_pieces:
                if my_row == new_row and my_col == new_col:
                    continue
                # Check if any friendly piece can protect this position
                if (abs(my_row - new_row) == 1 and 
                    abs(my_col - new_col) <= 1):
                    protected = True
                    break
            if not protected:
                # Unprotected piece in enemy territory is risky
                if (color == 'b' and new_row < 3) or (color == 'w' and new_row > 4):
                    score -= 15
            
            # 8. Piece safety: check if move exposes piece to immediate capture
            danger = 0
            for opp_row, opp_col in opp:
                opp_forward = -1 if color == 'b' else 1  # Opposite of our direction
                # Check if opponent can capture this piece next turn
                if (new_row == opp_row + opp_forward and 
                    new_col in [opp_col - 1, opp_col + 1]):
                    danger += 40
            score -= danger
            
            moves.append((((piece_row, piece_col), (new_row, new_col)), score))
    
    # Select best move
    if not moves:
        return None  # No legal moves available
    
    # Sort by score descending and return best move
    moves.sort(key=lambda x: x[1], reverse=True)
    best_move = moves[0][0]
    
    return best_move
