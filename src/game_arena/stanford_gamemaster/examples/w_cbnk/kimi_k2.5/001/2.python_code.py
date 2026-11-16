
def policy(state: list[list[object]], role: str) -> str:
    # Parse the state
    board = {}  # (x, y) -> color
    control = None
    
    for fact in state:
        if len(fact) == 0:
            continue
        if fact[0] == "location" and len(fact) == 4:
            x = int(fact[1])
            y = int(fact[2])
            color = fact[3]
            board[(x, y)] = color
        elif fact[0] == "control" and len(fact) == 2:
            control = fact[1]
    
    # If not our turn or no control info, return noop
    if control != role:
        return "noop"
    
    opponent = "red" if role == "black" else "black"
    
    def is_empty(x, y):
        return 1 <= x <= 8 and 1 <= y <= 8 and (x, y) not in board
    
    def is_opponent(x, y):
        return board.get((x, y)) == opponent
    
    # Barrel coordinate helpers
    def next_y(y):
        """Move forward one step for current role"""
        if role == "black":
            return (y % 8) + 1  # 1->2, 8->1
        else:
            return (y - 2) % 8 + 1  # 1->8, 8->7
    
    def next2_y(y):
        """Move forward two steps (jump landing) for current role"""
        if role == "black":
            return ((y + 1) % 8) + 1  # y+2
        else:
            return (y - 3) % 8 + 1  # y-2
    
    def y_plus(y):
        """y+1 with wrap"""
        return (y % 8) + 1
    
    def y_minus(y):
        """y-1 with wrap"""
        return (y - 2) % 8 + 1
    
    # Check if a piece at (x,y) can be captured by opponent
    def can_be_captured(x, y):
        if role == "black":
            # Red captures by moving down (decreasing y)
            # Red at (x-1, y+1) jumps to (x+1, y-1) over (x,y)
            # Red at (x+1, y+1) jumps to (x-1, y-1) over (x,y)
            yp = y_plus(y)
            ym = y_minus(y)
            # Left threat: red at (x-1, y+1), landing at (x+1, y-1)
            if x > 1 and (x-1, yp) in board and board[(x-1, yp)] == opponent:
                if x < 8 and is_empty(x+1, ym):
                    return True
            # Right threat: red at (x+1, y+1), landing at (x-1, y-1)
            if x < 8 and (x+1, yp) in board and board[(x+1, yp)] == opponent:
                if x > 1 and is_empty(x-1, ym):
                    return True
        else:
            # Black captures by moving up (increasing y)
            # Black at (x-1, y-1) jumps to (x+1, y+1) over (x,y)
            # Black at (x+1, y-1) jumps to (x-1, y+1) over (x,y)
            yp = y_plus(y)
            ym = y_minus(y)
            # Left threat: black at (x-1, y-1), landing at (x+1, y+1)
            if x > 1 and (x-1, ym) in board and board[(x-1, ym)] == opponent:
                if x < 8 and is_empty(x+1, yp):
                    return True
            # Right threat: black at (x+1, y-1), landing at (x-1, y+1)
            if x < 8 and (x+1, ym) in board and board[(x+1, ym)] == opponent:
                if x > 1 and is_empty(x-1, yp):
                    return True
        return False
    
    # Generate legal actions
    jumps = []  # (x_from, y_from, x_over, y_over, x_to, y_to)
    moves = []  # (x_from, y_from, x_to, y_to)
    
    my_pieces = [(x, y) for (x, y), color in board.items() if color == role]
    
    for (x, y) in my_pieces:
        y1 = next_y(y)
        y2 = next2_y(y)
        
        # Left diagonal
        if x > 1:
            if is_empty(x-1, y1):
                moves.append((x, y, x-1, y1))
            elif x > 2 and is_opponent(x-1, y1) and is_empty(x-2, y2):
                jumps.append((x, y, x-1, y1, x-2, y2))
        
        # Right diagonal
        if x < 8:
            if is_empty(x+1, y1):
                moves.append((x, y, x+1, y1))
            elif x < 7 and is_opponent(x+1, y1) and is_empty(x+2, y2):
                jumps.append((x, y, x+1, y1, x+2, y2))
    
    def format_move(m):
        return f"move({m[0]},{m[1]},{m[2]},{m[3]})"
    
    def format_jump(j):
        return f"jump({j[0]},{j[1]},{j[2]},{j[3]},{j[4]},{j[5]})"
    
    # Prioritize jumps (captures)
    if jumps:
        best_jump = None
        best_score = -1000
        
        for j in jumps:
            x_from, y_from, x_over, y_over, x_to, y_to = j
            score = 0
            
            # Prefer central landing (x=4 or 5)
            score += 4.5 - abs(x_to - 4.5)
            
            # Prefer advancement
            if role == "black":
                score += y_to * 0.5
            else:
                score += (9 - y_to) * 0.5
            
            # Prefer safe landing
            if not can_be_captured(x_to, y_to):
                score += 10
            
            if score > best_score:
                best_score = score
                best_jump = j
        
        return format_jump(best_jump)
    
    # If no jumps, choose best move
    if moves:
        best_move = None
        best_score = -1000
        
        for m in moves:
            x_from, y_from, x_to, y_to = m
            score = 0
            
            # Centrality bonus
            score += 4.5 - abs(x_to - 4.5)
            
            # Advancement bonus
            if role == "black":
                score += y_to * 0.3
            else:
                score += (9 - y_to) * 0.3
            
            # Safety bonus
            if not can_be_captured(x_to, y_to):
                score += 5
            
            if score > best_score:
                best_score = score
                best_move = m
        
        return format_move(best_move)
    
    # No legal moves available
    return "noop"
