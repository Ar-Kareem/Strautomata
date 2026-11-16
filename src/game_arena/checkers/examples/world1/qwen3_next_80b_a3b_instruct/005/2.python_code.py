
import numpy as np
from collections import defaultdict
import time

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Start timing to ensure we stay within 1 second
    start_time = time.time()
    
    # Convert to sets for O(1) lookup
    my_men = set(map(tuple, my_men))
    my_kings = set(map(tuple, my_kings))
    opp_men = set(map(tuple, opp_men))
    opp_kings = set(map(tuple, opp_kings))
    
    # All my pieces
    my_pieces = my_men | my_kings
    opp_pieces = opp_men | opp_kings
    
    # Determine direction based on color
    direction = -1 if color == 'b' else 1  # black moves down (row decreases), white moves up (row increases)
    
    # First: Check for mandatory captures
    capture_moves = find_all_capture_moves(my_men, my_kings, opp_men, opp_kings, color, direction)
    if capture_moves:
        # Among all capture moves, choose the one with best evaluation
        best_move = None
        best_eval = float('-inf')
        
        for move in capture_moves:
            # Simulate move and evaluate
            eval_score = evaluate_position_after_move(my_men, my_kings, opp_men, opp_kings, move, color, direction, start_time)
            if eval_score > best_eval:
                best_eval = eval_score
                best_move = move
                
        return best_move
        
    # No captures, search for best non-capture move using minimax
    non_capture_moves = find_all_non_capture_moves(my_men, my_kings, color, direction)
    if not non_capture_moves:
        # No legal moves - should not happen in valid games, but return something
        return ((0,0), (0,0))
    
    # Use minimax with alpha-beta pruning
    # Adaptive depth based on number of pieces
    total_pieces = len(my_pieces) + len(opp_pieces)
    max_depth = min(6, max(3, 8 - total_pieces // 4))  # Deeper when fewer pieces
    
    best_move = None
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    # Sort moves by heuristic to improve alpha-beta pruning efficiency
    sorted_moves = sorted(non_capture_moves, key=lambda m: heuristic_move_score(m, my_men, my_kings, opp_men, opp_kings, color, direction), reverse=True)
    
    for move in sorted_moves:
        if time.time() - start_time > 0.8:  # Leave buffer for recursion
            break
            
        # Simulate move
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = simulate_move(my_men, my_kings, opp_men, opp_kings, move, color, direction)
        
        # Evaluate this move using minimax
        score = minimax(new_my_men, new_my_kings, new_opp_men, new_opp_kings, color, direction, 
                       depth=max_depth-1, alpha=alpha, beta=beta, maximizing=False, start_time=start_time)
        
        if score > best_score:
            best_score = score
            best_move = move
            
        alpha = max(alpha, best_score)
        
        if beta <= alpha:
            break  # Alpha-beta pruning
    
    # If no good moves found (shouldn't happen), return first move
    if best_move is None:
        return non_capture_moves[0]
        
    return best_move

def is_dark_square(row, col):
    return (row + col) % 2 == 1

def find_all_capture_moves(my_men, my_kings, opp_men, opp_kings, color, direction):
    """Find all possible capture moves (including multi-jumps)"""
    all_captures = []
    my_pieces = my_men | my_kings
    
    def explore_jumps(piece, current_men, current_kings, current_opp_men, current_opp_kings, path, captured_so_far):
        row, col = piece
        captures = []
        
        # For kings: can move in all 4 diagonal directions
        # For men: only forward direction
        directions = []
        if piece in my_kings:
            directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
        else:
            directions = [(direction, -1), (direction, 1)]
        
        for dr, dc in directions:
            # Check if we can jump over opponent piece
            mid_row, mid_col = row + dr, col + dc
            land_row, land_col = row + 2*dr, col + 2*dc
            
            if (0 <= mid_row <= 7 and 0 <= mid_col <= 7 and 
                0 <= land_row <= 7 and 0 <= land_col <= 7 and
                is_dark_square(mid_row, mid_col) and is_dark_square(land_row, land_col)):
                
                # Check if opponent piece is on mid square
                mid_piece = (mid_row, mid_col)
                if mid_piece in current_opp_men or mid_piece in current_opp_kings:
                    # Check if landing square is empty
                    if (land_row, land_col) not in (current_men | current_kings | current_opp_men | current_opp_kings):
                        # This is a valid capture
                        # Create new board state after capture
                        new_men = current_men.copy()
                        new_kings = current_kings.copy()
                        new_opp_men = current_opp_men.copy()
                        new_opp_kings = current_opp_kings.copy()
                        
                        # Remove captured piece
                        if mid_piece in new_opp_men:
                            new_opp_men.remove(mid_piece)
                        else:
                            new_opp_kings.remove(mid_piece)
                            
                        # Move piece
                        if (row, col) in new_men:
                            new_men.remove((row, col))
                            if (land_row, land_col)[0] == (0 if direction == 1 else 7):  # Promote to king
                                new_kings.add((land_row, land_col))
                            else:
                                new_men.add((land_row, land_col))
                        else:  # It's a king
                            new_kings.remove((row, col))
                            new_kings.add((land_row, land_col))
                            
                        # Add this capture to path
                        new_path = path + [(row, col), (land_row, land_col)]
                        captures.append(((row, col), (land_row, land_col)))
                        
                        # Continue exploring from new position
                        more_captures = explore_jumps((land_row, land_col), new_men, new_kings, new_opp_men, new_opp_kings, new_path, captured_so_far + [mid_piece])
                        for mc in more_captures:
                            captures.append(mc)
        
        return captures
    
    # For each of our pieces, explore all possible capture sequences
    for piece in my_pieces:
        captures = explore_jumps(piece, my_men, my_kings, opp_men, opp_kings, [], [])
        # Flatten and return only the single-step moves that are part of capture sequences
        for capture in captures:
            if isinstance(capture, tuple) and len(capture) == 2 and isinstance(capture[0], tuple) and isinstance(capture[1], tuple):
                all_captures.append(capture)
            elif isinstance(capture, list) and len(capture) > 2:
                # This is a multi-jump sequence - we need to return each single jump
                # But for our policy, we only need the first jump to be returned
                # The engine will handle multi-jumps internally
                if len(capture) >= 4:  # At least two moves
                    all_captures.append((capture[0], capture[1]))
                    
    # Remove duplicates and return
    return list(set(all_captures))

def find_all_non_capture_moves(my_men, my_kings, color, direction):
    """Find all legal non-capture moves"""
    moves = []
    my_pieces = my_men | my_kings
    
    for piece in my_pieces:
        row, col = piece
        directions = []
        
        if piece in my_kings:
            directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
        else:
            directions = [(direction, -1), (direction, 1)]
            
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if (0 <= new_row <= 7 and 0 <= new_col <= 7 and 
                is_dark_square(new_row, new_col) and 
                (new_row, new_col) not in my_pieces):
                moves.append(((row, col), (new_row, new_col)))
                
    return moves

def simulate_move(my_men, my_kings, opp_men, opp_kings, move, color, direction):
    """Return new board state after making a move"""
    from_pos, to_pos = move
    new_my_men = my_men.copy()
    new_my_kings = my_kings.copy()
    new_opp_men = opp_men.copy()
    new_opp_kings = opp_kings.copy()
    
    # Remove piece from origin
    if from_pos in new_my_men:
        new_my_men.remove(from_pos)
    else:
        new_my_kings.remove(from_pos)
        
    # Check for promotion
    if (color == 'b' and to_pos[0] == 0) or (color == 'w' and to_pos[0] == 7):
        # Promote to king
        new_my_kings.add(to_pos)
    else:
        new_my_men.add(to_pos)
        
    # Check if it's a capture
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    mid_row, mid_col = (from_row + to_row) // 2, (from_col + to_col) // 2
    
    # If it's a capture, remove the opponent piece
    if (abs(from_row - to_row) == 2) and (abs(from_col - to_col) == 2):
        mid_piece = (mid_row, mid_col)
        if mid_piece in new_opp_men:
            new_opp_men.remove(mid_piece)
        elif mid_piece in new_opp_kings:
            new_opp_kings.remove(mid_piece)
            
    return new_my_men, new_my_kings, new_opp_men, new_opp_kings

def evaluate_position_after_move(my_men, my_kings, opp_men, opp_kings, move, color, direction, start_time):
    """Quick evaluation after move (used for capturing)"""
    if time.time() - start_time > 0.8:
        return 0
        
    new_my_men, new_my_kings, new_opp_men, new_opp_kings = simulate_move(my_men, my_kings, opp_men, opp_kings, move, color, direction)
    
    # Heuristic evaluation for immediate captures
    score = 0
    
    # Piece value: king is worth 3, man is worth 1
    score += 3 * len(new_my_kings)
    score += len(new_my_men)
    score -= 3 * len(new_opp_kings)
    score -= len(new_opp_men)
    
    # Control of center
    center_score = 0
    for r, c in new_my_men:
        if 2 <= r <= 5 and 2 <= c <= 5:
            center_score += 0.5
    for r, c in new_my_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            center_score += 1.0
            
    score += center_score
    
    # Advanced pieces (for black: lower row = better, for white: higher row = better)
    advancement_score = 0
    if color == 'b':  # black moves down (row decreases)
        for r, c in new_my_men:
            advancement_score += (7 - r) * 0.1
        for r, c in new_my_kings:
            advancement_score += (7 - r) * 0.2
        # penalize pieces on back row
        for r, c in new_opp_men:
            advancement_score -= r * 0.1
        for r, c in new_opp_kings:
            advancement_score -= r * 0.2
    else:  # white moves up (row increases)
        for r, c in new_my_men:
            advancement_score += r * 0.1
        for r, c in new_my_kings:
            advancement_score += r * 0.2
        # penalize opponent's advanced pieces
        for r, c in new_opp_men:
            advancement_score -= (7 - r) * 0.1
        for r, c in new_opp_kings:
            advancement_score -= (7 - r) * 0.2
            
    score += advancement_score
    
    return score

def heuristic_move_score(move, my_men, my_kings, opp_men, opp_kings, color, direction):
    """Heuristic to sort moves for better alpha-beta pruning"""
    from_pos, to_pos = move
    
    score = 0
    # Favor moves that capture
    if abs(from_pos[0] - to_pos[0]) == 2:
        score += 10
        
    # Favor center control
    if 2 <= to_pos[0] <= 5 and 2 <= to_pos[1] <= 5:
        score += 2
        
    # Favor advancement
    if color == 'b':  # black moves down (to lower row numbers)
        score += (7 - to_pos[0]) * 0.5
    else:  # white moves up (to higher row numbers)
        score += to_pos[0] * 0.5
        
    # Favor kinging
    if (color == 'b' and to_pos[0] == 0) or (color == 'w' and to_pos[0] == 7):
        score += 10
        
    # Penalize edge moves (more vulnerable)
    if to_pos[1] == 0 or to_pos[1] == 7:
        score -= 1
        
    return score

def minimax(my_men, my_kings, opp_men, opp_kings, color, direction, depth, alpha, beta, maximizing, start_time):
    """Minimax with alpha-beta pruning"""
    if time.time() - start_time > 0.8:
        return 0
        
    if depth == 0:
        return evaluate_position(my_men, my_kings, opp_men, opp_kings, color)
        
    # Check who is moving next
    next_color = color if maximizing else ('w' if color == 'b' else 'b')
    next_direction = -1 if next_color == 'b' else 1
    
    # Find captures - always mandatory
    captures = find_all_capture_moves(my_men, my_kings, opp_men, opp_kings, next_color, next_direction)
    
    if captures:
        # Must capture
        best_score = float('-inf') if maximizing else float('inf')
        
        for capture in captures:
            new_my_men, new_my_kings, new_opp_men, new_opp_kings = simulate_move(
                my_men, my_kings, opp_men, opp_kings, capture, next_color, next_direction)
                
            score = minimax(new_my_men, new_my_kings, new_opp_men, new_opp_kings, 
                           color, direction, depth-1, alpha, beta, not maximizing, start_time)
                           
            if maximizing:
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
            else:
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                
            if beta <= alpha:
                break
                
        return best_score
        
    else:
        # No captures, use non-capture moves
        moves = find_all_non_capture_moves(my_men, my_kings, next_color, next_direction)
        if not moves:  # No legal moves - loss for the player whose turn it is
            if maximizing:
                return -10000  # Loss for maximizer
            else:
                return 10000   # Win for maximizer
                
        best_score = float('-inf') if maximizing else float('inf')
        
        for move in moves:
            new_my_men, new_my_kings, new_opp_men, new_opp_kings = simulate_move(
                my_men, my_kings, opp_men, opp_kings, move, next_color, next_direction)
                
            score = minimax(new_my_men, new_my_kings, new_opp_men, new_opp_kings, 
                           color, direction, depth-1, alpha, beta, not maximizing, start_time)
                           
            if maximizing:
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
            else:
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                
            if beta <= alpha:
                break
                
        return best_score

def evaluate_position(my_men, my_kings, opp_men, opp_kings, color):
    """Evaluate the current position"""
    score = 0
    
    # Material count
    piece_count = len(my_men) + 3 * len(my_kings)
    opp_piece_count = len(opp_men) + 3 * len(opp_kings)
    score += piece_count
    score -= opp_piece_count
    
    # Mobility
    my_direction = -1 if color == 'b' else 1
    opp_direction = 1 if color == 'b' else -1
    
    my_mobility = len(find_all_non_capture_moves(my_men, my_kings, color, my_direction))
    opp_mobility = len(find_all_non_capture_moves(opp_men, opp_kings, 'w' if color == 'b' else 'b', opp_direction))
    
    score += 0.1 * my_mobility
    score -= 0.1 * opp_mobility
    
    # Center control
    center_control = 0
    for r, c in my_men:
        if 2 <= r <= 5 and 2 <= c <= 5:
            center_control += 0.2
    for r, c in my_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            center_control += 0.4
    for r, c in opp_men:
        if 2 <= r <= 5 and 2 <= c <= 5:
            center_control -= 0.2
    for r, c in opp_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            center_control -= 0.4
    score += center_control
    
    # Advancement
    advancement = 0
    if color == 'b':  # black moves down
        for r, c in my_men:
            advancement += (7 - r) * 0.1
        for r, c in my_kings:
            advancement += (7 - r) * 0.2
        for r, c in opp_men:
            advancement -= r * 0.1
        for r, c in opp_kings:
            advancement -= r * 0.2
    else:  # white moves up
        for r, c in my_men:
            advancement += r * 0.1
        for r, c in my_kings:
            advancement += r * 0.2
        for r, c in opp_men:
            advancement -= (7 - r) * 0.1
        for r, c in opp_kings:
            advancement -= (7 - r) * 0.2
    score += advancement
    
    # King safety - avoid giving opponent easy captures
    # Penalize edge pieces (except kings on safe side)
    edge_penalty = 0
    edge_positions = [(0,0), (0,2), (0,4), (0,6), (7,0), (7,2), (7,4), (7,6), (2,0), (4,0), (6,0), (2,7), (4,7), (6,7)]
    for piece in my_men:
        if piece in edge_positions and piece[0] not in [0, 7]:  # not on back row
            edge_penalty -= 0.3
    for piece in my_kings:
        if piece in [(0,0), (0,6), (7,0), (7,6)]:  # corners
            edge_penalty += 0.5
            
    score += edge_penalty
    
    # If game almost over (few pieces) give more weight to piece count
    total_pieces = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)
    if total_pieces <= 8:
        score *= 2  # weight material more heavily in endgame
        
    return score
