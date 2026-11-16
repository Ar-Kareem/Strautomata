
def policy(you, opponent):
    direction_map = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}
    
    # Generate all possible moves
    possible_moves = []
    for row in range(5):
        for col in range(6):
            pos = row * 6 + col
            if you[pos]:
                for dir_name in direction_map:
                    dr, dc = direction_map[dir_name]
                    new_row = row + dr
                    new_col = col + dc
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        if opponent[new_row * 6 + new_col]:
                            possible_moves.append((row, col, dir_name))
    
    if not possible_moves:
        # According to problem constraints, this should not occur
        return '0,0,U'  # Fallback move (should never be used)
    
    best_move = possible_moves[0]
    min_opponent_moves = float('inf')
    
    direction_values = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    
    for move in possible_moves:
        r, c, d = move
        dr, dc = direction_values[{'U':0, 'R':1, 'D':2, 'L':3}[d]]
        new_row = r + dr
        new_col = c + dc
        
        # Apply move to new_you and new_opponent
        new_you = list(you)
        new_opponent = list(opponent)
        current_pos = r * 6 + c
        new_you[current_pos] = 0
        new_opponent[new_row * 6 + new_col] = 0
        new_you[new_row * 6 + new_col] = 1
        
        # Count opponent's possible moves after this move
        count = 0
        for opp_row in range(5):
            opp_row_pos = opp_row * 6
            for opp_col in range(6):
                if new_opponent[opp_row_pos + opp_col]:
                    for odr, odc in direction_values:
                        o_new_r = opp_row + odr
                        o_new_c = opp_col + odc
                        if 0 <= o_new_r < 5 and 0 <= o_new_c < 6:
                            target_pos = o_new_r * 6 + o_new_c
                            if new_you[target_pos]:
                                count += 1
                                break  # No need to check other directions for this cell
        
        # Check if this move results in opponent having no moves
        if count == 0:
            return f"{r},{c},{d}"
        
        if count < min_opponent_moves:
            min_opponent_moves = count
            best_move = move
    
    r, c, d = best_move
    return f"{r},{c},{d}"
