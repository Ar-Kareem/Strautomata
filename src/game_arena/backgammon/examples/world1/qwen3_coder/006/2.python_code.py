
import numpy as np

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # No dice to play
    if not dice:
        return "H:P,P"
    
    # Generate all legal moves
    moves = generate_legal_moves(my_pts, opp_pts, my_bar, dice)
    
    # If no legal moves
    if not moves:
        return "H:P,P"
    
    # Evaluate moves and pick the best one
    best_move = evaluate_moves(moves, my_pts, opp_pts, my_bar, my_off)
    
    return best_move

def generate_legal_moves(my_pts, opp_pts, my_bar, dice):
    moves = []
    
    # Must move checkers from bar first if any
    if my_bar > 0:
        return generate_bar_moves(my_pts, opp_pts, my_bar, dice)
    
    # Check if all checkers are in home board (bearing off possible)
    can_bear_off = all(my_pts[i] == 0 for i in range(6, 24))
    
    if len(dice) == 1:
        d = dice[0]
        for i in range(24):
            if my_pts[i] > 0 and is_legal_move(i, d, my_pts, opp_pts, can_bear_off):
                moves.append((d, i, None))
    else:
        # Two dice - try both orders
        d1, d2 = dice[0], dice[1]
        
        # Order 1: d1 first
        for i1 in range(24):
            if my_pts[i1] > 0 and is_legal_move(i1, d1, my_pts, opp_pts, can_bear_off):
                temp_pts = list(my_pts)
                temp_pts[i1] -= 1
                new_pos1 = i1 - d1
                if new_pos1 >= 0:
                    temp_pts[new_pos1] += 1
                
                for i2 in range(24):
                    if temp_pts[i2] > 0 and is_legal_move(i2, d2, temp_pts, opp_pts, can_bear_off):
                        moves.append((d1, i1, d2, i2))
        
        # Order 2: d2 first
        for i1 in range(24):
            if my_pts[i1] > 0 and is_legal_move(i1, d2, my_pts, opp_pts, can_bear_off):
                temp_pts = list(my_pts)
                temp_pts[i1] -= 1
                new_pos1 = i1 - d2
                if new_pos1 >= 0:
                    temp_pts[new_pos1] += 1
                
                for i2 in range(24):
                    if temp_pts[i2] > 0 and is_legal_move(i2, d1, temp_pts, opp_pts, can_bear_off):
                        moves.append((d2, i1, d1, i2))
        
        # If we can't use both dice, try using just one (higher first)
        if not moves:
            higher = max(d1, d2)
            for i in range(24):
                if my_pts[i] > 0 and is_legal_move(i, higher, my_pts, opp_pts, can_bear_off):
                    moves.append((higher, i, None))
    
    return moves

def generate_bar_moves(my_pts, opp_pts, my_bar, dice):
    moves = []
    can_bear_off = all(my_pts[i] == 0 for i in range(6, 24))
    
    if len(dice) == 1:
        d = dice[0]
        enter_pos = 24 - d
        if enter_pos >= 0 and opp_pts[enter_pos] < 2:
            moves.append((d, 'B', None))
    else:
        d1, d2 = dice[0], dice[1]
        
        # Try both orders
        # Order 1: d1 first
        enter_pos1 = 24 - d1
        if enter_pos1 >= 0 and opp_pts[enter_pos1] < 2:
            # After entering with d1, try to use d2
            temp_pts = list(my_pts)
            if enter_pos1 >= 0:
                temp_pts[enter_pos1] += 1
            
            enter_pos2 = 24 - d2
            if enter_pos2 >= 0 and opp_pts[enter_pos2] < 2:
                # Can enter both checkers
                moves.append((d1, 'B', d2, 'B'))
            else:
                # Try to move the checker that was just entered
                for i in range(24):
                    if temp_pts[i] > 0 and is_legal_move(i, d2, temp_pts, opp_pts, can_bear_off):
                        moves.append((d1, 'B', d2, i))
        
        # Order 2: d2 first
        enter_pos2 = 24 - d2
        if enter_pos2 >= 0 and opp_pts[enter_pos2] < 2:
            # After entering with d2, try to use d1
            temp_pts = list(my_pts)
            if enter_pos2 >= 0:
                temp_pts[enter_pos2] += 1
            
            enter_pos1 = 24 - d1
            if enter_pos1 >= 0 and opp_pts[enter_pos1] < 2:
                # Can enter both checkers
                moves.append((d2, 'B', d1, 'B'))
            else:
                # Try to move the checker that was just entered
                for i in range(24):
                    if temp_pts[i] > 0 and is_legal_move(i, d1, temp_pts, opp_pts, can_bear_off):
                        moves.append((d2, 'B', d1, i))
        
        # If we can't use both dice, try using just one (higher first)
        if not moves:
            higher = max(d1, d2)
            enter_pos = 24 - higher
            if enter_pos >= 0 and opp_pts[enter_pos] < 2:
                moves.append((higher, 'B', None))
    
    return moves

