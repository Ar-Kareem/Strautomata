
import numpy as np

def policy(state):
    # Extract game state
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)
    
    # Generate all legal moves
    legal_moves = generate_legal_moves(my_pts, opp_pts, my_bar, dice)
    
    if not legal_moves:
        return "H:P,P"
    
    # Score each legal move
    scored_moves = []
    for move in legal_moves:
        score = evaluate_move(move, my_pts, opp_pts, my_bar, opp_bar, dice)
        scored_moves.append((score, move))
    
    # Select the best move
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    best_move = scored_moves[0][1]
    
    return format_move(best_move, dice)

def generate_legal_moves(my_pts, opp_pts, my_bar, dice):
    moves = []
    
    # Handle bar re-entry first if needed
    if my_bar > 0:
        return generate_bar_moves(my_pts, opp_pts, my_bar, dice)
    
    # Generate all possible moves when not on bar
    if len(dice) == 2:
        # Generate moves using both dice
        moves.extend(generate_two_dice_moves(my_pts, opp_pts, dice))
        
        # Generate moves using one die (when both can't be used)
        if not moves:
            moves.extend(generate_single_die_moves(my_pts, opp_pts, dice[0]))
            moves.extend(generate_single_die_moves(my_pts, opp_pts, dice[1]))
    elif len(dice) == 1:
        moves.extend(generate_single_die_moves(my_pts, opp_pts, dice[0]))
    
    # Add pass move if no other moves available
    if not moves:
        moves.append([('P', None), ('P', None)])
    
    return moves

def generate_bar_moves(my_pts, opp_pts, my_bar, dice):
    moves = []
    used_dice = set()
    
    for die in sorted(dice, reverse=True):
        if die in used_dice:
            continue
            
        entry_point = 24 - die
        if opp_pts[entry_point] <= 1:  # Can enter here
            if len(dice) == 2 and die != dice[1]:
                # Try to use both dice
                other_die = dice[0] if die == dice[1] else dice[1]
                other_entry_point = 24 - other_die
                if opp_pts[other_entry_point] <= 1:
                    moves.append([('B', die), ('B', other_die)])
                    used_dice.add(die)
                    used_dice.add(other_die)
            else:
                moves.append([('B', die), ('P', None)])
                used_dice.add(die)
    
    # If no moves found with both dice, try single die
    if not moves:
        for die in sorted(dice, reverse=True):
            entry_point = 24 - die
            if opp_pts[entry_point] <= 1:
                moves.append([('B', die), ('P', None)])
                break
    
    return moves if moves else [[('P', None), ('P', None)]]

def generate_two_dice_moves(my_pts, opp_pts, dice):
    moves = []
    die1, die2 = dice
    
    # Try all possible combinations of using both dice
    for src1 in range(24):
        if my_pts[src1] == 0:
            continue
        dest1 = src1 - die1
        if dest1 < 0:  # Bearing off
            if can_bear_off(my_pts):
                pass  # Will handle in bearing off logic
            else:
                continue
        else:
            if opp_pts[dest1] > 1:
                continue
        
        for src2 in range(24):
            if src2 == src1 and my_pts[src2] < 2:
                continue
            if my_pts[src2] == 0:
                continue
            dest2 = src2 - die2
            if dest2 < 0:  # Bearing off
                if can_bear_off(my_pts):
                    pass  # Will handle in bearing off logic
                else:
                    continue
            else:
                if opp_pts[dest2] > 1:
                    continue
            
            moves.append([(f"A{src1}", die1), (f"A{src2}", die2)])
    
    # Handle bearing off cases
    if can_bear_off(my_pts):
        moves.extend(generate_bear_off_moves(my_pts, dice))
    
    return moves

