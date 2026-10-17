
import copy

# Weights for the heuristic evaluation function
W_OFF = 100.0       # Weight for bearing off a checker
W_PIP = -1.0        # Weight for pip count (negative because lower is better)
W_HIT = 50.0        # Weight for hitting an opponent blot
W_BAR = -80.0       # Weight for having a checker on the bar
W_BLOT = -20.0      # Weight for having a blot (single checker)
W_BLOCK = 5.0       # Weight for making a point (2+ checkers)
W_THREAT = -15.0    # Weight for the danger of a blot being hit

def policy(state: dict) -> str:
    dice = state['dice']
    
    # If no dice, must pass
    if not dice:
        return "H:P,P"

    # Helper function to simulate a move sequence and evaluate it
    def evaluate_sequence(order, start1, start2, d1, d2):
        # start1, start2 are strings like "A5", "B", or "P"
        # d1 is the die value for start1, d2 for start2
        
        # Apply first move
        if start1 != "P":
            temp_state = copy.deepcopy(state)
            if not apply_move(temp_state, start1, d1):
                return None  # Should not happen if generated correctly
        else:
            temp_state = copy.deepcopy(state)
        
        # Apply second move
        if start2 != "P":
            if not apply_move(temp_state, start2, d2):
                return None
        
        # Calculate score of the resulting state
        return evaluate_board(temp_state, state['opp_bar'])

    # Generate candidates for a specific order (H or L)
    def get_candidates(order, high, low):
        d1 = high if order == 'H' else low
        d2 = low if order == 'H' else high
        
        candidates = []
        
        # Get all legal starts for the first die
        legal_starts_1 = get_legal_moves(state, d1)
        
        for s1 in legal_starts_1:
            # If we can make the first move (or pass it, though we filter passes later)
            temp_after_m1 = copy.deepcopy(state)
            if s1 != "P":
                if not apply_move(temp_after_m1, s1, d1):
                    continue
            
            # Get all legal starts for the second die from the updated state
            legal_starts_2 = get_legal_moves(temp_after_m1, d2)
            
            if not legal_starts_2:
                # No second move possible, candidate is (s1, P)
                if s1 != "P":
                    score = evaluate_sequence(order, s1, "P", d1, d2)
                    if score is not None:
                        candidates.append((score, f"{order}:{s1},P"))
            else:
                for s2 in legal_starts_2:
                    score = evaluate_sequence(order, s1, s2, d1, d2)
                    if score is not None:
                        candidates.append((score, f"{order}:{s1},{s2}"))
        return candidates

    # Handle single die
    if len(dice) == 1:
        d = dice[0]
        moves = get_legal_moves(state, d)
        if not moves:
            return "H:P,P"
        
        best_move = "H:P,P"
        best_score = -float('inf')
        for m in moves:
            score = evaluate_sequence('H', m, "P", d, 0) # 0 for unused die
            if score is not None and score > best_score:
                best_score = score
                best_move = f"H:{m},P"
        return best_move

    # Handle two dice
    if len(dice) == 2:
        high = max(dice)
        low = min(dice)
        
        # Check availability of dice independently
        can_play_high = bool(get_legal_moves(state, high))
        can_play_low = bool(get_legal_moves(state, low))
        
        all_candidates = []
        
        # Evaluate Order H (High then Low)
        # We can only choose Order H if we can play the high die (or pass it, but passing is only for no moves)
        # If we can play high, we explore using it.
        if can_play_high:
            h_candidates = get_candidates('H', high, low)
            # These candidates always use High (s1 is valid).
            # They are (High, Low) or (High, P). All are valid candidates.
            all_candidates.extend(h_candidates)
            
        # Evaluate Order L (Low then High)
        # We can play Low then High, or Low then Pass
        if can_play_low:
            l_candidates = get_candidates('L', high, low)
            for score, move_str in l_candidates:
                parts = move_str.split(',')
                s2 = parts[1]
                
                # If move is (Low, P), we are playing only the Low die.
                # This is only legal if we could NOT play the High die.
                if s2 == "P":
                    if not can_play_high:
                        all_candidates.append((score, move_str))
                else:
                    # (Low, High) uses both dice. Always valid if generated.
                    all_candidates.append((score, move_str))

        if not all_candidates:
            return "H:P,P"
        
        # Select the best move
        best_score = -float('inf')
        best_move = "H:P,P"
        for score, move in all_candidates:
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move

    return "H:P,P"

