
import numpy as np
from itertools import chain

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Determine all possible moves
    all_moves = get_all_possible_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    # If no moves available (shouldn't happen since we're called only when moves exist)
    if not all_moves:
        return ((0,0),(0,0))  # fallback
    
    # If only one move available, return it immediately
    if len(all_moves) == 1:
        return all_moves[0]
    
    # Evaluate moves using minimax with alpha-beta pruning
    best_move = None
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    depth = 3  # search depth
    
    for move in all_moves:
        # Simulate the move
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = simulate_move(
            my_men.copy(), my_kings.copy(), opp_men.copy(), opp_kings.copy(), move, color
        )
        
        # Evaluate the position
        value = minimax(
            new_my_men, new_my_kings, new_opp_men, new_opp_kings,
            'w' if color == 'b' else 'b',  # opponent's turn next
            depth - 1,
            alpha,
            beta,
            False  # minimizing player
        )
        
        if value > best_value:
            best_value = value
            best_move = move
            alpha = max(alpha, value)
    
    return best_move if best_move else all_moves[0]

def minimax(my_men, my_kings, opp_men, opp_kings, color, depth, alpha, beta, maximizing_player):
    if depth == 0:
        return evaluate_position(my_men, my_kings, opp_men, opp_kings, color)
    
    all_moves = get_all_possible_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if maximizing_player:
        max_eval = -float('inf')
        for move in all_moves:
            new_my_men, new_my_kings, new_opp_men, new_opp_kings = simulate_move(
                my_men.copy(), my_kings.copy(), opp_men.copy(), opp_kings.copy(), move, color
            )
            eval = minimax(
                new_my_men, new_my_kings, new_opp_men, new_opp_kings,
                'w' if color == 'b' else 'b',
                depth - 1,
                alpha,
                beta,
                False
            )
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in all_moves:
            new_my_men, new_my_kings, new_opp_men, new_opp_kings = simulate_move(
                my_men.copy(), my_kings.copy(), opp_men.copy(), opp_kings.copy(), move, color
            )
            eval = minimax(
                new_my_men, new_my_kings, new_opp_men, new_opp_kings,
                'w' if color == 'b' else 'b',
                depth - 1,
                alpha,
                beta,
                True
            )
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def evaluate_position(my_men, my_kings, opp_men, opp_kings, color):
    # Material score
    material = (len(my_men) + 2 * len(my_kings)) - (len(opp_men) + 2 * len(opp_kings))
    
    # Positional score - central positions are more valuable
    my_position = 0
    for (r, c) in chain(my_men, my_kings):
        my_position += (3.5 - abs(3.5 - r)) * 0.1  # rows
        my_position += (3.5 - abs(3.5 - c)) * 0.1  # columns
    
    opp_position = 0
    for (r, c) in chain(opp_men, opp_kings):
        opp_position += (3.5 - abs(3.5 - r)) * 0.1
        opp_position += (3.5 - abs(3.5 - c)) * 0.1
    
    # Promotion potential - pieces close to becoming kings
    promotion = 0
    if color == 'w':
        promotion = sum(1 for (r, _) in my_men if r >= 5) * 0.2
    else:
        promotion = sum(1 for (r, _) in my_men if r <= 2) * 0.2
    
    # King safety - kings not vulnerable to capture
    king_safety = 0
    for (r, c) in my_kings:
        safe = True
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            if (r + dr, c + dc) in opp_men or (r + dr, c + dc) in opp_kings:
                safe = False
                break
        if safe:
            king_safety += 0.1
    
    # Aggregation - pieces close together are better for defense
    aggregation = 0
    if len(my_men) + len(my_kings) > 1:
        avg_r = sum(r for (r, c) in chain(my_men, my_kings)) / (len(my_men) + len(my_kings))
        avg_c = sum(c for (r, c) in chain(my_men, my_kings)) / (len(my_men) + len(my_kings))
        aggregation = sum(
            abs(r - avg_r) + abs(c - avg_c) for (r, c) in chain(my_men, my_kings)
        ) * -0.05  # negative because lower distance is better
    
    return material + (my_position - opp_position) + promotion + king_safety + aggregation

def simulate_move(my_men, my_kings, opp_men, opp_kings, move, color):
    (from_row, from_col), (to_row, to_col) = move
    
    # Check if it's a capture move
    is_capture = abs(from_row - to_row) == 2
    
    # Remove the piece from its original position
    if (from_row, from_col) in my_men:
        my_men.remove((from_row, from_col))
    else:
        my_kings.remove((from_row, from_col))
    
    # Add to new position
    if color == 'w' and to_row == 7 or color == 'b' and to_row == 0:
        my_kings.append((to_row, to_col))  # promotion to king
    else:
        my_men.append((to_row, to_col))
    
    # Remove captured piece if this was a capture
    if is_capture:
        cap_row = (from_row + to_row) // 2
        cap_col = (from_col + to_col) // 2
        if (cap_row, cap_col) in opp_men:
            opp_men.remove((cap_row, cap_col))
        else:
            opp_kings.remove((cap_row, cap_col))
    
    return my_men, my_kings, opp_men, opp_kings

def get_all_possible_moves(my_men, my_kings, opp_men, opp_kings, color):
    all_pieces = my_men + my_kings
    opponent_pieces = opp_men + opp_kings
    capture_moves = []
    regular_moves = []
    
    for (r, c) in all_pieces:
        # Determine possible directions based on piece type and color
        if (r, c) in my_kings:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # kings can move both directions
        else:
            if color == 'w':
                directions = [(1, -1), (1, 1)]  # white moves upward
            else:
                directions = [(-1, -1), (-1, 1)]  # black moves downward
        
        # Check for regular moves and captures
        for dr, dc in directions:
            # Regular move
            new_r, new_c = r + dr, c + dc
            if 0 <= new_r < 8 and 0 <= new_c < 8:
                if (new_r, new_c) not in opponent_pieces and (new_r, new_c) not in all_pieces:
                    regular_moves.append(((r, c), (new_r, new_c)))
            
            # Capture move
            new_r, new_c = r + 2*dr, c + 2*dc
            mid_r, mid_c = r + dr, c + dc
            if (0 <= new_r < 8 and 0 <= new_c < 8 and 
                (mid_r, mid_c) in opponent_pieces and 
                (new_r, new_c) not in opponent_pieces and 
                (new_r, new_c) not in all_pieces):
                capture_moves.append(((r, c), (new_r, new_c)))
    
    # If there are captures available, they are mandatory - return only those
    if capture_moves:
        return capture_moves
    return regular_moves
