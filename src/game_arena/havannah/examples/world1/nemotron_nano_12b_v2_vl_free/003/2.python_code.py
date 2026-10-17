
def policy(me, opp, valid_mask):
    me_set = set(me)
    opp_set = set(opp)
    best_move = None
    max_score = -float('inf')
    
    # Generate all valid candidate moves
    valid_moves = []
    for row in range(15):
        for col in range(15):
            if valid_mask[row][col]:
                pos = (row, col)
                if pos not in me_set and pos not in opp_set:
                    valid_moves.append(pos)
    
    # If no moves left (unlikely per problem statement), return first valid cell
    if not valid_moves:
        return None  # Though problem states there is a move
    
    # Evaluate each valid move's score using heuristic
    for move in valid_moves:
        row, col = move
        
        # Calculate adjacent Me and Opp stones
        sum_me = 0
        sum_opp = 0
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]
        for dr, dc in dirs:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 15 and 0 <= nc < 15:
                if valid_mask[nr][nc]:
                    if (nr, nc) in me_set:
                        sum_me += 1
                    elif (nr, nc) in opp_set:
                        sum_opp += 1
        
        # Heuristic scoring: prioritize adjacency to own stones and closeness to center
        distance_score = (row - 7) ** 2 + (col - 7) ** 2  # square of distance to center
        score = sum_me * 4 - distance_score * 5 - sum_opp * 2  # Weighted sum
        
        if score > max_score:
            max_score = score
            best_move = move
    
    return best_move
