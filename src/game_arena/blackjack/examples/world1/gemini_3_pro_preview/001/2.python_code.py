
import sys

# Global cache to store the opponent's equilibrium score distribution for a given target.
# This ensures that if the function is called repeatedly for the same game/target,
# we don't recompute the fixed point every time.
_NASH_CACHE = {}

def policy(hand: list[str], target: int) -> str:
    """
    Decides whether to HIT or STAY in a simplified Blackjack game.
    Implements a Nash Equilibrium solver to play optimally against a rational opponent.
    """
    
    # --- Helper Functions ---

    def get_card_value(c):
        """Returns the numeric value of a card (A=1 for tracking sums)."""
        if c in ['J', 'Q', 'K', '10']:
            return 10
        if c == 'A':
            return 1
        return int(c)

    def calculate_final_score(raw_sum, has_ace, t):
        """Calculates the best valid score given a raw sum (where A=1) and ace presence."""
        # If we have an Ace and promoting it to 11 keeps us <= Target, do it.
        if has_ace and raw_sum + 10 <= t:
            return raw_sum + 10
        return raw_sum

    def solve_game_recursion(curr_sum, has_ace, deck_tuple, t, opp_dist, memo):
        """
        Recursive DP to solve the single-player MDP given a fixed opponent distribution.
        Returns: (expected_utility, outcome_distribution_list)
        """
        state_key = (curr_sum, has_ace, deck_tuple)
        if state_key in memo:
            return memo[state_key]
        
        # 1. Check if we have already busted
        if curr_sum > t:
            # Result:
            # If Opponent Busts -> Draw (0)
            # If Opponent <= T -> Lose (-1)
            # Expected U = 0 * P(Bust) + (-1) * P(Ok)
            p_opp_bust = opp_dist[t + 1]
            p_opp_ok = 1.0 - p_opp_bust
            u_bust = -p_opp_ok
            
            # Outcome distribution: 100% bust
            d_bust = [0.0] * (t + 2)
            d_bust[t + 1] = 1.0
            return u_bust, d_bust
        
        # 2. Calculate Utility of STAY
        my_score = calculate_final_score(curr_sum, has_ace, t)
        
        # Breakdown against opponent's outcomes:
        # Win (+1): Opponent Busts OR Opponent < MyScore
        # Draw (0): Opponent == MyScore
        # Lose (-1): Opponent > MyScore (and not bust)
        
        p_opp_bust = opp_dist[t + 1]
        p_win_score = sum(opp_dist[i] for i in range(my_score))
        p_lose_score = sum(opp_dist[i] for i in range(my_score + 1, t + 1))
        
        u_stay = p_opp_bust + p_win_score - p_lose_score
        
        d_stay = [0.0] * (t + 2)
        d_stay[my_score] = 1.0
        
        # 3. Calculate Utility of HIT
        total_cards = sum(deck_tuple)
        if total_cards == 0:
            # Cannot hit if deck is empty
            memo[state_key] = (u_stay, d_stay)
            return u_stay, d_stay
            
        u_hit_avg = 0.0
        d_hit_avg = [0.0] * (t + 2)
        
        # Iterate over all distinct card values remaining in deck
        # deck_tuple indices 0..9 correspond to card values 1..10
        for i, count in enumerate(deck_tuple):
            if count > 0:
                prob = count / total_cards
                val = i + 1
                
                # Next state parameters
                ns_sum = curr_sum + val
                ns_ace = has_ace or (val == 1)
                
                # Remove card from deck
                new_deck_list = list(deck_tuple)
                new_deck_list[i] -= 1
                ns_deck = tuple(new_deck_list)
                
                # Recursion
                u_next, d_next = solve_game_recursion(ns_sum, ns_ace, ns_deck, t, opp_dist, memo)
                
                # Weighted average
                u_hit_avg += prob * u_next
                for k in range(t + 2):
                    d_hit_avg[k] += prob * d_next[k]
        
        # 4. Decision: Choose Max Utility
        # We break ties in favor of STAY to reduce variance, but strictly > is fine.
        if u_hit_avg > u_stay + 1e-9:
            res = (u_hit_avg, d_hit_avg)
        else:
            res = (u_stay, d_stay)
            
        memo[state_key] = res
        return res

    def get_equilibrium_dist(t):
        """Iteratively solves for the Nash Equilibrium distribution of expected scores."""
        if t in _NASH_CACHE:
            return _NASH_CACHE[t]
        
        # Initial guess: Opponent plays somewhat randomly or conservatively.
        # We start with a distribution where opponent busts 30% of time and is uniform otherwise.
        # The fixed point iteration converges quickly regardless of start.
        dist = [0.0] * (t + 2)
        dist[t+1] = 0.3
        rem = 0.7
        # Spread remaining prob over reasonable scores (e.g., T-10 to T)
        start_range = max(0, t - 10)
        count = t - start_range + 1
        for i in range(start_range, t + 1):
            dist[i] = rem / count
            
        # Full deck state for the start of the game
        # 1 of each (A-9), 4 of 10s.
        start_deck = tuple([1]*9 + [4])
        
        # Fixed point iteration
        for _ in range(4):
            memo_iter = {}
            # Solve game from scratch (sum=0, ace=False) against current 'dist'
            _, new_dist = solve_game_recursion(0, False, start_deck, t, dist, memo_iter)
            dist = new_dist
            
        _NASH_CACHE[t] = dist
        return dist

    # --- Main Execution Path ---

    # 1. Reconstruct current state from hand
    #   - current_sum (hard sum)
    #   - current_has_ace (boolean)
    #   - current_deck (tuple of counts)
    current_deck_list = [1]*9 + [4]
    current_sum = 0
    current_has_ace = False
    
    for c in hand:
        val = get_card_value(c)
        current_sum += val
        if val == 1:
            current_has_ace = True
        idx = val - 1
        current_deck_list[idx] -= 1
        
    current_deck = tuple(current_deck_list)
    
    # 2. Get Optimal Opponent Distribution
    opp_dist = get_equilibrium_dist(target)
    
    # 3. Evaluate HIT vs STAY for the current specific hand
    # If we have already busted, we must stay (game rules trigger loss anyway)
    if current_sum > target:
        return "STAY"
        
    # Calculate Utility of Staying now
    my_pts = calculate_final_score(current_sum, current_has_ace, target)
    p_bust = opp_dist[target + 1]
    p_win = sum(opp_dist[i] for i in range(my_pts))
    p_lose = sum(opp_dist[i] for i in range(my_pts + 1, target + 1))
    u_stay = p_bust + p_win - p_lose
    
    # Calculate Utility of Hitting (One step lookahead + recursion)
    if sum(current_deck) == 0:
        return "STAY"
        
    u_hit = 0.0
    total_cards = sum(current_deck)
    memo_eval = {} # Fresh memo for this specific sub-tree evaluation
    
    for i, count in enumerate(current_deck):
        if count > 0:
            prob = count / total_cards
            val = i + 1
            
            ns_sum = current_sum + val
            ns_ace = current_has_ace or (val == 1)
            
            # Construct next deck state
            new_deck_list = list(current_deck_list)
            new_deck_list[i] -= 1
            ns_deck = tuple(new_deck_list)
            
            # Get max utility of the resulting state
            u_next, _ = solve_game_recursion(ns_sum, ns_ace, ns_deck, target, opp_dist, memo_eval)
            u_hit += prob * u_next
            
    # Decision
    if u_hit > u_stay + 1e-9:
        return "HIT"
    else:
        return "STAY"
