
def policy(hand: list[str], target: int) -> str:
    # 1. Setup and Parsing
    # Card values mapping for logic
    def parse_card_val(c_str):
        if c_str in ['J', 'Q', 'K']: return 10
        if c_str == 'A': return 11
        return int(c_str)

    # Standard "Full Deck" representation
    # Indices: 0->A(11), 1->2 ... 8->9, 9->10(10)
    # CARD_VALS corresponds to these indices
    CARD_VALS = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    # Counts in a full 13-card deck: 1 of each A-9, 4 of 10s
    FULL_DECK_COUNTS = (1, 1, 1, 1, 1, 1, 1, 1, 1, 4)

    # Helper to calculate score based on prompt rules
    def get_score(vals, tgt):
        s = sum(vals)
        aces = vals.count(11)
        # "A" -> 11 when <= target, else 1
        # We start with max possible (all 11) and reduce 10 per Ace until <= tgt
        while s > tgt and aces > 0:
            s -= 10
            aces -= 1
        return s

    # 2. Opponent Probability Distribution (DP)
    # We calculate the probability of the opponent ending up with each score.
    # We assume a heuristic policy for the opponent: Hit if score <= target - 5.
    
    opp_dist = {'BUST': 0.0}
    # Initialize score outcomes 1..Target
    for s in range(1, target + 1):
        opp_dist[s] = 0.0
        
    # BFS / Layer-wise probability propagation
    # State: tuple of card counts remaining in deck
    current_layer = {FULL_DECK_COUNTS: 1.0}
    
    # Max cards is 13, loop enough times to exhaust deck
    for _ in range(14):
        if not current_layer: break
        next_layer = {}
        
        for counts, prob in current_layer.items():
            # Reconstruct opponent's hand from missing cards to calc score
            hand_vals = []
            for i, qty in enumerate(counts):
                used = FULL_DECK_COUNTS[i] - qty
                if used > 0:
                    hand_vals.extend([CARD_VALS[i]] * used)
            
            score = get_score(hand_vals, target)
            
            if score > target:
                opp_dist['BUST'] += prob
                continue
            
            # Opponent Policy Heuristic
            is_empty = (sum(counts) == 0)
            should_stay = is_empty or (score >= target - 5)
            
            if should_stay:
                opp_dist[score] += prob
            else:
                # Opponent Hits - propagate probability to next deck states
                total_cards = sum(counts)
                for i, qty in enumerate(counts):
                    if qty > 0:
                        trans_prob = qty / total_cards
                        
                        nxt = list(counts)
                        nxt[i] -= 1
                        nxt_t = tuple(nxt)
                        
                        next_layer[nxt_t] = next_layer.get(nxt_t, 0.0) + prob * trans_prob
        
        current_layer = next_layer

    # 3. My Optimization (Expectimax)
    
    # Helper to calculate utility of a final stopped score
    def get_utility(my_final_score):
        # Result: Win(1), Draw(0.5), Loss(0)
        # If I bust:
        if my_final_score > target:
            # Draw if Opponent also busts
            return 0.5 * opp_dist['BUST']
        
        # If I don't bust:
        # Win if Opp busts
        u = 1.0 * opp_dist['BUST']
        
        # Win if Opp <= T and My > Opp
        for ops in range(1, target + 1):
            if ops in opp_dist and opp_dist[ops] > 0:
                if my_final_score > ops:
                    u += 1.0 * opp_dist[ops]
                elif my_final_score == ops:
                    u += 0.5 * opp_dist[ops]
                # else Loss (0.0)
        return u

    # Determine my current state
    my_hand_vals = [parse_card_val(c) for c in hand]
    my_current_counts = list(FULL_DECK_COUNTS)
    
    # Remove cards I hold from my deck
    for v in my_hand_vals:
        # Find index. A=11 (idx 0), 10=10 (idx 9), others v-1
        if v == 11: idx = 0
        elif v == 10: idx = 9
        else: idx = v - 2 + 1 # 2->1 ... 9->8
        my_current_counts[idx] -= 1
    
    memo = {}

    def solve(num_aces, sum_non_aces, deck_counts):
        state_key = (num_aces, sum_non_aces, deck_counts)
        if state_key in memo: 
            return memo[state_key]

        # Calculate current maximal valid score
        # Base sum (aces treated as 1)
        base_sum = sum_non_aces + num_aces
        
        # If even min score busts, we are done
        if base_sum > target:
            val = get_utility(999) # 999 represents Bust
            memo[state_key] = val
            return val
        
        # Optimize Aces (treat as 11 if possible)
        current_best = base_sum
        # We can add 10 for each ace provided we don't bust
        for _ in range(num_aces):
            if current_best + 10 <= target:
                current_best += 10
            else:
                break
        
        # Value of STAYing now
        u_stay = get_utility(current_best)
        
        # Value of HITting
        total_remaining = sum(deck_counts)
        if total_remaining == 0:
            # Must stay
            memo[state_key] = u_stay
            return u_stay
            
        u_hit_expected = 0.0
        for i, qty in enumerate(deck_counts):
            if qty > 0:
                prob = qty / total_remaining
                card_val = CARD_VALS[i]
                
                nxt_aces = num_aces + (1 if card_val == 11 else 0)
                nxt_non_aces = sum_non_aces + (card_val if card_val != 11 else 0)
                
                nxt_counts = list(deck_counts)
                nxt_counts[i] -= 1
                
                # Recursively get max utility of future state
                u_hit_expected += prob * solve(nxt_aces, nxt_non_aces, tuple(nxt_counts))
        
        # Expectimax: we assume we play optimally in future (Max)
        # But here 'solve' returns the value of the State.
        # The decision at the state is max(Stay, Hit_Expected).
        res = max(u_stay, u_hit_expected)
        memo[state_key] = res
        return res

    # 4. Make the Decision for the current root state
    # Calculate initial params
    init_aces = my_hand_vals.count(11)
    init_non_aces = sum(v for v in my_hand_vals if v != 11)
    
    # Calculate U_stay and U_hit for root manually to return action string
    
    # Current score
    curr_score = get_score(my_hand_vals, target)
    u_stay_now = get_utility(curr_score)
    
    # If already busted or empty deck, Stay
    if curr_score > target or sum(my_current_counts) == 0:
        return "STAY"
        
    u_hit_now = 0.0
    total = sum(my_current_counts)
    for i, qty in enumerate(my_current_counts):
        if qty > 0:
            prob = qty / total
            card_val = CARD_VALS[i]
            
            na = init_non_aces + (card_val if card_val != 11 else 0)
            ac = init_aces + (1 if card_val == 11 else 0)
            
            nc = list(my_current_counts)
            nc[i] -= 1
            
            u_hit_now += prob * solve(ac, na, tuple(nc))
            
    # Compare with slight epsilon preference for hitting if equal (rare)
    if u_hit_now > u_stay_now + 1e-7:
        return "HIT"
    else:
        return "STAY"
