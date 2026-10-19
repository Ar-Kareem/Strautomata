
import math

# --- Game Constants ---
CARDS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
CARD_MAP = {c: i for i, c in enumerate(CARDS)}
# Card values: 2-9 are face, 10-K are 10, A is 11 (logic handles reduction to 1)
VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]

# Global cache to store the optimal policy for a specific target T.
# This prevents re-computing the Nash Equilibrium on every call within the same game.
POLICY_CACHE = {}

def get_hand_mask(hand: list[str]) -> int:
    """Converts a list of card strings into a bitmask representing the used cards."""
    mask = 0
    for card in hand:
        mask |= (1 << CARD_MAP[card])
    return mask

def calculate_score(mask: int, target: int) -> int:
    """Calculates the standard score of a hand mask given the target."""
    raw_sum = 0
    aces = 0
    for i in range(13):
        if (mask >> i) & 1:
            val = VALUES[i]
            if val == 11:
                aces += 1
            raw_sum += val
    
    # Adjust Aces if we are over target
    while raw_sum > target and aces > 0:
        raw_sum -= 10
        aces -= 1
        
    return raw_sum

def solve_game(target: int):
    """
    Solves the game for a fixed target T using fixed-point iteration.
    Returns a dictionary mapping state_mask -> 'HIT' or 'STAY'.
    """
    if target in POLICY_CACHE:
        return POLICY_CACHE[target]

    num_states = 1 << 13  # 2^13 = 8192 distinct subsets
    
    # Probability distribution array size: Scores 0..target, plus one slot for BUST.
    # Indices: 0..target are scores. Index (target + 1) is BUST.
    idx_bust = target + 1
    prob_size = idx_bust + 1
    
    # 1. Precompute scores and transitions for all possible hand states
    # This speeds up the iterative solver significantly.
    scores = [0] * num_states
    children = [[] for _ in range(num_states)]
    
    for m in range(num_states):
        # Calculate score
        scores[m] = calculate_score(m, target)
        
        # Identify children (valid next states)
        # We can draw any card corresponding to a 0 bit
        for i in range(13):
            if not ((m >> i) & 1):
                children[m].append(m | (1 << i))
                
    # Sort states by number of cards (descending). 
    # This allows Dynamic Programming from full hands backwards to empty hands.
    sorted_masks = sorted(range(num_states), key=lambda x: bin(x).count('1'), reverse=True)

    # 2. Nash Equilibrium Solver
    # We iterate to find the opponent's outcome distribution that effectively responds to itself.
    # Initialization: Assume opponent uses a heuristic (e.g., Stand on >= Target - 8) to start.
    opp_dist = [0.0] * prob_size
    
    # Initial conservative guess for opponent distribution
    range_start = max(0, target - 8)
    initial_p = 0.8 / (target - range_start + 1) if (target - range_start + 1) > 0 else 0
    for i in range(range_start, target + 1):
        opp_dist[i] = initial_p
    opp_dist[idx_bust] = 0.2 # 20% bust chance initially
    
    # Data structures for DP
    # memo_values[m] stores the Expected Value of state m (1=Win, 0=Draw, -1=Loss)
    # memo_dists[m] stores the probability distribution of final scores starting from m
    policy_map = {}
    
    # Fixed-point iterations (usually converges in 3-5 steps for this game size)
    for _ in range(6):
        memo_values = [0.0] * num_states
        memo_dists = [[0.0] * prob_size for _ in range(num_states)]
        
        # Precompute cumulative distribution for O(1) EV calculations
        # opp_cum[x] = Sum(opp_dist[0]...opp_dist[x])
        opp_cum = [0.0] * prob_size
        running = 0.0
        for i in range(prob_size):
            running += opp_dist[i]
            opp_cum[i] = running
            
        # Value of Busting:
        # Lose (-1) if Opponent <= T. Draw (0) if Opponent Busts.
        # V_bust = (-1) * P(Opp <= T) + 0 * P(Opp Bust)
        p_opp_valid = opp_cum[target]
        val_bust = -1.0 * p_opp_valid
        
        dist_bust = [0.0] * prob_size
        dist_bust[idx_bust] = 1.0

        # DP Pass
        for m in sorted_masks:
            sc = scores[m]
            
            # Case 1: Already Busted
            if sc > target:
                memo_values[m] = val_bust
                # Copying list explicitly is safer, though references can work if careful
                memo_dists[m] = list(dist_bust)
                continue
            
            # Case 2: Stay
            # Win (1) if Opp < MyScore OR Opp Busts
            # Draw (0) if Opp == MyScore
            # Lose (-1) if MyScore < Opp <= T
            
            p_win = opp_dist[idx_bust]
            if sc > 0:
                p_win += opp_cum[sc - 1]
            
            p_loss = opp_cum[target] - opp_cum[sc]
            
            ev_stay = 1.0 * p_win + (-1.0) * p_loss
            
            # Case 3: Hit
            kids = children[m]
            if not kids:
                # No cards remaining (extremely rare/impossible if valid), must stay
                ev_hit = -99.0
            else:
                # EV of hitting is the average EV of all possible next cards
                sum_val = 0.0
                for k in kids:
                    sum_val += memo_values[k]
                ev_hit = sum_val / len(kids)
            
            # Decision
            # We add a tiny epsilon to break ties in favor of HIT unless strictly worse, 
            # though STAY preference is also valid. Here we maximize EV strictly.
            if ev_hit > ev_stay + 1e-9:
                policy_map[m] = "HIT"
                memo_values[m] = ev_hit
                
                # Compute resulting distribution (Average of children distributions)
                new_dist = [0.0] * prob_size
                for k in kids:
                    kd = memo_dists[k]
                    for i in range(prob_size):
                        new_dist[i] += kd[i]
                
                scale = 1.0 / len(kids)
                for i in range(prob_size):
                    memo_dists[m][i] = new_dist[i] * scale
            else:
                policy_map[m] = "STAY"
                memo_values[m] = ev_stay
                # Resulting distribution is 100% on current score
                memo_dists[m][sc] = 1.0

        # Update Opponent Distribution for the next iteration
        # The opponent starts from an empty hand (mask 0), and plays the computed optimal policy.
        opp_dist = list(memo_dists[0])

    POLICY_CACHE[target] = policy_map
    return policy_map

def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to HIT or STAY.
    Optimal strategy is computed/retrieved via Nash Equilibrium solver.
    """
    # Simply solve/lookup the policy for the game's target score
    pol = solve_game(target)
    
    # Map current hand to state mask
    current_mask = get_hand_mask(hand)
    
    # Return action (Default to STAY if state not found, though impossible)
    return pol.get(current_mask, "STAY")
