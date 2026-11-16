
import random

def policy(hand: list[str], target: int) -> str:
    """
    Provides a legal move for a simplified Blackjack-like game.
    Uses card counting and probability to determine the optimal action.
    """
    
    # --- Configuration ---
    # Cards available in the deck
    RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    # Values for non-Ace cards
    CARD_VALUES = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, 
        "10": 10, "J": 10, "Q": 10, "K": 10
    }

    # --- Helper Functions ---

    def get_hand_value(cards):
        """
        Calculates the current value of the hand using optimal Ace rules:
        11 if total <= target, else 1.
        """
        total = 0
        aces = 0
        
        for card in cards:
            if card == "A":
                aces += 1
            else:
                total += CARD_VALUES[card]
        
        # Add Aces
        for _ in range(aces):
            # If we can treat Ace as 11 without exceeding target, do so.
            # Note: Even if we exceed target, 11 might be better than 1 if we are calculating
            # current value (though usually we want to minimize bust). 
            # The prompt states: "A -> 11 when hand value <= target, or 1 when > target".
            # This implies a specific valuation strategy for the current state.
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        return total

    def get_card_value(card):
        if card == "A": return 11 # Conservative estimate for calculation, logic handles nuances
        return CARD_VALUES[card]

    # --- State Analysis ---

    # 1. Calculate current hand value
    current_value = get_hand_value(hand)

    # 2. Determine which cards are "known" (seen)
    # We know the cards currently in hand.
    # We also implicitly know that cards drawn in previous turns that resulted in a bust 
    # would have been seen (and the game would have ended).
    # However, since we are called again, it implies we haven't busted yet or this is a new turn.
    # We must assume we only know the cards currently in 'hand'.
    known_cards = set(hand)
    
    # 3. Analyze the deck (Remaining cards)
    remaining_cards = []
    for r in RANKS:
        # Since the deck is a standard set, we count occurrences of each rank
        # We only have 1 of each rank in this simplified game.
        if r not in known_cards:
            remaining_cards.append(r)
    
    total_remaining = len(remaining_cards)

    # --- Decision Logic ---

    # If we are at or very close to target, we should generally STAY.
    # Unless there is a significant advantage to hitting (rare in Blackjack variants without 21 specific rules).
    if current_value >= target:
        # We are at or over target (if over target, we bust, but the logic handles it)
        # If we are exactly at target, that's the best possible score. Stop.
        # If we are over target, we have already busted (value logic usually adjusts Aces, 
        # but if value > target, we are technically over).
        return "STAY"
    
    # --- Risk Assessment ---
    
    # We calculate the probability of busting on the next hit.
    # Busting happens if: current_value + card_value > target
    
    bust_threshold = target - current_value
    # We bust if we draw a card with value > bust_threshold.
    # Note: Ace is tricky.
    # If we draw an Ace:
    #   We want to add 11 if (current_value + 11 <= target). 
    #   We add 1 if (current_value + 11 > target).
    #   So, drawing an Ace is safe if (current_value + 11 <= target) OR (current_value + 1 <= target).
    #   Since current_value <= target (checked above), current_value + 1 <= target + 1.
    #   If current_value + 1 > target, then we bust even with an Ace (value 1).
    
    busting_cards_count = 0
    safe_cards_count = 0
    
    for card in remaining_cards:
        val = get_card_value(card)
        
        # Determine if this card causes a bust
        busts = False
        if card == "A":
            # If adding 11 pushes us over, we use 1.
            # We only bust if adding 1 ALSO pushes us over.
            if current_value + 1 > target:
                busts = True
        else:
            if current_value + val > target:
                busts = True
        
        if busts:
            busting_cards_count += 1
        else:
            safe_cards_count += 1

    if total_remaining == 0:
        # Deck empty (should not happen in standard play unless 13 cards drawn, 
        # which implies we are at 13 cards in hand and haven't busted).
        return "STAY"

    prob_bust = busting_cards_count / total_remaining
    
    # --- Risk Threshold Calculation ---
    
    # We need a dynamic threshold for when to STAY based on probability of busting.
    # Factors:
    # 1. Distance to target: The closer we are, the more conservative we should be.
    # 2. Number of cards left: Fewer cards mean higher variance; we might need to be more aggressive 
    #    if we are losing, or safer if we are winning.
    
    # Heuristic: We estimate the opponent's state. 
    # We don't know their hand, but we know the global max target is 30 and min is 10.
    # A safe assumption is that the opponent will try to get close to T as well.
    # We should STAY if our score is likely higher than what the opponent can achieve 
    # or if the risk of improving is too high.
    
    # Define the risk tolerance. 
    # We use a sigmoid-like curve based on distance to target.
    # Max distance to target is roughly 30. Min is 0.
    distance_to_target = target - current_value
    
    # Base threshold: If we have > 50% chance to bust, we usually STAY, unless we are far behind.
    # If we are very far from target, we MUST hit (even with high bust risk, staying guarantees a loss 
    # if opponent reaches target).
    
    # If distance is large (e.g., > 10), we accept high risk (up to 80%).
    # If distance is small (e.g., < 5), we accept low risk (maybe 10-20%).
    
    # Adjust risk tolerance based on remaining cards
    # If few cards remain, luck plays a bigger role, so we might be more conservative 
    # if we have a "decent" score, or aggressive if we are behind.
    
    # Let's establish a baseline "safe" score. 
    # Generally, in blackjack, 17+ is considered strong.
    # Here, "strong" depends on target.
    # A "good" score is roughly target - 4 (allowing room for opponent error/bust).
    
    risk_tolerance = 0.25 # Default moderate tolerance
    
    if distance_to_target > 8:
        # We are significantly behind. Must hit.
        risk_tolerance = 0.95
    elif distance_to_target > 4:
        # Moderate distance. Moderate risk.
        risk_tolerance = 0.60
    elif distance_to_target > 2:
        # Close. Be careful.
        risk_tolerance = 0.30
    else:
        # Very close (or exactly at target, handled earlier). Be very careful.
        risk_tolerance = 0.10

    # If we are busting on half the deck, and we aren't desperate, STAY.
    if prob_bust > risk_tolerance:
        # Check if staying is actually viable.
        # If we STAY at current_value, can we win?
        # We don't know opponent's hand, but we know they have to draw from the same deck constraints.
        # If current_value is high, say > target - 2, it's a strong score.
        # If current_value is low, say < target - 10, staying is likely a loss.
        
        if distance_to_target > 5:
            # If we have to STAY but we are far behind, we are likely losing.
            # However, if prob_bust is > 0.5, hitting is statistically losing faster.
            # In a competitive arena, maximizing expected value (or minimizing loss) is key.
            # If prob_bust > 0.5, hitting reduces EV compared to staying (if staying has a non-zero win chance).
            # If we stay at 12 and target is 20, opponent likely beats us. 
            # If we hit at 12 and bust 60% of the time, we lose 60% immediately.
            # We hit if the potential gain outweighs the bust risk.
            
            # Simple heuristic: If we are losing (staying is bad), and risk is acceptable, HIT.
            # But here prob_bust is HIGH. 
            # If we are far behind, we MUST take risks.
            # If prob_bust is 0.6, we have 0.4 chance to improve. 
            # If we stay, our win chance is roughly 0.1 (opponent busts).
            # 0.4 > 0.1. We should HIT.
            pass # Logic falls through to HIT
        else:
            # We are close to target. Busting is the worst outcome.
            # Staying gives us a chance (opponent might bust or over-shoot).
            return "STAY"

    # If we reach here, we decide to HIT.
    # But we must ensure we don't bust immediately on a known bad card if we have better info.
    # Actually, the probabilistic check above covers that.
    
    # Edge case: If we are already at a score where any card (except maybe Ace) busts us,
    # and we can't use Ace as 11 (because 1 also busts).
    # This is covered by prob_bust calculation.
    
    return "HIT"