def is_legal_move(from_pos, die_value, my_pts, opp_pts, can_bear_off):
    # Check if from_pos has our checker
    if my_pts[from_pos] == 0:
        return False
    
    # Calculate target position
    target = from_pos - die_value
    
    # Bearing off
    if target < 0:
        if not can_bear_off:
            return False
        # When bearing off, we can only bear off from the exact die value or from the highest point
        if from_pos > 5:  # Not in home board
            return False
        # Check if all checkers are in home board (already checked in calling function)
        # Also allow bearing off from highest occupied point when die is higher than needed
        highest = -1
        for i in range(6):
            if my_pts[i] > 0:
                highest = i
                break
        if from_pos == highest or die_value == from_pos + 1:
            return True
        return False
    
    # Normal move - check if target is blocked
    if opp_pts[target] >= 2:
        return False
    
    return True

def evaluate_moves(moves, my_pts, opp_pts, my_bar, my_off):
    best_score = float('-inf')
    best_move = "H:P,P"
    
    for move in moves:
        score = evaluate_move(move, my_pts, opp_pts, my_bar, my_off)
        if score > best_score:
            best_score = score
            best_move = format_move(move)
    
    return best_move

def evaluate_move(move, my_pts, opp_pts, my_bar, my_off):
    score = 0
    
    if len(move) == 3:  # Single move
        die, from_pos, _ = move
        if from_pos == 'B':
            # Re-entering from bar is good
            score += 10
            target = 24 - die
            if target >= 0:
                # Check if we hit an opponent blot
                if opp_pts[target] == 1:
                    score += 20
                # Check if we make a point
                if my_pts[target] == 1:
                    score += 15
        else:
            from_pos = int(from_pos)
            target = from_pos - die
            # Progress towards bearing off
            score += (23 - from_pos) * 0.5
            if target >= 0:
                # Check if we hit an opponent blot
                if opp_pts[target] == 1:
                    score += 20
                # Check if we make a point
                if my_pts[target] == 1:
                    score += 15
                # Check if we're moving to a safe point
                if opp_pts[target] == 0:
                    score += 5
            else:
                # Bearing off
                score += 25
    
    elif len(move) == 4:  # Double move
        die1, from_pos1, die2, from_pos2 = move
        # Evaluate both moves
        temp_score = 0
        
        # First move
        if from_pos1 == 'B':
            temp_score += 10
            target = 24 - die1
            if target >= 0:
                if opp_pts[target] == 1:
                    temp_score += 20
                if my_pts[target] == 1:
                    temp_score += 15
        else:
            from_pos1 = int(from_pos1)
            target = from_pos1 - die1
            temp_score += (23 - from_pos1) * 0.5
            if target >= 0:
                if opp_pts[target] == 1:
                    temp_score += 20
                if my_pts[target] == 1:
                    temp_score += 15
                if opp_pts[target] == 0:
                    temp_score += 5
            else:
                temp_score += 25
        
        # Second move
        if from_pos2 == 'B':
            temp_score += 10
            target = 24 - die2
            if target >= 0:
                if opp_pts[target] == 1:
                    temp_score += 20
                if my_pts[target] == 1:
                    temp_score += 15
        else:
            from_pos2 = int(from_pos2)
            target = from_pos2 - die2
            temp_score += (23 - from_pos2) * 0.5
            if target >= 0:
                if opp_pts[target] == 1:
                    temp_score += 20
                if my_pts[target] == 1:
                    temp_score += 15
                if opp_pts[target] == 0:
                    temp_score += 5
            else:
                temp_score += 25
        
        score = temp_score
    
    return score

def format_move(move):
    if len(move) == 3:
        die, from_pos, _ = move
        if isinstance(from_pos, str):
            return f"H:{from_pos},P" if die == max_dice(move) else f"L:{from_pos},P"
        else:
            from_str = f"A{from_pos}"
            return f"H:{from_str},P" if die == max_dice(move) else f"L:{from_str},P"
    else:
        die1, from_pos1, die2, from_pos2 = move
        # Determine which die is higher
        if die1 > die2:
            order = 'H'
            f1 = from_pos1 if isinstance(from_pos1, str) else f"A{from_pos1}"
            f2 = from_pos2 if isinstance(from_pos2, str) else f"A{from_pos2}"
        else:
            order = 'L'
            f1 = from_pos1 if isinstance(from_pos1, str) else f"A{from_pos1}"
            f2 = from_pos2 if isinstance(from_pos2, str) else f"A{from_pos2}"
        return f"{order}:{f1},{f2}"

def max_dice(move):
    if len(move) == 3:
        return move[0]
    else:
        return max(move[0], move[2])
