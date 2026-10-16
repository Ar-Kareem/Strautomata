
import random

def policy(hand: list[str], target: int) -> str:
    """
    Deterministic policy for simplified Blackjack using Expected Value Analysis
    and Exact Card Counting.
    """
    
    # --- 1. Setup & Constants ---
    # Full deck of 13 cards
    FULL_DECK = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Map ranks to their integer values (A is handled dynamically)
    RANK_VALUES = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
    }
    
    # --- 2. Calculate Current Hand Value ---
    # Standardize hand to lowercase to handle any case sensitivity
    hand_upper = [c.upper() for c in hand]
    
    def get_hand_sum(cards):
        """Calculates the sum of cards, treating A as 11 if <= target, else 1."""
        total = 0
        aces = 0
        
        for card in cards:
            if card == "A":
                aces += 1
                total += 11
            else:
                total += RANK_VALUES[card]
        
        # Adjust for Aces if we are over target
        while total > target and aces > 0:
            total -= 10  # Treat Ace as 1 instead of 11
            aces -= 1
            
        return total

    current_sum = get_hand_sum(hand_upper)
    
    # If we are already over target, we have busted (though policy shouldn't be called)
    if current_sum > target:
        return "STAY" # Busted, cannot hit anymore

    # --- 3. Determine Remaining Deck ---
    # Count cards currently in hand
    hand_counts = {rank: hand_upper.count(rank) for rank in FULL_DECK}
    
    # Calculate remaining cards in our private deck
    remaining_counts = {}
    remaining_cards = []
    
    for rank in FULL_DECK:
        count = 1 - hand_counts.get(rank, 0)
        if count > 0:
            remaining_counts[rank] = count
            remaining_cards.append(rank)
            
    num_remaining = len(remaining_cards)
    
    # If deck is empty, we must stay
    if num_remaining == 0:
        return "STAY"

    # --- 4. Evaluate "Stay" Score (Win Probability Estimate) ---
    # Since we don't know opponent's hand, we use a heuristic.
    # A hand close to target is generally strong. 
    # We define the "static value" of staying as (target - current_sum).
    # We add a "safety bonus" for strong hands to discourage hitting.
    # Heuristic: 
    #   Sum < 12: Very weak (High risk of opponent beating us).
    #   Sum >= target - 4: Very strong (High risk of busting).
    
    # Base value of staying: how close are we? (Lower distance is better)
    dist_from_target = target - current_sum
    
    # --- 5. Evaluate "Hit" Expectation ---
    # We calculate Expected Value (EV) of hitting.
    # EV = Sum(Prob(card) * Value(card_result))
    # Value(result) = target - new_sum (if new_sum <= target)
    # Value(result) = -Infinity (or large penalty) (if new_sum > target)
    
    total_expected_improvement = 0
    
    for card in remaining_cards:
        prob = 1.0 / num_remaining
        
        # Simulate drawing this card
        potential_hand = hand_upper + [card]
        new_sum = get_hand_sum(potential_hand)
        
        if new_sum > target:
            # BUST: We assign a heavy penalty. 
            # Penalty is proportional to how much we bust (distance).
            # If we bust, we effectively lose (unless opponent also busts, but we assume risk).
            # Penalty = -(target * 2) ensures we prefer staying on safe hands.
            value = -(target * 1.5) 
        else:
            # SAFE: Value is how much closer we got.
            # We want to minimize (target - new_sum).
            # We prefer hitting if we can get closer to target without busting.
            value = (target - new_sum)
            
        total_expected_improvement += (prob * value)

    # --- 6. Comparative Decision Logic ---
    # We compare the "Static Value" of staying vs "Expected Value" of hitting.
    
    # Threshold Logic:
    # We prefer staying if:
    # 1. We are very close to target (high probability of busting on hit).
    # 2. The expected improvement from hitting is marginal compared to the risk.
    
    # Normalize the "Stay" value to be comparable to the "Hit" value calculation.
    # The "Hit" value calculation measures closeness to 0 (distance).
    # The "Stay" value is simply the current distance.
    expected_value_stay = dist_from_target
    
    # If EV of hitting is better than staying, we Hit.
    # We add a small margin (epsilon) to favor staying in ambiguous situations (risk management).
    epsilon = 0.2 
    
    if total_expected_improvement < (expected_value_stay - epsilon):
        return "STAY"
    else:
        return "HIT"
