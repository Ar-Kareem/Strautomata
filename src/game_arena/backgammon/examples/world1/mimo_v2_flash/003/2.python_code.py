
import itertools

def policy(state: dict) -> str:
    """
    Backgammon AI Policy.
    Heuristics:
    1. Enter from bar if possible.
    2. Build primes (especially in the outer board).
    3. Run checkers from the back if the board is weak or lagging.
    4. Consolidate home board for bear-off.
    5. Safety (minimize blots).
    """
    
    # Extract State
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    dice = sorted(state['dice']) # [low, high]
    
    # --- 1. Generate All Legal Moves ---
    # Note: We rely on the engine to enforce standard rules (must enter, must play higher die if only one works).
    # We generate a superset of possibilities and score them.
    
    moves = generate_moves(my_pts, opp_pts, my_bar, dice)
    
    if not moves:
        # No legal moves (or forced pass)
        return "H:P,P"
    
    # --- 2. Scoring Function ---
    # We score each move sequence based on board state.
    # High score is better.
    
    best_score = -float('inf')
    best_move_str = None
    
    for (die_order, m1_src, m2_src) in moves:
        # Calculate score for this move
        score = 0
        
        # Create a temporary board state to evaluate outcome
        # (Simulate the moves to count resulting positions)
        temp_my = my_pts[:]
        temp_opp = opp_pts[:]
        temp_bar = my_bar
        
        # Helper to apply a move
        def apply_move(src, die):
            nonlocal temp_my, temp_opp, temp_bar
            dest = -1
            
            if src == 'B':
                # Bar entry
                temp_bar -= 1
                # Determine destination based on die
                # Opponent moves 0 -> 23, we move 23 -> 0
                # If we are at Bar, we enter at 23 - die + 1? 
                # Wait, engine handles indices. 
                # State indices: 0 (our home) to 23 (opponent home).
                # We move 23 -> 0.
                # If we are at Bar, we enter at 23 - die + 1? 
                # Standard: Die 1 enters at 24 (Index 23). Die 2 enters at 23 (Index 22).
                # Actually, in this representation:
                # We start at 23. Moving 6 lands on 18. Moving 1 lands on 22.
                # Destination = Source - Die
                dest = 23 - die
                temp_my[dest] += 1
            elif isinstance(src, int):
                src_idx = src
                dest = src_idx - die
                temp_my[src_idx] -= 1
                if dest < 0:
                    # Bearing off
                    pass # Just remove from board
                else:
                    temp_my[dest] += 1
            
            return dest

        # Apply M1
        d1 = dice[1] if die_order == 'H' else dice[0]
        dest1 = apply_move(m1_src, d1)
        
        # Apply M2 (if exists)
        if m2_src != 'P':
            d2 = dice[0] if die_order == 'H' else dice[1]
            apply_move(m2_src, d2)
        
        # --- Heuristic Evaluation ---
        
        # 1. Safety (Check for blots on temp board)
        # Penalize leaving blots (single checkers) exposed.
        blots = 0
        for i in range(24):
            if temp_my[i] == 1:
                # Check if attacked
                # Opponent attacks from i-6 to i-1 (moving 0->23)
                # Opponent sources are (dest + die)
                # If opp has a checker at j, they can hit i with die = i - j
                exposed = False
                for die_val in range(1, 7):
                    attacker_src = i + die_val
                    if attacker_src < 24 and temp_opp[attacker_src] > 0:
                        exposed = True
                        break
                if exposed:
                    blots += 1
        score -= blots * 10  # Heavy penalty for safety risks

        # 2. Priming (Pips in home board / outer board)
        # Count consecutive points occupied in home board (0-5)
        home_chain = 0
        for i in range(6):
            if temp_my[i] > 0:
                home_chain += 1
            else:
                break
        score += home_chain * 5
        
        # 3. Back Game / Running Checkers
        # We want checkers in the home board (0-5) for bearing off.
        # But also need to keep a "back" checker if running game is lost.
        # Checkers in 18-23 (our backfield) are slow.
        back_checkers = sum(temp_my[18:])
        score += 50 # Base for any checker safely home
        score -= back_checkers * 2 # Penalty for checkers in backfield (encourage advancement)

        # 4. Entering from Bar (Highest Priority)
        # If we started with bar checkers and managed to enter, boost score massively
        if my_bar > 0 and temp_bar < my_bar:
            score += 1000
            
        # 5. Hitting Opponent
        # Did we land on an opponent blot?
        # We need to check the destination against original opp_pts
        # But `apply_move` updates temp_opp? No, it only updates temp_my.
        # Check if dest1 (or dest2) was an opponent blot.
        if dest1 is not None and dest1 >= 0 and opp_pts[dest1] == 1:
            score += 25 # Hit bonus
        if m2_src != 'P':
            # Need to recalculate dest for m2 based on temp state or just check original?
            # Checking original is safer for immediate hit bonus
            d2 = dice[0] if die_order == 'H' else dice[1]
            # Determine dest2
            if m2_src == 'B':
                dest2 = 23 - d2
            else:
                dest2 = m2_src - d2
            if dest2 is not None and dest2 >= 0 and opp_pts[dest2] == 1:
                score += 25

        # 6. Consolidation
        # Avoid stacking too many on one point unless blocking
        for i in range(24):
            if temp_my[i] > 3:
                score -= 2 # Diminishing returns on stacks
        
        # Update best
        if score > best_score:
            best_score = score
            best_move_str = f"{die_order}:{m1_src},{m2_src if m2_src != 'P' else 'P'}"
    
    return best_move_str if best_move_str else "H:P,P"


