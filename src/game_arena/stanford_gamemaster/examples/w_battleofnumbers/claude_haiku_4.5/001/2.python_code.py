
def policy(state: list[list[object]], role: str) -> str:
    # Parse board state
    cells = {}  # (row, col) -> (number, owner)
    for fact in state:
        if fact[0] == "cell":
            col, row, number, owner = int(fact[1]), int(fact[2]), int(fact[3]), fact[4]
            cells[(row, col)] = (number, owner)
    
    # Determine opponent role
    opponent = "green" if role == "red" else "red"
    
    # Determine direction of movement (red moves right, green moves left)
    direction = 1 if role == "red" else -1
    target_col = 5 if role == "red" else 1
    
    # Generate all legal moves
    legal_moves = []
    
    for (row, col), (number, owner) in cells.items():
        if owner != role:
            continue
        
        # Generate all possible destination cells (orthogonal and diagonal)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                new_row, new_col = row + dr, col + dc
                
                # Check bounds
                if not (1 <= new_row <= 5 and 1 <= new_col <= 5):
                    continue
                
                # Check if destination is occupied
                if (new_row, new_col) in cells:
                    target_num, target_owner = cells[(new_row, new_col)]
                    
                    # Can only capture diagonally
                    if abs(dr) != 1 or abs(dc) != 1:
                        continue
                    
                    # Can only capture opponent pieces
                    if target_owner != opponent:
                        continue
                    
                    # Check capture rules: number eats equal or smaller, except 1 eats 5
                    can_capture = False
                    if number == 1 and target_num == 5:
                        can_capture = True
                    elif number >= target_num and not (number == 5 and target_num == 1):
                        can_capture = True
                    
                    if can_capture:
                        move_str = f"move({col},{row},{new_col},{new_row})"
                        legal_moves.append((move_str, number, True, target_num))
                else:
                    # Non-capture move
                    move_str = f"move({col},{row},{new_col},{new_row})"
                    legal_moves.append((move_str, number, False, 0))
    
    # Score moves
    def score_move(move_info):
        move_str, number, is_capture, captured_num = move_info
        
        # Extract coordinates from move string
        parts = move_str[5:-1].split(',')
        from_col, from_row, to_col, to_row = map(int, parts)
        
        score = 0
        
        # Captures are valuable
        if is_capture:
            score += 1000  # Base capture bonus
            score += captured_num * 100  # Bonus for capturing higher value pieces
            if captured_num == 5:
                score += 500  # Extra bonus for capturing 5
        
        # Forward movement bonus (moving toward opponent's side)
        col_movement = abs(to_col - target_col)
        prev_col_movement = abs(from_col - target_col)
        if col_movement < prev_col_movement:
            score += 50 * (prev_col_movement - col_movement)
        
        # Penalty for moving backward
        if direction == 1 and to_col < from_col:
            score -= 200
        elif direction == -1 and to_col > from_col:
            score -= 200
        
        # Bonus for moving higher-value pieces
        if number >= 4:
            score += 30
        
        return score
    
    if not legal_moves:
        # Fallback: return any valid move (shouldn't happen in normal play)
        return "move(1,1,1,2)"
    
    # Sort by score and return best move
    legal_moves.sort(key=score_move, reverse=True)
    return legal_moves[0][0]
