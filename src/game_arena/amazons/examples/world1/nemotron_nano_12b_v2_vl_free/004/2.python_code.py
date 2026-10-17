
import numpy as np

def policy(board):
    my_amazons = list(np.argwhere(board == 1))
    if not my_amazons:
        return ""
    
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    candidates = []
    
    for from_pos in my_amazons:
        from_r, from_c = from_pos
        
        for move_dr, move_dc in directions:
            step = 1
            while True:
                newr = from_r + move_dr * step
                newc = from_c + move_dc * step
                
                if newr < 0 or newr >= 6 or newc < 0 or newc >= 6:
                    break
                if board[newr, newc] != 0:
                    break
                
                # Generate new board state after moving the amazon
                temp_board = board.copy()
                temp_board[from_r, from_c] = 0
                temp_board[newr, newc] = 1
                
                moved_pos = (newr, newc)
                
                # Generate all possible arrows
                for arrow_dr, arrow_dc in directions:
                    arrow_positions = []
                    step_arrow = 1
                    while True:
                        ar = newr + arrow_dr * step_arrow
                        ac = newc + arrow_dc * step_arrow
                        if not (0 <= ar < 6 and 0 <= ac < 6):
                            break
                        if temp_board[ar, ac] != 0:
                            break
                        arrow_positions.append((ar, ac))
                        step_arrow += 1
                    
                    # If arrows are possible in this direction
                    if arrow_positions:
                        # Move through the arrow positions in reverse order to get the longest path
                        arrow_positions_rev = arrow_positions[::-1]
                        ar, ac = arrow_positions_rev[0]
                        move_str = f"{from_r},{from_c}:{new_r},{newc}:{ar},{ac}"
                        candidates.append(move_str)
                
                # Exit loop after finding the first move in a direction
                break
    
    if not candidates:
        return "0,0:0,1:0,0"  # Default fallback (should not occur)
    
    # Select candidate with longest arrow and highest mobility
    best_candidate = None
    best_arrow_length = -1
    best_candidate_move_str = None
    
    for move_str in candidates:
        from_indices = move_str.split(':')
        new_board = board.copy()
        from_r_shot = int(from_indices[0])
        from_c_shot = int(from_indices[1])
        new_r = int(from_indices[2])
        new_c = int(from_indices[3])
        ar = int(from_indices[4])
        ac = int(from_indices[5])
        
        # Simulate the new board with arrow shot
        new_board = board.copy()
        new_board[from_r_shot, from_c_shot] = 0
        new_board[new_r, new_c] = 1
        new_board[ar, ac] = -1  # Block with arrow
        
        # Calculate mobility after arrow is placed
        mobility = 0
        for arrow_dir in directions:
            leg = 0
            ar_check = new_r
            ac_check = new_c
            while True:
                ar_check += arrow_dir[0]
                ac_check += arrow_dir[1]
                if not (0 <= ar_check < 6 and 0 <= ac_check < 6) or new_board[ar_check, ac_check] != 0:
                    break
                leg += 1
            mobility += leg
        
        # Calculate arrow length
        ar_start_r = ar - arrow_dr * len(arrow_positions_rev)
        ar_start_c = ac - arrow_dc * len(arrow_positions_rev)
        arrow_length = len(arrow_positions)
        
        if arrow_length > best_arrow_length:
            best_arrow_length = arrow_length
            best_candidate_move_str = move_str
        elif arrow_length == best_arrow_length:
            if mobility > best_mobility:
                best_mobility = mobility
                best_candidate_move_str = move_str
    
    return best_candidate_move_str
