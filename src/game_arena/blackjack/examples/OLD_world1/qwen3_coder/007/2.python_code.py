
import numpy as np
from typing import List

def card_value(card: str) -> int:
    if card in ["J", "Q", "K"]:
        return 10
    elif card == "A":
        return 11
    else:
        return int(card)

def hand_value(hand: List[str]) -> int:
    total = sum(card_value(card) for card in hand)
    
    # If we're over and have aces, try to count them as 1 instead of 11
    num_aces = hand.count("A")
    while total > 0 and num_aces > 0 and total > 21:
        total -= 10
        num_aces -= 1
        
    return total

def best_action(hand: List[str], target: int, deck: List[str]) -> str:
    current_value = hand_value(hand)
    
    # If we've already busted or reached target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're very close to target, stay
    if target - current_value <= 1:
        return "STAY"
    
    # Calculate the probability of improving our hand without busting
    safe_cards = 0
    total_cards = len(deck)
    
    if total_cards == 0:
        return "STAY"
    
    for card in deck:
        new_hand = hand + [card]
        new_value = hand_value(new_hand)
        if new_value <= target:
            safe_cards += 1
    
    # If all remaining cards cause us to bust, stay
    if safe_cards == 0:
        return "STAY"
    
    # Probability of not busting with the next card
    prob_safe = safe_cards / total_cards
    
    # Expected value if we hit
    expected_value = 0
    if safe_cards > 0:
        safe_total = 0
        safe_count = 0
        for card in deck:
            new_hand = hand + [card]
            new_value = hand_value(new_hand)
            if new_value <= target:
                safe_total += new_value
                safe_count += 1
        if safe_count > 0:
            expected_value = safe_total / safe_count
    
    # If expected improvement is good, hit
    # We use a threshold that becomes more conservative as we get closer to target
    threshold = target * 0.7
    
    # If we're far from target and have a good chance of not busting, hit
    if current_value < threshold and prob_safe > 0.5:
        return "HIT"
    
    # Otherwise, if we're close to target, be more conservative
    if current_value >= threshold:
        # Stay if we're within 3 of target, or if risk of busting is high
        if target - current_value <= 3 or prob_safe < 0.4:
            return "STAY"
        else:
            return "HIT"
    
    return "HIT"

def policy(hand: List[str], target: int) -> str:
    # Create a full deck
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Remove cards that are already in our hand
    remaining_deck = full_deck[:]
    for card in hand:
        if card in remaining_deck:
            remaining_deck.remove(card)
    
    # Use our strategy function
    return best_action(hand, target, remaining_deck)
