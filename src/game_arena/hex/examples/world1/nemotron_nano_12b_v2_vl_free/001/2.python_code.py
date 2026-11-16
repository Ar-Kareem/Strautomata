
def policy(me, opp, color):
    my_stones = set(me)
    opp_stones = set(opp)
    
    legal_moves = []
    for x in range(11):
        for y in range(11):
            if (x, y) not in my_stones and (x, y) not in opp_stones:
                legal_moves.append((x, y))
                
    # Handle first move specially
    if not me:
        if color == 'b':
            return (5, 4)
        else:
            return (4, 5)
    
    best_score = float('-inf')
    best_move = legal_moves[0]  # Initialize with a default move
    
    for cell in legal_moves:
        x, y = cell
        
        my_adj = 0
        opp_adj = 0
        
        # Define adjacency directions based on Hex's hex grid
        neighbors = [
            (x-1, y),
            (x+1, y),
            (x, y-1),
            (x, y+1),
            (x-1, y+1),
            (x+1, y-1),
        ]
        
        for nx, ny in neighbors:
            if 0 <= nx < 11 and 0 <= ny < 11:
                if (nx, ny) in my_stones:
                    my_adj += 1
                elif (nx, ny) in opp_stones:
                    opp_adj += 1
        
        # Base score prioritizing adjacency to my stones and penalizing opponent adjacency
        score = my_adj * 3 - opp_adj * 2
        
        # Positional bonus calculation
        if color == 'b':
            edge_dist = min(x, 10 - x)
            # Prioritize stones closer to top/bottom edges with bonus
            score += (10 - edge_dist) * 2
        else:
            # 'w' prioritizes proximity to left/right edges
            edge_dist = min(y, 10 - y)
            score += (10 - edge_dist) * 2
        
        # Update best move if current score is better
        if (score > best_score) or (score == best_score and cell < best_move):
            best_score = score
            best_move = (x, y)
            
    return best_move
