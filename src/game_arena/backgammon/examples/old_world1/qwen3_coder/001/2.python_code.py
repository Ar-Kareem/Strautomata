
import numpy as np

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # If no dice, pass
    if not dice:
        return "H:P,P"
    
    # Generate all legal moves
    moves = generate_legal_moves(my_pts, opp_pts, my_bar, dice)
    
    # If no legal moves, pass
    if not moves:
        return "H:P,P"
    
    # Evaluate each move and select the best one
    best_move = None
    best_score = float('-inf')
    
    for move in moves:
        score = evaluate_move(my_pts, opp_pts, my_bar, opp_off, move, dice)
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move, dice)

def generate_legal_moves(my_pts, opp_pts, my_bar, dice):
    """Generate all legal moves based on current state and dice."""
    moves = []
    
    if len(dice) == 0:
        return moves
    
    # If we have checkers on bar, we must move them first
    if my_bar > 0:
        return generate_bar_moves(my_pts, opp_pts, my_bar, dice)
    
    # Otherwise generate moves from points
    return generate_point_moves(my_pts, opp_pts, dice)

def generate_bar_moves(my_pts, opp_pts, my_bar, dice):
    """Generate moves when we have checkers on the bar."""
    moves = []
    
    for die in dice:
        # Check if we can enter from bar with this die
        enter_point = die - 1  # Point where we enter (0-indexed)
        # In backgammon, entering from bar with die n means landing on point n
        # But since our perspective is from our side, this point is 24 - die
        enter_point = 24 - die
        
        if enter_point >= 0 and enter_point < 24:
            if opp_pts[enter_point] < 2:  # Can enter if point is not blocked
                # Create a move with this die
                moves.append([('B', die)])
    
    # If we have two dice and can make both moves
    if len(dice) == 2:
        move1 = None
        move2 = None
        
        # Try first die
        enter_point1 = 24 - dice[0]
        if 0 <= enter_point1 < 24 and opp_pts[enter_point1] < 2:
            move1 = ('B', dice[0])
        
        # Try second die
        enter_point2 = 24 - dice[1]
        if 0 <= enter_point2 < 24 and opp_pts[enter_point2] < 2:
            move2 = ('B', dice[1])
        
        # If both moves are possible, add them as one move
        if move1 and move2:
            moves.append([move1, move2])
        elif move1:
            moves.append([move1])
        elif move2:
            moves.append([move2])
    
    return moves

def generate_point_moves(my_pts, opp_pts, dice):
    """Generate moves from points when no checkers are on bar."""
    moves = []
    
    if len(dice) == 1:
        die = dice[0]
        for point in range(24):
            if my_pts[point] > 0:
                dest = point - die  # Moving toward home (0)
                if dest >= 0 and opp_pts[dest] < 2:
                    moves.append([(f"A{point}", die)])
    elif len(dice) == 2:
        # Try both orderings of dice
        for first_die, second_die in [(dice[0], dice[1]), (dice[1], dice[0])]:
            # Try first move
            first_moves = []
            for point in range(24):
                if my_pts[point] > 0:
                    dest = point - first_die
                    if dest >= 0 and opp_pts[dest] < 2:
                        first_moves.append((point, dest, first_die))
            
            # For each first move, try second move
            for point1, dest1, die1 in first_moves:
                # Apply first move temporarily
                temp_my_pts = list(my_pts)
                temp_my_pts[point1] -= 1
                if dest1 >= 0:
                    temp_my_pts[dest1] += 1
                
                # Try second move from new position
                for point2 in range(24):
                    if temp_my_pts[point2] > 0:
                        dest2 = point2 - second_die
                        if dest2 >= 0 and opp_pts[dest2] < 2:
                            moves.append([(f"A{point1}", die1), (f"A{point2}", second_die)])
                
                # Also try bearing off with second die if in home board
                # Check if all checkers are in home board for bearing off
                if all(i < 6 for i in range(24) if temp_my_pts[i] > 0):
                    # Try bearing off
                    for point2 in range(6):  # Home board points (0-5)
                        if temp_my_pts[point2] > 0:
                            if point2 - second_die < 0:  # Can bear off
                                moves.append([(f"A{point1}", die1), (f"A{point2}", second_die)])
    
    return moves

def evaluate_move(my_pts, opp_pts, my_bar, opp_off, move, dice):
    """Evaluate a move and return a score."""
    score = 0
    
    # Prefer moves that get checkers off the bar
    if my_bar > 0:
        for move_part in move:
            if move_part[0] == 'B':
                score += 20  # High priority for getting off bar
    
    # Consider the safety of moved pieces
    for move_part in move:
        from_pos = move_part[0]
        die = move_part[1]
        
        if from_pos != 'B':
            point = int(from_pos[1:])
            dest = point - die
            
            # Prefer moving from points with multiple checkers (safety in numbers)
            if my_pts[point] > 1:
                score += 2
            
            # Prefer moving to points that are safe (not easily hit)
            if dest >= 0 and dest < 24:
                # Point is safe if we land on it with 2+ checkers or if it's blocked for opponent
                if my_pts[point] - 1 + (1 if dest >= 0 else 0) >= 2:
                    score += 3
                
                # Prefer points that block opponent
                if opp_pts[dest] == 1:
                    score += 5  # Hitting opponent checker
    
    # Prefer bearing off when possible
    # Check if we can bear off
    home_board_occupied = any(my_pts[i] > 0 for i in range(6))
    if home_board_occupied and all(i >= 6 or my_pts[i] == 0 for i in range(6, 24)):
        # All checkers in home board, prefer bearing off
        for move_part in move:
            from_pos = move_part[0]
            die = move_part[1]
            if from_pos != 'B':
                point = int(from_pos[1:])
                if point < 6 and point - die < 0:  # Bearing off
                    score += 15
    
    # Prefer advancing checkers
    for move_part in move:
        from_pos = move_part[0]
        die = move_part[1]
        if from_pos != 'B':
            point = int(from_pos[1:])
            dest = point - die
            if dest >= 0:
                # Prefer moving checkers toward home
                score += (23 - point) * 0.1
                # Prefer larger moves when safe
                score += die * 0.2
    
    # Prefer making points (landing with exactly 2 checkers)
    for move_part in move:
        from_pos = move_part[0]
        die = move_part[1]
        if from_pos != 'B':
            point = int(from_pos[1:])
            dest = point - die
            if dest >= 0:
                # If landing would make a point (2 checkers)
                if my_pts[point] + (1 if dest >= 0 and dest < 24 else 0) == 2:
                    score += 8
    
    return score

def format_move(move, dice):
    """Format a move according to the required format."""
    if not move:
        return "H:P,P"
    
    # Default to higher die first
    order = "H"
    die1_val = dice[0]
    die2_val = dice[1] if len(dice) > 1 else None
    
    # If we have two dice, we might want to use the lower die first
    if len(dice) > 1 and len(move) > 1:
        # Check which die is used first in our move
        first_move_die = move[0][1]
        if first_move_die == min(dice):
            order = "L"
    
    from1 = "P"
    from2 = "P"
    
    if len(move) > 0:
        from1 = move[0][0]
    if len(move) > 1:
        from2 = move[1][0]
    
    return f"{order}:{from1},{from2}"
