
def policy(state: list[list[object]], role: str) -> str:
    # Parse the state to find leaves and player positions
    leaves = set()
    players = {}
    
    for fact in state:
        if fact[0] == "leaf":
            leaves.add((int(fact[1]), int(fact[2])))
        elif fact[0] == "isplayer":
            pos = (int(fact[1]), int(fact[2]))
            player_role = fact[3]
            players[player_role] = pos
    
    # Get current player position
    if role not in players:
        # Fallback - shouldn't happen in valid states
        return "move(0,0)"
    
    current_pos = players[role]
    current_x, current_y = current_pos
    
    # Find all adjacent cells with leaves
    adjacent_moves = []
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    
    for dx, dy in directions:
        new_x, new_y = current_x + dx, current_y + dy
        if (new_x, new_y) in leaves:
            adjacent_moves.append((new_x, new_y))
    
    # If no moves available, this shouldn't happen in valid game state
    if not adjacent_moves:
        return "move(0,0)"
    
    # Scoring function: prefer moves that keep us mobile and limit opponent
    def score_move(pos):
        x, y = pos
        # Count how many leaves would be adjacent after this move
        future_leaves = leaves - {current_pos}  # After eating current leaf
        future_adjacent = 0
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (nx, ny) in future_leaves and (nx, ny) != current_pos:
                future_adjacent += 1
        
        # Prefer positions with more adjacent leaves (stay mobile)
        score = future_adjacent
        
        # Secondary: prefer moving towards center (x=4, y=4 on a 7x7 board)
        center_x, center_y = 4, 4
        dist_to_center = abs(x - center_x) + abs(y - center_y)
        score += 10 - dist_to_center  # Normalize for typical board sizes
        
        return score
    
    # Choose the best move
    best_move = max(adjacent_moves, key=score_move)
    
    return f"move({best_move[0]},{best_move[1]})"
