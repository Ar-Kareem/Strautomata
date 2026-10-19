
import numpy as np
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Convert to sets for easier manipulation
    me_set = set(me)
    opp_set = set(opp)
    
    # Determine home row based on color
    if color == 'b':
        home_row = 0  # black moves down, home row is row 0
        forward_dir = 1  # black moves towards lower rows
    else:
        home_row = 7  # white moves up, home row is row 7
        forward_dir = -1  # white moves towards higher rows
    
    # Get all legal moves for all pieces
    legal_moves = []
    
    # Generate all possible moves for each piece
    for row, col in me:
        # Check straight forward move
        new_row = row + forward_dir
        if 0 <= new_row <= 7 and (new_row, col) not in me_set and (new_row, col) not in opp_set:
            legal_moves.append(((row, col), (new_row, col)))
            
        # Check diagonal left capture
        new_row = row + forward_dir
        new_col = col - 1
        if 0 <= new_row <= 7 and 0 <= new_col <= 7:
            if (new_row, new_col) in opp_set:
                legal_moves.append(((row, col), (new_row, new_col)))
        
        # Check diagonal right capture
        new_row = row + forward_dir
        new_col = col + 1
        if 0 <= new_row <= 7 and 0 <= new_col <= 7:
            if (new_row, new_col) in opp_set:
                legal_moves.append(((row, col), (new_row, new_col)))
    
    # If no legal moves, game is over or no moves available
    if not legal_moves:
        # Try to find any valid move even if it's not capturing or advancing
        for row, col in me:
            new_row = row + forward_dir
            # Forward move
            if 0 <= new_row <= 7 and (new_row, col) not in me_set and (new_row, col) not in opp_set:
                return ((row, col), (new_row, col))
            
            # Diagonal captures
            for dc in [-1, 1]:
                new_row = row + forward_dir
                new_col = col + dc
                if 0 <= new_row <= 7 and 0 <= new_col <= 7 and (new_row, new_col) in opp_set:
                    return ((row, col), (new_row, new_col))
        
        # If still no valid moves, return a default (this shouldn't happen)
        return ((0, 0), (0, 0))
        
    # Evaluate each move based on several criteria
    best_move = None
    best_score = -1000000  # Low starting score
    
    for move in legal_moves:
        from_pos, to_pos = move
        row, col = from_pos
        new_row, new_col = to_pos
        
        score = 0
        
        # Win condition check - reaching home row
        if new_row == home_row:
            score += 1000  # Major bonus for reaching home row
        
        # Capture bonus
        if (new_row, new_col) in opp_set:
            score += 500  # Capture bonus
        
        # Advancement bonus (prioritize moves that move towards home row)
        advancement = abs(home_row - new_row) - abs(home_row - row)
        score += advancement * 10  # Bonus for moving closer to home
        
        # Central control bonus (prefer positions closer to center)
        center_dist = abs(3.5 - new_col)  # 3.5 is the center
        score += (3.5 - center_dist) * 5  # Prefer center positions
        
        # Mobility bonus (try to keep pieces that can make more moves)
        mobility_bonus = 0
        if color == 'b':
            # For black, prefer positions that allow more moves
            potential_moves = 0
            # Check if capturing move
            if (new_row + 1, new_col - 1) in opp_set or (new_row + 1, new_col + 1) in opp_set:
                potential_moves += 1
            if (new_row + 1, new_col) not in me_set and (new_row + 1, new_col) not in opp_set:
                potential_moves += 1
            mobility_bonus = potential_moves * 2
        else:
            # For white, prefer positions that allow more moves  
            potential_moves = 0
            # Check if capturing move
            if (new_row - 1, new_col - 1) in opp_set or (new_row - 1, new_col + 1) in opp_set:
                potential_moves += 1
            if (new_row - 1, new_col) not in me_set and (new_row - 1, new_col) not in opp_set:
                potential_moves += 1
            mobility_bonus = potential_moves * 2
        
        score += mobility_bonus
        
        # Avoid blocking own pieces
        if from_pos != to_pos and (new_row, new_col) in me_set:
            # This is a case of invalid move (shouldn't happen with our legal moves, but just in case)
            continue
            
        if score > best_score:
            best_score = score
            best_move = move
            
    # If no moves are preferred, try to find any legal move that isn't just a straight forward that's blocked
    if best_move is None:
        # Return a simple move to prevent disqualification
        return legal_moves[0]
        
    return best_move