def generate_single_die_moves(my_pts, opp_pts, die):
    moves = []
    
    for src in range(24):
        if my_pts[src] == 0:
            continue
        dest = src - die
        if dest < 0:  # Bearing off
            if can_bear_off(my_pts):
                moves.append([(f"A{src}", die), ('P', None)])
        else:
            if opp_pts[dest] <= 1:
                moves.append([(f"A{src}", die), ('P', None)])
    
    return moves if moves else [[('P', None), ('P', None)]]

def generate_bear_off_moves(my_pts, dice):
    moves = []
    die1, die2 = dice
    
    # Try bearing off with both dice
    for src1 in range(24):
        if my_pts[src1] == 0:
            continue
        if src1 + 1 >= die1:  # Can bear off
            for src2 in range(24):
                if src2 == src1 and my_pts[src2] < 2:
                    continue
                if my_pts[src2] == 0:
                    continue
                if src2 + 1 >= die2:  # Can bear off
                    moves.append([(f"A{src1}", die1), (f"A{src2}", die2)])
    
    # If no moves with both dice, try single die
    if not moves:
        for src in range(24):
            if my_pts[src] == 0:
                continue
            if src + 1 >= die1:
                moves.append([(f"A{src}", die1), ('P', None)])
            if src + 1 >= die2:
                moves.append([(f"A{src}", die2), ('P', None)])
    
    return moves if moves else [[('P', None), ('P', None)]]

def can_bear_off(my_pts):
    # Check if all checkers are in home board (points 0-5)
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True

def evaluate_move(move, my_pts, opp_pts, my_bar, opp_bar, dice):
    score = 0
    temp_my_pts = my_pts.copy()
    temp_opp_pts = opp_pts.copy()
    
    # Apply the move to temporary board state
    for action in move:
        src, die = action
        if src == 'P' or die is None:
            continue
        
        if src == 'B':
            # Bar re-entry
            dest = 24 - die
            if opp_pts[dest] == 1:  # Hit opponent
                score += 15
            else:
                # Prefer entering deeper
                score += (24 - dest) * 0.5
        else:
            # Normal move
            src_idx = int(src[1:])
            dest = src_idx - die
            
            if dest < 0:  # Bearing off
                score += 10
                # Prefer bearing off from higher points first
                score += (src_idx + 1) * 0.2
            else:
                # Check if we're hitting an opponent
                if opp_pts[dest] == 1:
                    score += 12
                
                # Check if we're making a new point
                if temp_my_pts[dest] == 0:
                    score += 8
                
                # Check if we're extending an existing point
                if temp_my_pts[dest] > 0:
                    score += 4
                
                # Prefer moving from higher points to lower points
                score += (src_idx - dest) * 0.3
                
                # Prefer moving back checkers that are advanced
                if src_idx > 12:
                    score += (src_idx - 12) * 0.4
    
    # Additional strategic considerations
    # Prefer moves that leave fewer blots
    blot_penalty = count_blots(temp_my_pts, temp_opp_pts) * -5
    score += blot_penalty
    
    # Prefer moves that create primes (2+ consecutive points)
    prime_bonus = count_primes(temp_my_pts) * 3
    score += prime_bonus
    
    return score

def count_blots(my_pts, opp_pts):
    blots = 0
    for i in range(24):
        if my_pts[i] == 1 and opp_pts[23 - i] > 0:
            blots += 1
    return blots

def count_primes(my_pts):
    primes = 0
    consecutive = 0
    for i in range(24):
        if my_pts[i] >= 2:
            consecutive += 1
            if consecutive >= 2:
                primes += 1
        else:
            consecutive = 0
    return primes

def format_move(move, dice):
    die1, die2 = sorted(dice, reverse=True)
    order = 'H'
    from1, from2 = 'P', 'P'
    
    if move[0][0] != 'P':
        # Determine order based on which die was used first
        if move[0][1] == die1:
            order = 'H'
        else:
            order = 'L'
        
        from1 = move[0][0]
        if move[1][0] != 'P':
            from2 = move[1][0]
    
    return f"{order}:{from1},{from2}"
