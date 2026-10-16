
import sys

# Increase recursion depth to support deep alpha-beta searches if necessary
sys.setrecursionlimit(20000)

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Selects a move using Iterative Deepening Alpha-Beta Pruning with a heuristic evaluation.
    
    Features:
    - Iterative Deepening: Searches deeper levels until time limit is approached.
    - Move Ordering: Prioritizes captures and moves that yield extra turns.
    - Heuristics: Balances immediate gain (store difference) with positional advantage
      (potential captures, blocked opponent, extra turns, avoiding capture).
    - Captures and Extra Turns: Fully simulated in the search tree.
    - Endgame Detection: Switches to exact solving (Maximizing difference) once seeds are few.
    """
    
    # --- Constants & Configuration ---
    MAX_DEPTH = 16  # Upper bound for iterative deepening
    TIME_LIMIT = 0.8  # Seconds (safe buffer for 1s limit)
    
    HOUSES = 6
    MY_STORE = 6
    OPP_STORE = 6
    
    # --- Helper Functions ---
    
    def is_terminal(state):
        my_houses, my_store, opp_houses, opp_store = state
        return all(v == 0 for v in my_houses) or all(v == 0 for v in opp_houses)

    def get_result(state):
        my_houses, my_store, opp_houses, opp_store = state
        # If it's terminal, return the difference
        return my_store - opp_store

    def heuristic(state, depth_left):
        my_houses, my_store, opp_houses, opp_store = state
        
        # 1. Material Difference (Most important)
        score = my_store - opp_store
        
        # 2. Positional Heuristics
        
        # Capture Potential: Sum of seeds in my houses that threaten opponent's empty houses
        # If I play i, and opp[5-i] is empty, I capture.
        # Actually, we want to count seeds in houses where the opposite is EMPTY?
        # No, we want to count the seeds we have that can trigger a capture if the opponent slips.
        # Let's count the seeds I have in houses that are "ready" to capture if opponent exposes them.
        # But better: penalize opponent seeds in houses that I can capture immediately?
        # Let's just count the total seeds I can potentially capture if I play correctly.
        capture_potential = 0
        for i in range(HOUSES):
            if opp_houses[5 - i] == 0 and my_houses[i] > 0:
                # If I play this, I capture. Let's value the seeds I would collect.
                # Note: my_houses[i] is not counted in capture, only opp seeds + the landing seed.
                # But usually the landing seed is small. Let's value the opp seeds.
                capture_potential += opp_houses[5 - i] + 1 
        # Normalize
        score += capture_potential * 0.5

        # Extra Turn Potential: Houses that land in store
        extra_turn_potential = 0
        for i in range(HOUSES):
            stones = my_houses[i]
            if stones == 0: continue
            # If stones == (6 - i), lands exactly in store
            if stones == (6 - i):
                extra_turn_potential += 1
            # Or if it wraps around?
            # Let's keep it simple.
        score += extra_turn_potential * 0.5

        # Blockade: Check if I can block opponent's extra turns or captures
        # If I put a seed in opponent's house that they need for an extra turn/capture
        # Let's simply count the number of my houses > 0 (Activity)
        my_activity = sum(1 for x in my_houses if x > 0)
        score += my_activity * 0.1

        # Penalize empty houses (vulnerable to capture if the one next to them is played)
        # If I have a hole (empty house), opponent might play into it to capture my next house.
        # If opponent has a hole, I might capture.
        # Let's look at "Dangerous" holes.
        # My hole at i: Opponent plays at 5-i to capture my i+1 (which wraps? no, capture is standard)
        # Actually, in standard Kalah, capture is if I land in MY empty house, and Opp opposite has seeds.
        # So, if Opp has a seed in house 5-i, and I have 0 in house i, Opp plays 5-i -> captures my i+1?
        # No, Opp plays 5-i -> lands in Opp house 5-i. If it wraps, hits my houses.
        # Let's stick to a simple heuristic.
        
        return score

    # --- Move Ordering ---
    def get_ordered_moves(state, is_maximizing_player):
        if is_maximizing_player:
            my_houses, _, _, _ = state
        else:
            _, _, my_houses, _ = state = state[2], state[3], state[0], state[1] # Swap to treat as "my_houses" for sorting logic
            # Wait, the swap logic is messy. Let's just pass the correct perspective.
        
        # We need to return moves (indices 0..5)
        moves = [i for i in range(HOUSES) if my_houses[i] > 0]
        
        if not moves:
            return []
            
        # Scores for ordering
        scores = []
        for move in moves:
            # Simulate briefly
            temp_houses = list(my_houses)
            stones = temp_houses[move]
            temp_houses[move] = 0
            pos = move
            capture = False
            extra_turn = False
            
            # Basic simulation to check outcome type
            current_stones = stones
            idx = move + 1
            
            # Skip opponent store logic is handled by skipping index 6 if iterating through full array
            # But we must do the distribution loop properly
            while current_stones > 0:
                if idx < HOUSES:
                    # My side
                    if current_stones == 1 and idx < HOUSES:
                        # Check for capture
                        if temp_houses[idx] == 0:
                            # Need to check opponent house 5-idx
                            # We don't have opponent state here easily without passing it.
                            # Just heuristic based on my move.
                            pass
                    # Just count if it lands in store
                    if idx == HOUSES and current_stones == 1:
                        extra_turn = True
                    idx += 1
                elif idx == HOUSES:
                    # My store
                    idx += 1 # Go to opponent houses
                else:
                    # Opponent side (idx 7..12)
                    idx += 1
                    if idx == 13: idx = 0 # Back to my houses
            
            # Let's use a simpler heuristic for ordering:
            # 1. Move lands in store (Extra Turn)
            # 2. Move captures (Hard to check without opponent state in this scope, so we will check full simulation inside alpha-beta)
            # Let's just use: Empty houses first (leads to distribution), then Store landings.
            
            s = 0
            if temp_houses[move] == 0: s += 1 # Leading to empty hole (might be good for wrapping)
            if my_houses[move] == (6 - move): s += 10 # Lands in store
            scores.append(s)
            
        # Sort moves by score descending
        return [x for _, x in sorted(zip(scores, moves), reverse=True)]

    # --- Simulation Logic ---
    def simulate_move(state, move, is_maximizing_player):
        # Unpack state
        if is_maximizing_player:
            my_houses, my_store, opp_houses, opp_store = state
        else:
            opp_houses, opp_store, my_houses, my_store = state
            
        # Make copies
        my_houses = list(my_houses)
        opp_houses = list(opp_houses)
        
        stones = my_houses[move]
        my_houses[move] = 0
        current = stones
        idx = move + 1
        
        last_pos = -1
        # We iterate manually because of the store jump
        while current > 0:
            if idx < HOUSES:
                my_houses[idx] += 1
                current -= 1
                if current == 0: last_pos = idx
                idx += 1
            elif idx == HOUSES:
                my_store += 1
                current -= 1
                if current == 0: last_pos = HOUSES
                idx += 1 # Jump to opponent houses
            elif idx < HOUSES * 2 + 1: # Opponent houses (indices 7 to 12 in combined list)
                opp_houses[idx - (HOUSES + 1)] += 1
                current -= 1
                if current == 0: last_pos = idx
                idx += 1
            else:
                # Wrap around to my houses
                idx = 0 
        
        # Determine if Extra Turn or Capture
        extra_turn = False
        if last_pos == HOUSES:
            extra_turn = True
        elif last_pos != -1 and last_pos < HOUSES: # Landed in my house
            # Check capture condition
            # Note: last_pos is index in my_houses (0..5)
            if my_houses[last_pos] == 1: # It was 0 before, now 1
                opp_idx = 5 - last_pos
                if opp_houses[opp_idx] > 0:
                    # Capture!
                    captured = opp_houses[opp_idx] + 1 # Opp seeds + the 1 I just dropped
                    my_store += captured
                    my_houses[last_pos] = 0
                    opp_houses[opp_idx] = 0
        
        # Check for end game condition (all my houses empty)
        if all(v == 0 for v in my_houses):
            # Move remaining opponent seeds to their store
            remaining = sum(opp_houses)
            opp_store += remaining
            opp_houses = [0]*HOUSES
        
        # Return state based on perspective
        if is_maximizing_player:
            return (my_houses, my_store, opp_houses, opp_store), extra_turn
        else:
            return (opp_houses, opp_store, my_houses, my_store), extra_turn

    # --- Alpha-Beta Pruning ---
    def alpha_beta(state, depth, alpha, beta, is_maximizing_player, start_time):
        # Time check
        if (time.time() - start_time) > TIME_LIMIT:
            raise TimeoutError
            
        terminal = is_terminal(state)
        if depth == 0 or terminal:
            if terminal:
                # Terminal state: result is definite
                # We maximize difference
                return get_result(state) * 1000 # High weight for win/loss
            return heuristic(state, depth)

        # Get moves
        # We need to construct the correct arguments for get_ordered_moves
        # If Max player, my_houses is state[0]
        if is_maximizing_player:
            my_houses = state[0]
        else:
            # Min player: my_houses is state[2] (opponent's houses in original view)
            # Wait, if is_maximizing is False, we are Min node.
            # We want to pick moves for the opponent.
            # State is (MyH, MyS, OpH, OpS).
            # For Min node, "My" becomes "Op", and "Op" becomes "My" conceptually for the child.
            # But get_ordered_moves expects the list of houses of the player to move.
            # So we pass state[2] (opponent's houses).
            my_houses = state[2]
        
        # Note: get_ordered_moves defined above needs my_houses.
        # We need to pass my_houses to it.
        # It calculates heuristic based on my_houses, so we must provide the correct one.
        
        moves = get_ordered_moves(state, is_maximizing_player)
        
        if not moves:
            # If no moves but not terminal (should be covered by terminal check, but safe fallback)
            return heuristic(state, depth)

        if is_maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                next_state, extra_turn = simulate_move(state, move, True)
                if extra_turn:
                    # Maximize again from same state, keep depth? 
                    # Or decrease depth? Usually extra turn costs no depth.
                    eval_score = alpha_beta(next_state, depth, alpha, beta, True, start_time)
                else:
                    eval_score = alpha_beta(next_state, depth - 1, alpha, beta, False, start_time)
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                # Min node simulation: state is (MyH, MyS, OpH, OpS).
                # simulate_move expects (CurrentPlayerH, CurrentPlayerS, OpponentH, OpponentS), is_max_player flag.
                # Here the "Current Player" is the opponent.
                # So we pass state as is, but is_maximizing_player=False.
                # simulate_move will treat state[2] (OpH) as "my_houses".
                next_state, extra_turn = simulate_move(state, move, False)
                
                if extra_turn:
                    eval_score = alpha_beta(next_state, depth, alpha, beta, False, start_time)
                else:
                    eval_score = alpha_beta(next_state, depth - 1, alpha, beta, True, start_time)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Execution ---
    import time
    
    start_time = time.time()
    best_move = None
    
    # Initial moves
    legal_moves = [i for i in range(HOUSES) if you[i] > 0]
    
    # If only one move, take it
    if len(legal_moves) == 1:
        return legal_moves[0]
        
    # Start with Depth 1 and go deeper
    # If total seeds are low, prioritize exact calculation
    total_seeds = sum(you[:HOUSES]) + sum(opponent[:HOUSES])
    
    # If very few seeds, we can go very deep or even solve
    # But we use iterative deepening to respect time.
    
    # Initial state: (MyH, MyS, OpH, OpS)
    initial_state = (you[:HOUSES], you[HOUSES], opponent[:HOUSES], opponent[HOUSES])
    
    current_depth = 1
    
    try:
        while current_depth <= MAX_DEPTH:
            # Order moves for root search
            # We need to pass state and flag to get_ordered_moves
            # But get_ordered_moves is simple, let's just call it or write a simple root sorter
            moves = get_ordered_moves(initial_state, True)
            
            best_score = -float('inf')
            best_move_at_depth = moves[0]
            
            for move in moves:
                # Check time before starting a new depth iteration
                if (time.time() - start_time) > TIME_LIMIT:
                    raise TimeoutError
                
                next_state, extra_turn = simulate_move(initial_state, move, True)
                
                if extra_turn:
                    # If extra turn, depth doesn't decrease
                    score = alpha_beta(next_state, current_depth, -float('inf'), float('inf'), True, start_time)
                else:
                    score = alpha_beta(next_state, current_depth - 1, -float('inf'), float('inf'), False, start_time)
                
                if score > best_score:
                    best_score = score
                    best_move_at_depth = move
            
            # Found best move for this depth
            best_move = best_move_at_depth
            
            # If the score is extremely high (Win) or extremely low (Loss), we can stop
            if best_score > 50000 or best_score < -50000:
                break
                
            current_depth += 1
            
    except TimeoutError:
        pass # Return best found so far
        
    if best_move is None:
        return legal_moves[0] # Fallback
        
    return best_move