def get_legal_moves(state, die):
    """Returns a list of start points ('A0'..'A23', 'B') legal for the given die."""
    moves = []
    
    # 1. Bar Rule: Must move from bar if checkers exist
    if state['my_bar'] > 0:
        entry_point = 24 - die
        if state['opp_pts'][entry_point] < 2:
            moves.append("B")
        return moves
    
    # 2. Normal moves
    # Check if we can bear off
    all_in_home = all(c == 0 for c in state['my_pts'][6:])
    
    # Iterate from high points to low points (23 down to 0)
    # Moving from 23 -> 0, so we prefer moving pieces further back?
    # Standard search order doesn't matter for correctness, but good for consistency.
    for i in range(23, -1, -1):
        if state['my_pts'][i] > 0:
            dest = i - die
            
            if dest >= 0:
                # Standard move
                if state['opp_pts'][dest] < 2:
                    moves.append(f"A{i}")
            else:
                # Bearing off
                if all_in_home:
                    if dest == -1:
                        # Exact bear off
                        moves.append(f"A{i}")
                    else:
                        # Overshoot bear off (dest < -1)
                        # Only allowed if no checkers on higher points in home board
                        # Higher points are indices i+1 to 5
                        has_higher = any(c > 0 for c in state['my_pts'][i+1:6])
                        if not has_higher:
                            moves.append(f"A{i}")
    return moves

def apply_move(state, start, die):
    """Applies a move to the state dict. Returns True if successful."""
    if start == "P":
        return True
        
    # Remove from start
    if start == "B":
        if state['my_bar'] == 0: return False
        state['my_bar'] -= 1
        dest = 24 - die
    else:
        idx = int(start[1:])
        if state['my_pts'][idx] == 0: return False
        state['my_pts'][idx] -= 1
        dest = idx - die
        
    # Handle destination
    if dest < 0:
        # Bear off
        state['my_off'] += 1
    else:
        # Land on board
        if state['opp_pts'][dest] == 1:
            # Hit!
            state['opp_pts'][dest] = 0
            state['opp_bar'] += 1
        elif state['opp_pts'][dest] >= 2:
            # Blocked
            return False
        state['my_pts'][dest] += 1
        
    return True

def evaluate_board(state, initial_opp_bar):
    """Heuristic evaluation of the board state."""
    score = 0.0
    
    # 1. Checkers borne off
    score += state['my_off'] * W_OFF
    
    # 2. Pip count (Lower is better)
    pips = sum(i * c for i, c in enumerate(state['my_pts']))
    score += pips * W_PIP
    
    # 3. Bar penalty
    score -= state['my_bar'] * W_BAR
    
    # 4. Hits reward
    hits = state['opp_bar'] - initial_opp_bar
    score += hits * W_HIT
    
    # 5. Blots and Blocks
    blots = []
    for i in range(24):
        count = state['my_pts'][i]
        if count == 1:
            blots.append(i)
            score += W_BLOT
        elif count >= 2:
            score += W_BLOCK
            
    # 6. Blot Safety (Threats)
    # Opponent moves 0 -> 23. Hits my blot at 't' if opp has checker at 't-die'.
    for blot_idx in blots:
        # Opponent can hit if they are within range 1..6
        # Opponent start positions that can hit blot_idx: [blot_idx - 6, blot_idx - 1]
        min_start = max(0, blot_idx - 6)
        max_start = min(23, blot_idx - 1)
        
        if min_start <= max_start:
            threats = sum(state['opp_pts'][min_start : max_start + 1])
            score += threats * W_THREAT
            
    return score
