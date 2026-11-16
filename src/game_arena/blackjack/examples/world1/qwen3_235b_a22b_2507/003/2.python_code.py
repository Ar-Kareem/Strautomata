
import numpy as np

def policy(hand: list[str], target: int) -> str:
    # Map card to its value. A can be 11 or 1.
    def card_value(c, hand_total_without_c):
        if c in ["J", "Q", "K"]:
            return 10
        elif c == "A":
            # Ace is 11 if it doesn't bust, otherwise 1
            if hand_total_without_c + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(c)
    
    # Compute current hand value with optimal Aces
    def hand_value(hand):
        # Count aces separately
        non_ace_sum = 0
        ace_count = 0
        for c in hand:
            if c == "A":
                ace_count += 1
            else:
                non_ace_sum += card_value(c, 0)  # safe to use card_value for non-A
        # Now add Aces optimally
        total = non_ace_sum
        for _ in range(ace_count):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        return total
    
    current_sum = hand_value(hand)
    
    # If we're already at or above target, stay (avoid further risk)
    if current_sum >= target:
        return "STAY"
    
    # All possible cards in the deck
    deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Determine which cards have not been used (in hand)
    # Since we draw without replacement from our own 13-card deck
    remaining_cards = [c for c in deck if c not in hand]
    
    # If no cards left, must stay
    if not remaining_cards:
        return "STAY"
    
    # Compute value of each remaining card if added
    def value_of(card):
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Ace value depends on new total
            if current_sum + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    # Count how many remaining cards would *not* cause a bust
    safe_cards = 0
    for card in remaining_cards:
        val = value_of(card)
        if current_sum + val <= target:
            safe_cards += 1
    
    proportion_safe = safe_cards / len(remaining_cards)
    
    gap = target - current_sum
    
    # If we're very close to target, and not much to gain, stay
    if gap <= 2:
        # Even a 1 might bust with Ace as 1, so only hit if safe
        # But improvement is small. Prefer to stay if any risk
        if proportion_safe < 0.7:
            return "STAY"
        else:
            # Small chance, but we might close the gap
            return "HIT"
    
    # If we're moderately close and risk is high, stay
    if gap <= 5:
        if proportion_safe < 0.5:
            return "STAY"
    
    # If we are far from target, hit unless most cards are dangerous
    if gap > 5:
        if proportion_safe < 0.3:
            # Even though far, too risky
            return "STAY"
        else:
            return "HIT"
    
    # Default cautious strategy: if proportion of safe cards is too low, stay
    if proportion_safe < 0.4:
        return "STAY"
    
    # Otherwise, hit to get closer
    return "HIT"
