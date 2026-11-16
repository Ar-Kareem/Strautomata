
import numpy as np

def policy(board):
    directions = [(-1, -1), (-1, 0), (-1, 1), 
                  (0, -1),          (0, 1), 
                  (1, -1),  (1, 0), (1, 1)]
    
    # Find all enemy Amazons
    enemy_amazons = list(zip(*np.where(board == 2)))
    if not enemy_amazons:
        # No enemies, focus on center control
        pass
    
    our_amazons = list(zip(*np.where(board == 1)))
    best_move = None
    best_heuristic = float('-inf')
    
    for (from_r, from_c) in our_amazons:
        possible_moves = []
        for dr, dc in directions:
            step = 1
            while True:
                nr = from_r + dr * step
                nc = from_c + dc * step
                if nr < 0 or nr >= 6 or nc < 0 or nc >= 6:
                    break
                if board[nr][nc] != 0:
                    break
                possible_moves.append((nr, nc))
                step += 1
        
        for (to_r, to_c) in possible_moves:
            # Evaluate all possible arrow shots from (to_r, to_c)
            arrow_directions = []
            for dr, dc in directions:
                steps = 1
                arrow_pos = []
                while True:
                    ar_r = to_r + dr * steps
                    ar_c = to_c + dc * steps
                    if ar_r < 0 or ar_r >= 6 or ar_c < 0 or ar_c >= 6:
                        break
                    if board[ar_r][ar_c] != 0:
                        break
                    arrow_pos.append((ar_r, ar_c))
                    steps += 1
                if arrow_pos:
                    arrow_directions.extend([(ar_r, ar_c, dr, dc) for ar_r, ar_c in arrow_pos])
            
            if not arrow_directions:
                continue  # Skip this move since no arrow can be shot
            
            # Evaluate each arrow direction for enemy presence
            max_enemy_score = 0
            best_arrow = None
            for (ar_r, ar_c, ar_dr, ar_dc) in arrow_directions:
                enemy_count = 0
                # Check if there are enemies in the direction of the arrow
                for (e_r, e_c) in enemy_amazons:
                    delta_r = e_r - to_r
                    delta_c = e_c - to_c
                    if delta_r * ar_dc == delta_c * ar_dr:
                        # Determine direction consistency
                        is_same_dir = True
                        for delta_step in 1, 2:
                            test_r = to_r + ar_dr * delta_step
                            test_c = to_c + ar_dc * delta_step
                            if (test_r == e_r and test_c == e_c) or (test_r == to_r and test_c == to_c):
                                is_same_dir = True
                                break
                            if not (0 <= test_r < 6 and 0 <= test_c < 6):
                                is_same_dir = False
                                break
                            if board[test_r][test_c] != 0:
                                is_same_dir = False
                                break
                        if not is_same_dir:
                            continue
                        # Calculate distance
                        distance = max(abs(e_r - to_r), abs(e_c - to_c))
                        enemy_count += 1 / max(1, distance)  # Prefer closer enemies
                if enemy_count > max_enemy_score:
                    max_enemy_score = enemy_count
                    best_arrow = (ar_r, ar_c)
            
            if best_arrow:
                # Evaluate move heuristic (e.g., distance to center, arrows blocking enemies)
                move_distance_to_center = abs(5 - to_r) + abs(5 - to_c)
                arrow_enemy_benefit = max_enemy_score
                # Move closer to center after considering enemy arrows
                heuristic = -move_distance_to_center + arrow_enemy_benefit
            else:
                # Fallback to arbitrary arrow direction
                best_arrow = arrow_directions[0][0], arrow_directions[0][1]
                heuristic = - (abs(5 - to_r) + abs(5 - to_c))
            
            if heuristic > best_heuristic or (heuristic == best_heuristic and best_move is None):
                best_heuristic = heuristic
                best_move = (from_r, from_c, to_r, to_c, best_arrow[0], best_arrow[1])
    
    if best_move:
        fr, fc, to_r, to_c, ar_r, ar_c = best_move
        return f"{fr},{fc}:{to_r},{to_c}:{ar_r},{ar_c}"
    else:
        # Fallback to any legal move (shouldn't happen as per problem constraints)
        for from_r, from_c in our_amazons:
            for dr, dc in directions:
                step = 1
                while True:
                    to_r = from_r + dr * step
                    to_c = from_c + dc * step
                    if not (0 <= to_r < 6 and 0 <= to_c < 6):
                        break
                    if board[to_r][to_c] != 0:
                        break
                    # Find any possible arrow
                    for ar_dir in directions:
                        steps = 1
                        while True:
                            ar_r = to_r + ar_dir[0] * steps
                            ar_c = to_c + ar_dir[1] * steps
                            if not (0 <= ar_r < 6 and 0 <= ar_c < 6):
                                break
                            if board[ar_r][ar_c] != 0:
                                break
                            # Found valid arrow, return move
                            return f"{from_r},{from_c}:{to_r},{to_c}:{ar_r},{ar_c}"
                    steps += 1
        return "0,0:0,0:0,0"