def generate_moves(my_pts, opp_pts, my_bar, dice):
    """
    Generates all legal move sequences.
    Returns list of (die_order, m1_src, m2_src).
    die_order: 'H' (High first) or 'L' (Low first).
    src: 'B' (Bar), int (Point index), or 'P' (Pass).
    """
    moves = []
    
    # If doubles, only one order matters (H or L produces same result), 
    # but we can just stick to H convention or generate both.
    # If not doubles, we have two orders: (d0, d1) and (d1, d0).
    
    d1, d2 = dice[0], dice[1]
    is_double = (d1 == d2)
    
    orders = [('H', d2, d1)] if d2 >= d1 else [('L', d1, d2)] 
    # Convention: 'H' means first move uses higher die.
    # If dice are [2, 5], H order is move 5 then 2. L order is move 2 then 5.
    
    if not is_double:
        # For non-doubles, we must try both orders if both result in legal moves.
        # But engine constraints say: "If only one die can be played, you must play the higher die."
        # This implies we should try High first, then Low.
        # We will generate both orders and let the engine/restrictions handle it.
        # Actually, to be safe, we generate all valid sequences.
        orders = [('H', d2, d1), ('L', d1, d2)]
    
    # Remove duplicates if double
    orders = list(set(orders))

    for order_name, die_first, die_second in orders:
        # Find all moves for the first die
        first_legals = get_legals_for_die(my_pts, opp_pts, my_bar, die_first)
        
        for src1 in first_legals:
            # Simulate first move
            sim_my, sim_opp, sim_bar = simulate_board(my_pts, opp_pts, my_bar, src1, die_first)
            
            # Find legals for second die on simulated board
            second_legals = get_legals_for_die(sim_my, sim_opp, sim_bar, die_second)
            
            # If no legals for second die, we can still return a 1-move sequence if valid
            if not second_legals:
                # Check if we were forced to play both? 
                # Rule: "If both dice can be played, you must play both."
                # We check if the first move left us unable to play the second.
                # If we can play the second, we MUST.
                # So we only add (src1, 'P') if we literally cannot play die_second.
                moves.append((order_name, src1, 'P'))
            else:
                for src2 in second_legals:
                    moves.append((order_name, src1, src2))

    # Filter: If we have a move that uses both dice, we should prefer it over one that uses one.
    # The engine might enforce this, but let's be helpful.
    two_die_moves = [m for m in moves if m[2] != 'P']
    if two_die_moves:
        return two_die_moves
    
    return moves

def get_legals_for_die(my_pts, opp_pts, my_bar, die):
    """
    Returns list of source points (int or 'B') valid for a specific die roll.
    """
    legals = []
    
    # 1. Bar Entry
    if my_bar > 0:
        # Destination is 23 - die + 1? No, 23 - die.
        # 23 (Index) is furthest back. 
        # Die 1 -> Dest 22. Die 2 -> Dest 21.
        dest = 23 - die
        if 0 <= dest < 24:
            if opp_pts[dest] < 2:
                legals.append('B')
        # If dest is bearing off (negative), cannot enter from bar with high die usually.
        # Backgammon rules: Can only bear off if all checkers are in home board.
        # Bar is not home board. So dest must be >= 0.
        return legals # If on bar, must move from bar.
    
    # 2. Regular Moves
    for i in range(24):
        if my_pts[i] > 0:
            dest = i - die
            
            if dest < 0:
                # Bearing off
                # Check if all checkers are in home board (0-5)
                # We check the current board state (pre-move)
                if is_all_home(my_pts):
                    legals.append(i)
            else:
                # Regular move
                if opp_pts[dest] < 2:
                    legals.append(i)
                    
    return legals

def is_all_home(my_pts):
    # Check points 6 to 23 (backgammon points) are empty
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True

def simulate_board(my_pts, opp_pts, my_bar, src, die):
    """
    Returns new my_pts, opp_pts, my_bar after a move.
    Does not handle hits (engine does), only moves our checkers.
    """
    new_my = my_pts[:]
    new_opp = opp_pts[:]
    new_bar = my_bar
    
    if src == 'B':
        new_bar -= 1
        dest = 23 - die
        if dest >= 0:
            new_my[dest] += 1
    else:
        new_my[src] -= 1
        dest = src - die
        if dest >= 0:
            new_my[dest] += 1
        # If dest < 0, checker is borne off (removed)
            
    return new_my, new_opp, new_bar
