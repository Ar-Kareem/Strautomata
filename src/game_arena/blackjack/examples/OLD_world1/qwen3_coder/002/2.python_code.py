
import random
from typing import List

def card_value(card: str) -> int:
    if card in ["J", "Q", "K"]:
        return 10
    elif card == "A":
        return 11  # We'll handle the 1 or 11 logic separately
    else:
        return int(card)

def hand_value(hand: List[str]) -> int:
    total = sum(card_value(card) for card in hand)
    # If we have aces and are over 21, convert aces from 11 to 1 one by one
    num_aces = hand.count("A")
    while total > 21 and num_aces > 0:
        total -= 10  # Convert one ace from 11 to 1
        num_aces -= 1
    return total

def expected_bust_probability(current_hand: List[str], target: int, remaining_deck: List[str]) -> float:
    current_value = hand_value(current_hand)
    if current_value > target:
        return 1.0
    if not remaining_deck:
        return 0.0 if current_value <= target else 1.0
    
    bust_count = 0
    simulations = min(1000, len(remaining_deck) * 10)  # Adjust simulations based on deck size
    
    for _ in range(simulations):
        deck_copy = remaining_deck[:]
        random.shuffle(deck_copy)
        hand_copy = current_hand[:]
        value = current_value
        
        # Draw cards until we bust, stay, or run out of cards
        for card in deck_copy:
            hand_copy.append(card)
            value = hand_value(hand_copy)
            if value > target:  # Bust
                bust_count += 1
                break
            # A simple heuristic: if we're within 2 of target, we might stay
            # But for bust probability, we'll assume we keep drawing
            # This is a simplification - in reality, our policy would dictate when to stay
    
    return bust_count / simulations

def expected_value_if_hit(current_hand: List[str], target: int, remaining_deck: List[str]) -> float:
    if not remaining_deck:
        return hand_value(current_hand)
    
    total_value = 0
    simulations = min(1000, len(remaining_deck) * 10)
    
    for _ in range(simulations):
        deck_copy = remaining_deck[:]
        random.shuffle(deck_copy)
        hand_copy = current_hand[:]
        value = hand_value(current_hand)
        
        for card in deck_copy:
            hand_copy.append(card)
            new_value = hand_value(hand_copy)
            if new_value > target:  # Bust
                total_value += 0  # Value of busting
                break
            # If we're close to target, we might stay
            # Simple heuristic: stay if within 2 points of target
            if new_value >= target - 2:
                total_value += new_value
                break
            # Otherwise keep drawing
        else:
            # If we went through the whole deck without busting or staying
            final_value = hand_value(hand_copy)
            total_value += final_value if final_value <= target else 0
    
    return total_value / simulations

def policy(hand: List[str], target: int) -> str:
    current_value = hand_value(hand)
    
    # If we've already busted, it doesn't matter, but we shouldn't hit
    if current_value > target:
        return "STAY"
    
    # If we're at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # Create a full deck
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Determine which cards are left in our deck
    hand_copy = hand[:]  # Copy our hand
    remaining_deck = full_deck[:]
    
    # Remove cards we've already drawn
    for card in hand_copy:
        if card in remaining_deck:
            remaining_deck.remove(card)
    
    # If no cards left, we must stay
    if not remaining_deck:
        return "STAY"
    
    # Simple conservative strategy based on how close we are to target
    distance_to_target = target - current_value
    
    # If we're very close to target, consider staying
    if distance_to_target <= 2:
        # Calculate bust probability if we hit
        bust_prob = expected_bust_probability(hand, target, remaining_deck)
        # If bust probability is high, stay
        if bust_prob > 0.5:
            return "STAY"
        else:
            # Compare expected value of hitting vs staying
            expected_if_hit = expected_value_if_hit(hand, target, remaining_deck)
            # If expected value when hitting is significantly better than current value, hit
            if expected_if_hit > current_value + 1:
                return "HIT"
            else:
                return "STAY"
    elif distance_to_target <= 5:
        # Moderate distance - be more cautious
        bust_prob = expected_bust_probability(hand, target, remaining_deck)
        if bust_prob > 0.3:
            return "STAY"
        else:
            return "HIT"
    else:
        # Far from target - be more aggressive
        # But still check if a single hit could bust us
        # Check the best case scenario (lowest value card)
        min_card_value = 1 if "A" in remaining_deck else min([card_value(c) for c in remaining_deck])
        if current_value + min_card_value > target:
            # Even the best card would make us bust
            return "STAY"
        return "HIT"
