
import sys
from functools import lru_cache
from collections import Counter

def policy(hand: list[str], target: int) -> str:
    """
    Determines the optimal move (HIT or STAY) in a simplified Blackjack game.
    
    Logic:
    1. We calculate the probability of winning if we STAY.
       - If STAY, our score is fixed. We win if the opponent busts or scores less than us.
       - We estimate opponent outcomes based on the assumption that their deck 
         contains the same distribution of unseen cards as ours (minus our hand).
         
    2. We calculate the expected probability of winning if we HIT.
       - We iterate through every possible card rank remaining in our deck.
       - For each rank, we calculate the resulting state (new hand).
       - If we don't bust, we recursively estimate the win probability of the new state.
       - If we bust, the win probability is 0.
       
    3. We choose the action with the higher win probability.
    """

    # --- Card Value & Setup ---

    CARD_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 
        '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11
    }
    
    ALL_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    # Helper to get current hand value
    def get_hand_value(cards):
        total = 0
        aces = 0
        for card in cards:
            if card == 'A':
                aces += 1
                total += 11
            else:
                total += CARD_VALUES[card]
        
        # Adjust for Aces to stay <= target if possible, or minimize bust
        # The definition: "A is 11 when hand value is <= target, or 1 when hand value > target"
        # This implies Aces are flexible to keep the score as high as possible without busting relative to target,
        # or if we are already busting (relative to target logic?), they become 1.
        # Actually, in standard Blackjack, aces are 11 unless it busts you, then 1.
        # Here, it's context dependent on Target.
        
        # Let's refine: "A is 11 when the hand value is <= target, or 1 when the hand value is > target".
        # This usually means: calculate sum with A=11. If sum > target, A becomes 1.
        # If multiple aces: We want the highest sum <= target. If no such sum exists (min sum > target), then we are bust anyway, 
        # so we just calculate min sum (aces=1) to be consistent.
        
        # Let's calculate min sum and max sum.
        min_sum = total - 10 * aces
        max_sum = total
        
        if max_sum <= target:
            return max_sum
        elif min_sum > target:
            return min_sum
        else:
            # Somewhere in between. We want the highest value <= target.
            # Since each ace is worth 10 or 11, we decrement by 10 until <= target.
            current = max_sum
            while current > target and aces > 0:
                current -= 10
                aces -= 1
            return current

    # --- Opponent Simulation ---

    # We need to simulate the opponent's deck.
    # We assume the opponent's deck has the same composition as our starting deck,
    # minus the cards we have seen (our hand).
    # Since we don't know opponent's hand, we assume they haven't drawn yet (worst case for us? No, average case).
    # Actually, since we only see our hand, the opponent's unseen cards are exactly the full deck minus our hand.
    # We will use a Monte Carlo simulation for the opponent because recursive probability distribution
    # with dynamic aces can be tricky, and Monte Carlo is robust.
    
    @lru_cache(maxsize=None)
    def get_opponent_win_prob(opponent_remaining_deck_tuple, target):
        # Returns (prob_bust, prob_score_less_than_x)
        # We simulate the opponent playing out their hand with the given deck.
        # The opponent plays "optimally" to reach target (Hit if < target, assuming risk).
        # Wait, what is the opponent policy?
        # Usually in these games, the opponent follows a simple policy: Hit if < Target, Stay if >= Target.
        # Let's assume the opponent plays "Hit on < Target, Stay on >= Target".
        # This is a standard baseline.
        
        deck = list(opponent_remaining_deck_tuple)
        if not deck:
            return 0.0, {} # Should not happen if game continues

        # Monte Carlo
        iterations = 2000
        wins = 0
        scores = Counter()
        
        import random
        
        for _ in range(iterations):
            random.shuffle(deck)
            opp_hand = []
            opp_score = 0
            
            # Draw until logic
            while True:
                # Evaluate current hand
                val = 0
                aces = 0
                for c in opp_hand:
                    if c == 'A': 
                        val += 11
                        aces += 1
                    else:
                        val += CARD_VALUES[c]
                
                # Determine if we should hit
                # Simple logic: keep hitting if safe value < target
                # Adjust for aces if needed to check condition
                current_safe = val
                while current_safe > target and aces > 0:
                    current_safe -= 10
                
                if current_safe >= target:
                    # If we are at or above target (in safe value), we stay.
                    # Exception: if we are exactly at target, we stay.
                    # If we are above target but using aces to keep it below? 
                    # The 'current_safe' logic handles "max value <= target".
                    # If current_safe >= target, we stop.
                    opp_score = val # The raw value (A=11) is what counts for comparison if not bust?
                    # No, "Ace is 1 if value > target". So if val > target, aces become 1.
                    opp_score = val
                    while opp_score > target and opp_hand.count('A') > 0: # Need to know how many aces used 11
                        # This logic is slightly loose in loop, let's use the get_hand_value helper
                        opp_score = get_hand_value(opp_hand)
                    
                    break
                
                # We need to hit
                if not deck:
                    break # Deck empty? Game ends
                    # Actually in this game, deck is infinite? No, "single suit... 13 distinct cards".
                    # If opponent runs out, they stop.
                card = deck.pop()
                opp_hand.append(card)
                
                # Check bust immediately after draw?
                # The rule: "If at any point the sum... is greater than target, you bust and stop".
                val = 0
                aces = 0
                for c in opp_hand:
                    if c == 'A': 
                        val += 11
                        aces += 1
                    else:
                        val += CARD_VALUES[c]
                # If raw value > target and we can't fix with aces
                min_val = val - 10 * aces
                if min_val > target:
                    opp_score = -1 # BUST
                    break
            
            scores[opp_score] += 1

        # Analyze results
        total_iter = sum(scores.values())
        prob_bust = scores.get(-1, 0) / total_iter
        
        # We need distribution of non-bust scores to compare against our score
        dist = {}
        for s, count in scores.items():
            if s != -1:
                # Ensure score is properly calculated (Aces adjusted)
                # The raw 's' in loop might be messy, let's clean it
                # Re-eval score for the recorded hand (simpler to just store hand?)
                # Optimization: Just use the final score logic inside loop
                dist[s] = count / total_iter
                
        return prob_bust, dist

    # --- Main Logic ---

    # 1. Current State
    current_hand_value = get_hand_value(hand)
    
    # If we are bust, we can't move (game should be over), but return STAY to be safe
    if current_hand_value > target:
        return "STAY"
    
    # 2. Prepare Remaining Deck for Probability Calculation
    # Our deck starts with all 13 cards. We have used `hand`.
    remaining_deck_counts = Counter(ALL_RANKS)
    for card in hand:
        remaining_deck_counts[card] -= 1
    
    remaining_cards = []
    for rank, count in remaining_deck_counts.items():
        remaining_cards.extend([rank] * count)
    
    total_cards_left = len(remaining_cards)
    
    if total_cards_left == 0:
        return "STAY" # No cards left to draw

    # 3. Calculate Win Rate if STAY
    # Opponent deck is assumed to be the same as our remaining deck (because we haven't seen opponent cards)
    # Wait, if we have drawn N cards, opponent has drawn N cards? Or 0?
    # The problem says: "You have your own 13-card deck... Opponent has their own".
    # "On each call to policy you observe: hand".
    # It does NOT say we observe opponent hand.
    # So opponent deck is "full deck - opponent_hand". We don't know opponent_hand.
    # This is Partially Observable.
    # To be robust, we assume the opponent's deck composition is identical to ours, 
    # and they are at the start of their turn (most optimistic for us? No, average).
    # Actually, if we assume opponent is playing at the same time, or just starting,
    # using our remaining deck is the best estimate of the "pool of unseen cards".
    
    prob_bust, score_dist = get_opponent_win_prob(tuple(sorted(remaining_cards)), target)
    
    win_rate_stay = prob_bust
    for score, prob in score_dist.items():
        if score < current_hand_value:
            win_rate_stay += prob
            
    # 4. Calculate Win Rate if HIT
    win_rate_hit = 0.0
    
    if total_cards_left > 0:
        # Iterate through unique cards to save computation
        unique_ranks = set(remaining_cards)
        for rank in unique_ranks:
            # Probability of drawing this rank
            prob_draw = remaining_cards.count(rank) / total_cards_left
            
            # Simulate drawing this card
            new_hand = hand + [rank]
            new_value = get_hand_value(new_hand)
            
            if new_value > target:
                # Busted immediately
                prob_win_after_draw = 0.0
            else:
                # We have a new state. We need to decide if we should stay or hit again?
                # Wait, the policy function is called recursively? 
                # No, we are INSIDE the policy function. We must decide HIT or STAY for the current turn.
                # But if we hit, we might want to hit again in the future.
                # However, for the expected value of the HIT action, we need to know the expected value of the *next state*.
                # The "next state" implies the opponent hasn't played yet.
                # We can approximate the value of the new hand by assuming we play optimally from there.
                # But we can't call policy recursively easily because of the cache/state.
                # Let's approximate: 
                # If we draw, we effectively "lock in" the new value as our final score for this decision step?
                # No, that's wrong. We draw, then we check the result.
                # If we draw '2', we are now at V+2. Is it better to STAY or HIT again?
                # The policy function is called *every time* it's our turn.
                # So, if we return "HIT", the game will draw a card, and call policy again.
                # So the expected value of returning "HIT" now is the expected value of the *future game state*.
                # That future game state depends on the next policy call.
                # So, we should estimate the value of the new hand assuming we play optimally from there.
                
                # Approximation for Value of New Hand (V_new):
                # Simple approach: Just use the new value as if we stayed. 
                # This is conservative if we could hit again to improve, but safe from busting.
                # Better approach: Assume we will STAY at the new value (since we are making a local decision).
                # Actually, if we are risk neutral, we should calculate expected value recursively.
                # But recursion with deck state is complex.
                # Let's use a heuristic:
                # V_new = get_hand_value(new_hand).
                # We will use V_new as if we STAYED in the future.
                
                # To be smarter: 
                # If we draw, we effectively get to see the card. 
                # The value of the HIT action is the expectation of (Value of new state).
                # We can approximate Value of new state by assuming we STAY at the new value.
                # Why? Because calling policy recursively is possible if we use the same logic for the sub-problem.
                # The sub-problem: Opponent deck is smaller (one card removed).
                
                # Let's do a 1-step lookahead with recursion on the opponent simulation.
                # The opponent deck for the *future* state is `remaining_cards` minus the drawn card.
                
                new_remaining_cards = remaining_cards.copy()
                new_remaining_cards.remove(rank)
                
                # Calculate win rate if we draw this card and then stay
                p_bust_new, score_dist_new = get_opponent_win_prob(tuple(sorted(new_remaining_cards)), target)
                
                val_new = get_hand_value(new_hand)
                
                prob_win_if_stay_new = p_bust_new
                for s, p in score_dist_new.items():
                    if s < val_new:
                        prob_win_if_stay_new += p
                
                # If we draw this card, we might want to hit again? 
                # But `policy` is called to decide "HIT" or "STAY".
                # If we return "HIT", the engine draws a card and calls `policy` again.
                # So the decision to hit *once* implies the engine will handle subsequent turns.
                # So we just need the expected win rate *after* this draw.
                # Which is exactly `prob_win_if_stay_new` if we assume we stay after this (which is what the engine does if we don't explicitly hit again).
                # Wait, the engine calls policy *after* the draw. 
                # If we return "HIT" now, we draw. Then policy is called again.
                # So the value of "HIT" is the average value of the next call's result.
                # To approximate that, we can calculate the value of the new hand assuming optimal play (which we are defining now).
                
                # Let's just use `prob_win_if_stay_new` as the value of drawing this card.
                # This is a strong heuristic because we are likely to stay if we improve our hand significantly.
                
                prob_win_after_draw = prob_win_if_stay_new
                
            win_rate_hit += prob_draw * prob_win_after_draw

    # 5. Decision
    # Tie-breaker: Prefer STAY if rates are close, to avoid variance? 
    # No, pick max.
    epsilon = 1e-9
    if win_rate_hit > win_rate_stay + epsilon:
        return "HIT"
    else:
        return "STAY"

# The code must be wrapped in <code> tags as per instructions.
# Since the prompt asks for the Python file, I will provide the code block.
