
import numpy as np
from itertools import chain
from collections import defaultdict

def policy(my_men, my_kings, opp_men, opp_kings, color):
    all_my_pieces = my_men + my_kings
    all_opp_pieces = opp_men + opp_kings
    all_pieces = set(all_my_pieces + all_opp_pieces)
    is_king = lambda piece: piece in my_kings or piece in opp_kings
    
    # Get all possible captures
    max_captures = []
    max_capture_count = 0
    
    def search_captures(start, path, captured, current_piece):
        nonlocal max_captures, max_capture_count
        from_row, from_col = start
        is_k = current_piece in my_kings
        
        found = False
        for dx, dy in [(1,1), (1,-1), (-1,1), (-1,-1)] if is_k else \
                      [(1,1), (1,-1)] if color == 'b' else [(-1,1), (-1,-1)]:
            # Check for opponent piece to capture
            mid_r, mid_c = from_row + dx, from_col + dy
            land_r, land_c = from_row + 2*dx, from_col + 2*dy
            
            if (mid_r, mid_c) in all_opp_pieces and \
               0 <= land_r < 8 and 0 <= land_c < 8 and \
               (land_r, land_c) not in all_pieces and \
               (land_r, land_c) not in path and \
               (mid_r, mid_c) not in captured:
                
                new_path = path + [(land_r, land_c)]
                new_captured = captured + [(mid_r, mid_c)]
                search_captures((land_r, land_c), new_path, new_captured, current_piece)
                found = True
        
        if not found and len(captured) > 0:
            if len(captured) > max_capture_count:
                max_capture_count = len(captured)
                max_captures = [((current_piece[0], current_piece[1]), path[-1])]
            elif len(captured) == max_capture_count:
                max_captures.append(((current_piece[0], current_piece[1]), path[-1]))
    
    # Find all possible captures
    for piece in all_my_pieces:
        search_captures(piece, [piece], [], piece)
    
    if max_capture_count > 0:
        # Select best capture: prioritize kinging and center positions
        def capture_score(move):
            from_pos, to_pos = move
            score = 0
            # King promotion
            if from_pos not in my_kings:
                if (color == 'b' and to_pos[0] == 0) or (color == 'w' and to_pos[0] == 7):
                    score += 100
            # Center control
            center_dist = abs(to_pos[0] - 3.5) + abs(to_pos[1] - 3.5)
            score += (7 - center_dist) * 0.5
            return score
        
        best_capture = max(max_captures, key=capture_score)
        return best_capture
    
    # No captures available - find best regular move
    possible_moves = []
    
    for piece in all_my_pieces:
        from_row, from_col = piece
        is_k = piece in my_kings
        
        # Possible movement directions
        directions = [(1,1), (1,-1), (-1,1), (-1,-1)] if is_k else \
                     [(1,1), (1,-1)] if color == 'b' else [(-1,1), (-1,-1)]
        
        for dx, dy in directions:
            to_row, to_col = from_row + dx, from_col + dy
            if 0 <= to_row < 8 and 0 <= to_col < 8 and (to_row, to_col) not in all_pieces:
                possible_moves.append(((from_row, from_col), (to_row, to_col)))
    
    if not possible_moves:
        # Shouldn't happen (stalemate), but return random valid move to avoid disqualification
        return ((0,0), (0,0))
    
    # Evaluate regular moves
    def move_score(move):
        from_pos, to_pos = move
        score = 0
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # King promotion
        if from_pos not in my_kings:
            if (color == 'b' and to_row == 0) or (color == 'w' and to_row == 7):
                score += 10
        
        # Safe position (not immediately capturable)
        safe = True
        opp_dir = -1 if color == 'b' else 1
        for dx, dy in [(opp_dir, 1), (opp_dir, -1)]:
            r, c = to_row + dx, to_col + dy
            if 0 <= r < 8 and 0 <= c < 8 and (r, c) in all_opp_pieces:
                jump_r, jump_c = to_row - dx, to_col - dy
                if (jump_r, jump_c) not in all_pieces:
                    if (r, c) in opp_kings or (dx == opp_dir and color == 'b') or (dx == -opp_dir and color == 'w'):
                        safe = False
                        break
        if safe:
            score += 5
        
        # Progress toward promotion
        if color == 'b':
            score += (7 - from_row - to_row) * 0.5
        else:
            score += (from_row - to_row) * 0.5
        
        # Center control
        center_dist = abs(to_row - 3.5) + abs(to_col - 3.5)
        score += (7 - center_dist) * 0.2
        
        return score
    
    best_move = max(possible_moves, key=move_score)
    return best_move
