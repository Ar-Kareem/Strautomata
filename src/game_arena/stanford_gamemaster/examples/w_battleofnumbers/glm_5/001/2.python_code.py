
def policy(state, role):
    """
    Policy for Battle of Numbers game.
    Returns the best legal move for the given role.
    """
    
    def can_capture(attacker, defender):
        """Check if attacker can capture defender based on game rules."""
        if attacker == 5 and defender == 1:
            return False
        if attacker == 1 and defender == 5:
            return True
        return attacker >= defender
    
    # Parse board state
    board = {}
    my_pieces = []
    opponent = "green" if role == "red" else "red"
    
    for prop in state:
        if prop[0] == "cell":
            row = int(prop[1])
            col = int(prop[2])
            num = int(prop[3])
            color = prop[4]
            board[(row, col)] = (num, color)
            if color == role:
                my_pieces.append((row, col, num))
    
    # Forward direction: red moves right (+1), green moves left (-1)
    forward_dc = 1 if role == "red" else -1
    
    # Generate all legal moves
    moves = []
    
    for r, c, num in my_pieces:
        # Normal moves (forward only, to empty cells)
        # Forward orthogonal
        new_c = c + forward_dc
        if 1 <= new_c <= 5 and (r, new_c) not in board:
            moves.append(("move", r, c, r, new_c, num, 0))
        
        # Forward diagonal
        for dr in [-1, 1]:
            new_r = r + dr
            new_c = c + forward_dc
            if 1 <= new_r <= 5 and 1 <= new_c <= 5 and (new_r, new_c) not in board:
                moves.append(("move", r, c, new_r, new_c, num, 0))
        
        # Capture moves (diagonal only, can be forward or backward)
        for dr in [-1, 1]:
            for dc in [-1, 1]:
                new_r, new_c = r + dr, c + dc
                if 1 <= new_r <= 5 and 1 <= new_c <= 5:
                    if (new_r, new_c) in board:
                        target_num, target_color = board[(new_r, new_c)]
                        if target_color == opponent and can_capture(num, target_num):
                            moves.append(("capture", r, c, new_r, new_c, num, target_num))
    
    if not moves:
        return "noop"
    
    # Evaluate each move
    def evaluate(m):
        move_type, r1, c1, r2, c2, my_num, target_num = m
        score = 0
        
        # Captures are extremely valuable
        if move_type == "capture":
            # Higher value targets are worth more
            capture_values = {1: 400, 2: 500, 3: 700, 4: 900, 5: 2000}
            score += capture_values.get(target_num, 500)
            # Special bonus for 1 capturing 5 (excellent trade)
            if my_num == 1 and target_num == 5:
                score += 800
        
        # Advancement toward enemy territory
        advancement = (c2 - c1) if role == "red" else (c1 - c2)
        score += advancement * 25
        
        # Danger assessment: can we be captured at destination?
        danger = 0
        for dr in [-1, 1]:
            for dc in [-1, 1]:
                adj_r, adj_c = r2 + dr, c2 + dc
                if (adj_r, adj_c) in board:
                    adj_num, adj_color = board[(adj_r, adj_c)]
                    if adj_color == opponent and can_capture(adj_num, my_num):
                        piece_value = {1: 150, 2: 200, 3: 300, 4: 400, 5: 600}
                        danger = max(danger, piece_value.get(my_num, 300))
        
        # Reduce danger penalty for capture moves (sacrifice may be worth it)
        if move_type == "capture":
            danger //= 4
        score -= danger
        
        # Threat assessment: can we capture from new position?
        for dr in [-1, 1]:
            for dc in [-1, 1]:
                adj_r, adj_c = r2 + dr, c2 + dc
                if (adj_r, adj_c) in board:
                    adj_num, adj_color = board[(adj_r, adj_c)]
                    if adj_color == opponent and can_capture(my_num, adj_num):
                        threat_value = {1: 30, 2: 40, 3: 60, 4: 80, 5: 150}
                        score += threat_value.get(adj_num, 50)
        
        # Center control bonus
        center_dist = abs(r2 - 3) + abs(c2 - 3)
        score += max(0, 5 - center_dist) * 5
        
        return score
    
    # Select best move
    moves.sort(key=evaluate, reverse=True)
    best = moves[0]
    
    return f"move({best[1]},{best[2]},{best[3]},{best[4]})"
