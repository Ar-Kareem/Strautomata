
def policy(state: dict) -> str:
    """
    Backgammon Policy: Evaluates legal moves using a heuristic evaluation function
    to maximize board safety and progress towards bearing off.
    """
    
    # --- Helper Functions ---

    def is_home_point(p, is_white):
        """Returns True if point p is in the player's home board."""
        # The engine handles the mapping, so we rely on the standard definition:
        # White (0) home is 18-23, Black (1) home is 0-5.
        # Since we don't explicitly know our color (0 or 1) from the state dict,
        # we infer it from the board's occupation context or assume standard indexing.
        # However, the state is always relative to 'my_pts'. 
        # In standard OpenSpiel Backgammon, if we are Player 0, we move 0->23. 
        # If we are Player 1, we move 23->0.
        # Usually, the API `my_pts` implies the points are indexed 0..23 relative to our view.
        # But standard backgammon indices are absolute. 
        # Let's assume standard absolute indices: 0-23 on one side, 0-23 on the other.
        # To be safe, we check the boundaries. 
        # If we are moving 0->23 (White), home is 18-23.
        # If we are moving 23->0 (Black), home is 0-5.
        # We can infer direction by looking at standard play or assuming we are always Player 0?
        # Actually, the state doesn't say "my_color". But standard `my_pts` usually implies 
        # the array index 0 is our furthest point.
        # Let's use a trick: check if we have checkers at 0 or 23.
        # If we have checkers at 0 and not 23, we are likely Black (moving 23->0).
        # If we have checkers at 23 and not 0, we are likely White (moving 0->23).
        # However, this might fail if both have checkers.
        # Let's rely on the fact that `state` is given. 
        # `my_pts` is a list of 24 ints.
        # Let's assume the standard "White is 0" convention usually used in libraries, 
        # where White moves 0->23.
        # Let's check `my_off`. If we are bearing off, we are at the end.
        # Let's simply check boundaries: 0-5 is one end, 18-23 is the other.
        # We need to know which end is "our" end.
        # Given `my_pts`, if we have checkers in 0-5, is that our home?
        # Let's look at `my_bar` checkers. If they exist, they must enter at 0 or 23?
        # If we are White (0->23), we enter at 0 (if hit).
        # If we are Black (23->0), we enter at 23.
        # Let's determine direction based on where we are likely to bear off from.
        # Actually, let's just check the two standard ranges.
        # If we are bearing off, all checkers are in 18-23 (White) or 0-5 (Black).
        # Let's write a generic check.
        # If we have checkers at 23, we are likely White (start 0).
        # If we have checkers at 0, we are likely Black (start 23).
        # But both might be empty.
        # Let's use the heuristic: assume we are "Player 0" (White) unless `my_pts[0]` has checkers and `my_pts[23]` doesn't.
        # Actually, simpler: Let's look at the `dice` logic.
        # In the engine, White moves +, Black moves -.
        # If we are White, home is 18-23.
        # If we are Black, home is 0-5.
        # Let's infer color:
        # If sum(my_pts[0:6]) > sum(my_pts[18:23]), we are likely Black (stuck at start).
        # If sum(my_pts[18:23]) > sum(my_pts[0:6]), we are likely White.
        # Let's just check `my_pts[23]`. If it's > 0, we are likely White.
        # Let's check `my_pts[0]`. If it's > 0, we are likely Black.
        # Let's assume the `state` is given such that we are always Player 0 (White) in this specific API context, 
        # but let's code defensively.
        
        # Let's assume standard White rules (0->23, home 18-23) for simplicity 
        # unless we see checkers occupying 0..5 with no checkers 18..23 (unlikely start).
        # Actually, let's just check `my_off`. If we are bearing off, we are in home.
        # Let's define home based on index.
        # If `my_pts[23]` > 0 (or `my_bar` > 0 and we can enter at 23?), 
        # wait, bar entry is always 0 or 23?
        # White enters 0, Black enters 23.
        # If we have bar checkers, we must enter at 0 or 23.
        # If we are White, we enter 0. If Black, 23.
        # Let's check `my_bar` and `opp_bar` logic.
        # Actually, the prompt says `state` is absolute indices.
        # Let's define "my home" as 18-23 if we have checkers there, else 0-5.
        # Let's count checkers.
        c_in_0_5 = sum(state['my_pts'][0:6])
        c_in_18_23 = sum(state['my_pts'][18:24])
        
        # If we have more in 18-23, we are likely White.
        # If we have more in 0-5, we are likely Black.
        # If equal, default to White (0->23).
        is_white = c_in_18_23 >= c_in_0_5
        
        if is_white:
            return 18 <= p <= 23
        else:
            return 0 <= p <= 5

    def evaluate_board(p_pts, p_bar, p_off, o_pts, o_bar, o_off):
        """
        Heuristic evaluation of the board state.
        Higher score is better for the current player (p).
        """
        score = 0
        
        # 1. Progress: Checkers in home board / borne off
        # Home board points
        my_home_pts = 0
        opp_home_pts = 0
        for i in range(24):
            if is_home_point(i, True): # We assume True is our perspective
                my_home_pts += p_pts[i]
                opp_home_pts += o_pts[i]
        
        # Weight borne off heavily
        score += p_off * 20 
        # Weight home board
        score += my_home_pts * 5
        
        # 2. Safety: Penalize blots (single checkers)
        # Check if any of our single checkers are hitable by opponent dice
        # Opponent moves: if opp is White (0->23), they move +die. If Black, -die.
        # We need to know opponent direction to know if we are safe.
        # Let's assume symmetric safety check: 
        # If we are a blot at `i`, and opponent has a checker at `i - die` (if opp is White)
        # or `i + die` (if opp is Black).
        # We can approximate by checking if `i` is "reachable" by opponent from their home side.
        # If `i` is high (18-23), it's safe from someone moving from 0 (White).
        # If `i` is low (0-5), it's safe from someone moving from 23 (Black).
        # Let's use a simple rule: Blots on 0-5 are risky if opp is close to bearing off (near 0-5).
        # Blots on 18-23 are risky if opp is near bearing off (near 18-23).
        
        # Let's find opponent home range
        opp_in_0_5 = sum(o_pts[0:6])
        opp_in_18_23 = sum(o_pts[18:24])
        opp_is_white = opp_in_18_23 >= opp_in_0_5
        
        for i in range(24):
            if p_pts[i] == 1:
                # It is a blot
                penalty = 0
                
                # Check hitting distance (assume max die 6 for generality)
                # If opp is White (0->23), they hit by moving from `i - d`
                # If opp is Black (23->0), they hit by moving from `i + d`
                # We check if there are any opp checkers within distance 6 in the "back" direction.
                
                if opp_is_white:
                    # Opponent moves +. They hit us if they are at i - d.
                    # Check range `i-6` to `i-1`
                    for d in range(1, 7):
                        if 0 <= i-d < 24:
                            if o_pts[i-d] > 0:
                                penalty += 10 - d # Closer = higher penalty
                                break # Only care about closest?
                else:
                    # Opponent moves -. They hit us if they are at i + d.
                    for d in range(1, 7):
                        if 0 <= i+d < 24:
                            if o_pts[i+d] > 0:
                                penalty += 10 - d
                                break
                
                # Extra penalty if blot is in opponent home board (very bad)
                if opp_is_white and 0 <= i <= 5: 
                    penalty += 15
                if not opp_is_white and 18 <= i <= 23:
                    penalty += 15
                    
                score -= penalty

            elif p_pts[i] > 1:
                # Good, prime building
                score += 2 * p_pts[i]
        
        # 3. Safety of Bar
        # Being on bar is bad (lost turn potential)
        score -= p_bar * 10
        
        return score

    # --- Main Logic ---

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # Determine direction (True if White/0->23, False if Black/23->0)
    c_in_0_5 = sum(my_pts[0:6])
    c_in_18_23 = sum(my_pts[18:24])
    am_white = c_in_18_23 >= c_in_0_5

    # Helper to get destination
    def get_dest(src, die):
        if src == 'B':
            # Entering from bar
            # If White (0->23), enter at 0 if 0 is open, else 23? No, White moves 0->23. 
            # So White enters at 0 (moving +die).
            # If Black (23->0), enter at 23 (moving -die).
            if am_white:
                return die # 0 + die
            else:
                return 23 - die # 23 - die
        if src == 'P': return None
        
        p = int(src[1:])
        if am_white:
            return p + die
        else:
            return p - die

    def can_enter(player_pts, opp_pts, die):
        dest = get_dest('B', die)
        if dest is None: return False
        if not (0 <= dest <= 23): return False # Bearing off handled separately
        return opp_pts[dest] < 2

    def can_move(src, die, my_pts_check, opp_pts_check, my_bar_check):
        if my_bar_check > 0:
            # Must move from bar if possible
            if src != 'B': return False
            return can_enter(my_pts_check, opp_pts_check, die)
        
        if src == 'B': return False # Can't move from bar if bar is empty
        
        p_idx = int(src[1:])
        if my_pts_check[p_idx] == 0: return False # No checker there
        
        dest = get_dest(src, die)
        
        # Bearing off
        if dest is None: 
            # Check if all checkers are in home board
            in_home = True
            for i in range(24):
                if not is_home_point(i, True) and my_pts_check[i] > 0:
                    in_home = False
                    break
            if not in_home: return False
            
            # Logic: must be able to bear off from p_idx
            # If exact match, OK. If p_idx is highest and dest>23, OK.
            # Since we are processing specific die/dst, we just need to know if p_idx is valid.
            # Standard rule: Can only bear off if all checkers in home.
            # If p_idx > die (White) or p_idx < 23-die (Black), we might need to move back if checkers behind.
            # Actually, since we are simulating, we just need to know if this move is allowed.
            # If dest is None, we are bearing off.
            # Check: is there a checker in a higher point (for White) or lower point (for Black)?
            if am_white:
                for i in range(p_idx + 1, 24):
                    if my_pts_check[i] > 0: return False
            else:
                for i in range(p_idx - 1, -1, -1):
                    if my_pts_check[i] > 0: return False
            return True

        if not (0 <= dest <= 23): return False # Out of bounds (unless bearing off, handled above)
        
        if opp_pts_check[dest] >= 2: return False # Blocked
        return True

    def apply_move(my_pts, my_bar, my_off, opp_pts, src, die):
        new_my_pts = list(my_pts)
        new_my_bar = my_bar
        new_my_off = my_off
        new_opp_pts = list(opp_pts)
        
        if src == 'B':
            dest = get_dest('B', die)
            new_my_bar -= 1
            if opp_pts[dest] == 1: # Hit
                new_opp_pts[dest] = 0
                opp_bar += 1 # We need to return opp_bar too, but for eval we keep track
                # Actually, for eval, we need to update opp_bar. 
                # Let's create a temp object for state update.
            new_my_pts[dest] += 1
        elif src == 'P':
            pass
        else:
            p_idx = int(src[1:])
            dest = get_dest(src, die)
            
            new_my_pts[p_idx] -= 1
            
            if dest is None: # Bear off
                new_my_off += 1
            else:
                if opp_pts[dest] == 1: # Hit
                    new_opp_pts[dest] = 0
                    # We don't track opp_bar in return signature of helper, but for eval we need it.
                    # We will pass opp_bar explicitly in evaluation.
                new_my_pts[dest] += 1
                
        return new_my_pts, new_my_bar, new_my_off, new_opp_pts

    # Generate all possible moves
    # If double (e.g., [4, 4], must play 4 moves if possible)
    # If distinct, play both dice.
    
    # To simplify, we will use a recursive generator or nested loops depending on dice count.
    
    possible_moves = [] # List of (move_string, resulting_score)
    
    # We need to handle the "must play higher die if only one possible" rule.
    # Let's generate moves for die 1, die 2, and both.
    
    # Construct list of dice to play (with doubles expanded)
    dice_to_play = []
    if len(dice) == 2:
        if dice[0] == dice[1]:
            dice_to_play = [dice[0]] * 4
        else:
            dice_to_play = sorted(dice, reverse=True) # Higher first
    else:
        dice_to_play = dice # 0 or 1 die

    # We need to explore sequences.
    # Let's do a BFS/DFS for the best sequence.
    # Since we can't do full lookahead (time), we evaluate after playing ALL dice or as many as possible.
    # But the rule says we MUST play both if possible.
    # So we need to find the sequence of moves that allows max dice played (if possible) and best score.
    
    # Let's define a recursive function to find best sequence
    # (current_pts, current_bar, current_off, opp_pts, dice_left, path)
    
    # But `path` needs to track "Order" (H/L) and "From1, From2".
    # The format `H:A0,A5` implies we play High die first from A0, then Low die from A5.
    # If we have 4 moves, we need `H:1,2`? No, format is fixed for 2 moves. 
    # Wait, the prompt says "up to two checker moves".
    # But the dice can be doubles. Doubles are played as 4 moves.
    # How to represent 4 moves in `H:A1,A2`?
    # Usually, the engine handles sequences. 
    # "Your action specifies only the starting points for up to two checker moves."
    # If doubles, we might need to make 4 moves.
    # The prompt example `H:A0,A18` implies 2 moves.
    # If doubles, does the engine expect 2 moves that cover 4 dice? No.
    # Does it expect repeated calls?
    # No, the API is `policy(state)` returns a string.
    # If the dice are [4, 4], the state persists until all 4 are played?
    # Or does the engine expect a sequence of moves?
    # "Return a move string... <FROM1>, <FROM2>". 
    # This implies max 2 moves.
    # BUT, Backgammon rules say you play doubles as 4 moves.
    # How does OpenSpiel handle this?
    # In OpenSpiel, the game proceeds in turns. 
    # If you roll [4, 4], you get to make moves. 
    # Usually, you make a move (e.g., 2 checkers moved using 2 dice). 
    # Then the dice remaining are [4, 4] again?
    # No, usually you play 4 moves.
    # But the prompt says "Action... <FROM1>, <FROM2>".
    # This is confusing for doubles.
    # Let's assume the `state['dice']` for doubles `[4,4]` expects a move that uses 4 dice.
    # But the format `H:A0,A18` uses 2 dice.
    # Maybe the engine repeats the policy call?
    # Let's look at "If both dice can be played, you must play both." This implies 2 moves.
    # But doubles are an exception.
    # Perhaps for doubles, `state['dice']` will be called 4 times? 
    # No, usually `state` contains the current roll.
    # If the format is strictly `H:X,Y`, it might be that doubles are treated differently.
    # OR, maybe we only return the first two moves, and the engine updates state.
    # But "You must always return a legal move string".
    # If we have 4 moves to play, returning 2 moves leaves 2 moves.
    # The prompt says "Action/Return Format: <ORDER>:<FROM1>,<FROM2>".
    # It doesn't explicitly say how to handle 4 moves.
    # Given the "up to two checker moves" phrasing, maybe doubles are not possible in the input? 
    # Or maybe we return a sequence of moves separated by something? 
    # No, the examples show single strings.
    # Let's assume if dice are [4,4], we must play 2 moves that cover 4 dice? No.
    # Let's assume the engine is smart enough to handle partial moves.
    # If I return `H:A0,B` (A0 with 4, B with 4), that's 2 moves using 2 dice.
    # This is the most likely scenario for this API format.
    # I will assume we only need to specify one move for each distinct die value.
    # If doubles [4,4], I will pick a move for die 4.
    # But the rules say "must play both (if distinct)". 
    # For doubles, usually you play 4 moves.
    # If the API is `H:X,Y`, maybe the engine just expects the first two moves?
    # Or maybe we play 4 moves in one string? `H:A0,A0,A0,A0`?
    # No, `<FROM1>,<FROM2>` implies two tokens.
    # Let's re-read: "Action specifies only the starting points for up to two checker moves."
    # Okay, I will assume that if `state['dice']` contains two distinct integers, we play two moves.
    # If `state['dice']` contains `[x, x]`, I will play a single move (or two moves if we double count?)
    # Actually, in many simple BG APIs, doubles are just played as 2 moves (using 2 dice), ignoring the "4 moves" rule to simplify.
    # Or, `state['dice']` might return `[x]` if we have to play 4 moves?
    # Let's implement a safe approach: 
    # 1. If len(dice) == 0: Pass.
    # 2. If len(dice) == 1: Play that die.
    # 3. If len(dice) == 2 and distinct: Play both.
    # 4. If len(dice) == 2 and doubles: Play both (using 2 dice).
    # Wait, standard Backgammon rules are strict on doubles.
    # Let's check the "must play both" constraint. It says "If both dice can be played, you must play both."
    # If dice are [4,4], that's two dice. 
    # If the rule is "play 4 moves", the API format is insufficient.
    # I will assume the engine allows playing 2 dice at once for doubles (even if technically 4 moves).
    # OR, `state['dice']` might be passed as `[4, 4, 4, 4]` if the engine expects 4 moves?
    # No, the prompt says `dice`: "list of 0, 1, or 2 integers".
    # So we only get 0, 1, or 2 dice.
    # This strongly implies we play 1 or 2 moves.
    # Therefore, I will treat doubles as playing 2 moves (using 2 dice).
    # (Note: This is a simplification of BG rules, but fits the API constraints).
    
    # Let's refine the move generation.
    # We need to generate moves for 1 or 2 dice.
    # Let `moves_1` be all possible single moves using one die.
    # Let `moves_2` be all possible pairs of moves using two dice (or one die if the other is unplayable).
    
    # We need to handle the "must play higher die" rule if only one move is possible.
    
    # Let's get all sources we can move from.
    sources = []
    if my_bar > 0:
        sources.append('B')
    else:
        for i in range(24):
            if my_pts[i] > 0:
                sources.append(f'A{i}')
    
    # If no sources (or all blocked), return P,P or H:P,P or L:P,P
    if not sources:
        # Check if we can even enter if on bar
        can_enter_any = False
        if my_bar > 0:
            for d in dice:
                if can_enter(my_pts, opp_pts, d):
                    can_enter_any = True
                    break
        if not can_enter_any:
            if len(dice) == 2:
                return f"H:P,P" # Or L? Usually H if possible.
            elif len(dice) == 1:
                return f"H:P,P" # Format requires H/L even for 1 die? 
                # Example: `H:P,P`. Yes.
            else:
                return "H:P,P"
    
    # Generate all legal single moves
    def get_single_moves(my_pts, my_bar, my_off, opp_pts, die):
        moves = []
        # If on bar, must enter
        if my_bar > 0:
            if can_enter(my_pts, opp_pts, die):
                # Calculate dest to check hit
                dest = get_dest('B', die)
                hit = 1 if opp_pts[dest] == 1 else 0
                moves.append(('B', my_pts, my_bar-1, my_off, opp_pts, hit, dest))
        else:
            for src in sources:
                if src == 'B': continue
                p_idx = int(src[1:])
                if can_move(src, die, my_pts, opp_pts, my_bar):
                    dest = get_dest(src, die)
                    hit = 1 if (dest is not None and opp_pts[dest] == 1) else 0
                    moves.append((src, my_pts, my_bar, my_off, opp_pts, hit, dest))
        return moves

    # We want to maximize score. Let's use recursion to find the best pair of moves (or 4 if doubles, but API limits to 2).
    # Wait, if API limits to 2, we can't play 4 moves.
    # I will assume we only play 2 moves max. 
    # If we have [4, 4], I will generate pairs of moves that use the dice.
    
    # Best move tracking
    best_move_str = None
    best_score = -float('inf')
    
    # Sort dice: High first.
    sorted_dice = sorted(dice, reverse=True)
    
    # If no dice
    if not dice:
        return "H:P,P"
    
    # If one die
    if len(dice) == 1:
        # Check if we can play
        moves = get_single_moves(my_pts, my_bar, my_off, opp_pts, dice[0])
        if not moves:
            return "H:P,P"
        # Evaluate each
        for (src, n_pts, n_bar, n_off, o_pts, hit, dest) in moves:
            # Apply hit?
            n_opp_pts = list(o_pts)
            n_opp_bar = opp_bar
            if hit:
                n_opp_pts[dest] = 0
                n_opp_bar += 1
            
            score = evaluate_board(n_pts, n_bar, n_off, n_opp_pts, n_opp_bar, opp_off)
            
            # Move string
            move_str = f"H:{src},P"
            if score > best_score:
                best_score = score
                best_move_str = move_str
                
        return best_move_str if best_move_str else "H:P,P"

    # If two dice
    # We need to try Die1 then Die2, and Die2 then Die1 (if distinct)
    # We need to respect "must play higher die if only one move possible".
    # We need to respect "must play both if possible".
    
    # Let's generate all valid sequences of length 2 (or 1 if only one move possible)
    # Actually, the constraint "must play both" implies we need to try to play 2 moves.
    
    # Let's generate all possible outcomes of playing 2 dice.
    # We will use a list of `(state_after_move, move_str_part, dice_remaining)`.
    
    # Initial state
    init_state = (my_pts, my_bar, my_off, opp_pts, opp_bar)
    
    # We will generate all legal paths of 2 moves.
    # We store (n_pts, n_bar, n_off, n_opp_pts, n_opp_bar, move_str_seq)
    paths = []
    
    # Function to expand one step
    def expand_step(current_pts, current_bar, current_off, current_opp_pts, current_opp_bar, remaining_dice, path_str, order_h_used):
        # remaining_dice is list of ints (e.g., [5, 6])
        if not remaining_dice:
            paths.append((current_pts, current_bar, current_off, current_opp_pts, current_opp_bar, path_str))
            return

        # Try to play one die
        # We must try playing all available dice. 
        # If we have [5, 6], we try playing 5 then 6, and 6 then 5.
        # But the output format requires specifying Order H/L based on first move.
        # So we need to track which die was played first for the final output.
        
        # However, the output format `H:A0,A18` means first move used High die (6), second used Low (5).
        # If we play 5 then 6, it should be `L:A0,A18`? No, `L` means first move uses Lower die.
        # So if dice are [5, 6], 
        # Path 1: Move 6 (High), then 5 (Low). Output `H:6_src,5_src`.
        # Path 2: Move 5 (Low), then 6 (High). Output `L:5_src,6_src`.
        
        # So we need to try both orders.
        
        # Also, if only one die can be played (e.g., 5 can be played but 6 cannot), 
        # we MUST play the higher die (6) if possible. 
        # If 6 cannot be played, we play 5.
        
        # If neither can be played -> Pass.
        
        # Let's separate logic based on distinct/doubles.
        
        pass # Defined below

    # Let's implement the logic specifically for 2 dice
    
    d1, d2 = sorted_dice[0], sorted_dice[1] # d1 is High, d2 is Low
    
    # Check availability of moves for each die from initial state
    moves_d1 = get_single_moves(my_pts, my_bar, my_off, opp_pts, d1)
    moves_d2 = get_single_moves(my_pts, my_bar, my_off, opp_pts, d2)
    
    has_d1 = len(moves_d1) > 0
    has_d2 = len(moves_d2) > 0
    
    # Strategy:
    # 1. If both moves possible, try both orders (D1->D2 and D2->D1).
    # 2. If only D1 possible, play D1 then Pass (or D1 twice if doubles? No, we have distinct dice).
    #    Actually, if we have [5, 6] and only 6 is possible, we MUST play 6.
    #    But we must play both if possible. If only 6 is possible, we play 6.
    #    Do we need to specify the second move? Yes, `H:A0,P`.
    # 3. If only D2 possible, we play D2.
    #    BUT "If only one die can be played, you must play the higher die when possible."
    #    If only D2 is possible, D1 was NOT possible. So we play D2.
    #    But wait, if D1 is not possible, we play D2.
    #    The format `L:A0,P` means first move uses Lower die.
    
    # Let's build a list of candidate paths (sequence of 2 actions)
    candidates = []
    
    # Helper to apply a move and return new state
    def apply_move_clean(pts, bar, off, opp_pts, opp_bar, src, die):
        # Returns new state
        n_pts = list(pts)
        n_bar = bar
        n_off = off
        n_opp_pts = list(opp_pts)
        n_opp_bar = opp_bar
        
        if src == 'B':
            dest = get_dest('B', die)
            n_bar -= 1
            if n_opp_pts[dest] == 1:
                n_opp_pts[dest] = 0
                n_opp_bar += 1
            n_pts[dest] += 1
        else:
            p_idx = int(src[1:])
            dest = get_dest(src, die)
            n_pts[p_idx] -= 1
            if dest is None:
                n_off += 1
            else:
                if n_opp_pts[dest] == 1:
                    n_opp_pts[dest] = 0
                    n_opp_bar += 1
                n_pts[dest] += 1
        return n_pts, n_bar, n_off, n_opp_pts, n_opp_bar

    # Case A: Try playing High (d1) first
    if has_d1:
        for move1 in moves_d1:
            src1, n_pts1, n_bar1, n_off1, o_pts1, hit1, dest1 = move1
            # Update opp bar if hit
            n_opp_bar1 = opp_bar + (1 if hit1 else 0)
            n_opp_pts1 = list(o_pts1)
            if hit1: n_opp_pts1[dest1] = 0
            
            # Now try playing second die (d2) from new state
            moves_d2_next = get_single_moves(n_pts1, n_bar1, n_off1, n_opp_pts1, d2)
            
            if moves_d2_next:
                for move2 in moves_d2_next:
                    src2, n_pts2, n_bar2, n_off2, o_pts2, hit2, dest2 = move2
                    n_opp_bar2 = n_opp_bar1 + (1 if hit2 else 0)
                    n_opp_pts2 = list(o_pts2)
                    if hit2: n_opp_pts2[dest2] = 0
                    
                    score = evaluate_board(n_pts2, n_bar2, n_off2, n_opp_pts2, n_opp_bar2, opp_off)
                    move_str = f"H:{src1},{src2}"
                    candidates.append((score, move_str))
            else:
                # Cannot play second die. Is that legal? 
                # "If both dice can be played, you must play both."
                # So if we play first, and second cannot be played, but maybe a DIFFERENT first move allows second?
                # Or if no move allows second, we just play first.
                # But wait, we might be forced to play High if possible.
                # If we play High and stuck, is that it?
                # If we can't play Low after High, but maybe we could have played Low then High?
                # If we can't play Low after High, but Low is playable first?
                # The rule "must play both" means if there exists *any* sequence playing both, we must.
                # So we shouldn't commit to a path that blocks the second die unless no path allows both.
                # So we shouldn't add this candidate yet. We only add if we can play both.
                # Unless we CANNOT play both in any way.
                pass

    # Case B: Try playing Low (d2) first
    # Only relevant if d1 != d2 (distinct dice)
    if d1 != d2 and has_d2:
        for move1 in moves_d2:
            src1, n_pts1, n_bar1, n_off1, o_pts1, hit1, dest1 = move1
            n_opp_bar1 = opp_bar + (1 if hit1 else 0)
            n_opp_pts1 = list(o_pts1)
            if hit1: n_opp_pts1[dest1] = 0
            
            # Try playing d1 next
            moves_d1_next = get_single_moves(n_pts1, n_bar1, n_off1, n_opp_pts1, d1)
            
            if moves_d1_next:
                for move2 in moves_d1_next:
                    src2, n_pts2, n_bar2, n_off2, o_pts2, hit2, dest2 = move2
                    n_opp_bar2 = n_opp_bar1 + (1 if hit2 else 0)
                    n_opp_pts2 = list(o_pts2)
                    if hit2: n_opp_pts2[dest2] = 0
                    
                    score = evaluate_board(n_pts2, n_bar2, n_off2, n_opp_pts2, n_opp_bar2, opp_off)
                    move_str = f"L:{src1},{src2}"
                    candidates.append((score, move_str))
            else:
                # Cannot play second die
                pass

    # Now handle the case where we CANNOT play both dice.
    # We need to check if ANY candidate exists.
    if not candidates:
        # We cannot play both dice.
        # We must play the higher die if possible.
        if has_d1:
            # Play High
            # We pick the best move for High
            best_move = None
            best_s = -float('inf')
            for move1 in moves_d1:
                src1, n_pts1, n_bar1, n_off1, o_pts1, hit1, dest1 = move1
                n_opp_bar1 = opp_bar + (1 if hit1 else 0)
                n_opp_pts1 = list(o_pts1)
                if hit1: n_opp_pts1[dest1] = 0
                
                s = evaluate_board(n_pts1, n_bar1, n_off1, n_opp_pts1, n_opp_bar1, opp_off)
                if s > best_s:
                    best_s = s
                    best_move = src1
            
            return f"H:{best_move},P"
            
        elif has_d2:
            # Play Low
            best_move = None
            best_s = -float('inf')
            for move1 in moves_d2:
                src1, n_pts1, n_bar1, n_off1, o_pts1, hit1, dest1 = move1
                n_opp_bar1 = opp_bar + (1 if hit1 else 0)
                n_opp_pts1 = list(o_pts1)
                if hit1: n_opp_pts1[dest1] = 0
                
                s = evaluate_board(n_pts1, n_bar1, n_off1, n_opp_pts1, n_opp_bar1, opp_off)
                if s > best_s:
                    best_s = s
                    best_move = src1
            
            return f"L:{best_move},P"
            
        else:
            # Cannot play any
            return "H:P,P"

    # If we have candidates (played both), pick the best score
    # But wait, if dice are [x, x], the rules are slightly different?
    # In my logic, d1=d2.
    # If d1=d2, `has_d1` and `has_d2` are same.
    # Case A runs.
    # Case B doesn't run (d1==d2).
    # So we only try playing High first.
    # Is that correct for doubles?
    # In standard BG, order doesn't matter for doubles.
    # So playing High first is fine.
    
    # However, there is a catch. "If only one die can be played, you must play the higher die."
    # This is handled in the "no candidates" block.
    
    # Also, "You may not move onto a point occupied by 2 or more opposing checkers."
    # Handled in `can_move`.
    
    # Finally, sort candidates by score and pick best
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    if candidates:
        return candidates[0][1]

    # Fallback
    return "H:P,P"
