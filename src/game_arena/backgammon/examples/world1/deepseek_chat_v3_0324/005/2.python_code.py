
import numpy as np

def policy(state: dict) -> str:
    # Extract game state
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)
    
    if not dice:
        return "H:P,P"
    
    # Generate all possible legal moves
    possible_moves = generate_legal_moves(state)
    
    if not possible_moves:
        return "H:P,P"
    
    # Score each possible move and select the best one
    best_move = None
    best_score = -float('inf')
    
    for move in possible_moves:
        score = evaluate_move(move, state)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def generate_legal_moves(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = sorted(state['dice'], reverse=True)
    moves = []
    
    # Handle bar re-entry first if needed
    if my_bar > 0:
        return generate_bar_moves(state)
    
    # Generate all possible non-bar moves
    if len(dice) == 1:
        # Single die moves
        die = dice[0]
        for src in range(24):
            if my_pts[src] > 0:
                dest = src - die
                if is_valid_move(src, dest, my_pts, opp_pts, state):
                    moves.append(f"H:A{src},P")
        if not moves:
            moves.append("H:P,P")
    else:
        # Two dice moves - try both orders
        die1, die2 = dice[0], dice[1]
        
        # Try high die first
        valid_h = False
        for src1 in range(24):
            if my_pts[src1] > 0:
                dest1 = src1 - die1
                if is_valid_move(src1, dest1, my_pts, opp_pts, state):
                    temp_my_pts = my_pts.copy()
                    temp_opp_pts = opp_pts.copy()
                    temp_my_pts[src1] -= 1
                    if dest1 >= 0:
                        temp_my_pts[dest1] += 1
                    
                    for src2 in range(24):
                        if temp_my_pts[src2] > 0:
                            dest2 = src2 - die2
                            if is_valid_move(src2, dest2, temp_my_pts, temp_opp_pts, state):
                                moves.append(f"H:A{src1},A{src2}")
                                valid_h = True
                    if not valid_h:
                        moves.append(f"H:A{src1},P")
        
        # Try low die first if high die first didn't find valid moves
        if not valid_h:
            for src1 in range(24):
                if my_pts[src1] > 0:
                    dest1 = src1 - die2
                    if is_valid_move(src1, dest1, my_pts, opp_pts, state):
                        temp_my_pts = my_pts.copy()
                        temp_opp_pts = opp_pts.copy()
                        temp_my_pts[src1] -= 1
                        if dest1 >= 0:
                            temp_my_pts[dest1] += 1
                        
                        for src2 in range(24):
                            if temp_my_pts[src2] > 0:
                                dest2 = src2 - die1
                                if is_valid_move(src2, dest2, temp_my_pts, temp_opp_pts, state):
                                    moves.append(f"L:A{src1},A{src2}")
        
        if not moves:
            moves.append("H:P,P")
    
    return moves

def generate_bar_moves(state):
    my_bar = state['my_bar']
    opp_pts = state['opp_pts']
    dice = sorted(state['dice'], reverse=True)
    moves = []
    
    if len(dice) == 1:
        die = dice[0]
        dest = 24 - die
        if opp_pts[dest] <= 1:
            moves.append(f"H:B,P")
        else:
            moves.append("H:P,P")
    else:
        die1, die2 = dice[0], dice[1]
        valid_die1 = False
        dest1 = 24 - die1
        if opp_pts[dest1] <= 1:
            temp_opp_pts = opp_pts.copy()
            temp_opp_pts[dest1] = max(0, temp_opp_pts[dest1] - 1)
            dest2 = 24 - die2
            if opp_pts[dest2] <= 1:
                moves.append(f"H:B,B")
            else:
                moves.append(f"H:B,P")
            valid_die1 = True
        
        if not valid_die1:
            dest1 = 24 - die2
            if opp_pts[dest1] <= 1:
                dest2 = 24 - die1
                if opp_pts[dest2] <= 1:
                    moves.append(f"L:B,B")
                else:
                    moves.append(f"L:B,P")
            else:
                moves.append("H:P,P")
    
    return moves

def is_valid_move(src, dest, my_pts, opp_pts, state):
    # Check if bearing off is allowed
    if dest < 0:
        # Check if all checkers are in home board (0-5)
        home_board = range(6)
        for i in range(6, 24):
            if my_pts[i] > 0:
                return False
        return True
    
    # Check if destination is blocked
    if dest >= 0 and opp_pts[dest] >= 2:
        return False
    
    return True

def evaluate_move(move, state):
    my_pts = state['my_pts'].copy()
    opp_pts = state['opp_pts'].copy()
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    score = 0
    
    # Parse the move
    order, moves_str = move.split(':')
    moves = moves_str.split(',')
    
    # Apply the move to a temporary board state
    for i, m in enumerate(moves):
        if m == 'P':
            continue
            
        die = dice[0 if (i == 0 and order == 'H') or (i == 1 and order == 'L') else 1]
        
        if m == 'B':
            src = -1  # bar
        else:
            src = int(m[1:])
        
        dest = src - die if src != -1 else (24 - die)
        
        if src == -1:  # bar move
            my_bar -= 1
        else:
            my_pts[src] -= 1
        
        if dest < 0:  # bearing off
            my_off += 1
        else:
            if opp_pts[dest] == 1:  # hit opponent
                opp_pts[dest] = 0
                opp_bar += 1
            my_pts[dest] += 1
    
    # Evaluate the resulting position
    
    # 1. Score for bearing off checkers
    score += my_off * 10
    
    # 2. Penalty for having checkers on the bar
    score -= my_bar * 15
    
    # 3. Score for hitting opponent
    score += opp_bar * 8
    
    # 4. Score for building points (2+ checkers)
    for i in range(24):
        if my_pts[i] >= 2:
            score += 2
            if i >= 18:  # opponent's home board
                score += 3
    
    # 5. Penalty for leaving blots (single checkers)
    for i in range(24):
        if my_pts[i] == 1 and opp_pts[i] > 0:
            score -= 5
    
    # 6. Score for having checkers in good positions
    for i in range(24):
        if my_pts[i] > 0:
            # Higher score for being closer to bearing off
            score += (23 - i) * 0.5
    
    # 7. Bonus for having all checkers in home board when close to bearing off
    all_in_home = True
    for i in range(6, 24):
        if my_pts[i] > 0:
            all_in_home = False
            break
    if all_in_home:
        score += 20
    
    return score
