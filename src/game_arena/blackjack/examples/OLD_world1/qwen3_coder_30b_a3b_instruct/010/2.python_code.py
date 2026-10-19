
import random
from collections import Counter

def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value
    def hand_value(hand):
        value = 0
        aces = 0
        for card in hand:
            if card == "A":
                aces += 1
                value += 11
            elif card in ["J", "Q", "K"]:
                value += 10
            else:
                value += int(card)
        
        # Adjust aces from 11 to 1 if needed
        while value > target and aces > 0:
            value -= 10
            aces -= 1
            
        return value
    
    current_value = hand_value(hand)
    
    # If we already busted, we must stay (though this shouldn't happen in practice)
    if current_value > target:
        return "STAY"
    
    # If we're at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're very close to target, stay
    if current_value >= target - 3:
        return "STAY"
    
    # If we're far from target and have high-value cards, consider staying
    if len(hand) >= 3 and current_value < target - 10:
        # Count how many cards would be bad to draw (i.e., would make us bust)
        bust_cards = 0
        for card in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]:
            if card == "A":
                test_hand = hand + ["A"]
                test_value = hand_value(test_hand)
                if test_value > target:
                    bust_cards += 1
            else:
                test_hand = hand + [card]
                test_value = hand_value(test_hand)
                if test_value > target:
                    bust_cards += 1
        
        # If most cards would bust us, stay
        if bust_cards > 7:
            return "STAY"
    
    # Basic heuristics for decision making
    # If we have a low value and few cards, take a risk
    if current_value < 12 and len(hand) < 3:
        return "HIT"
    
    # If we have a few cards but have a decent value, be more conservative
    if len(hand) >= 3:
        # If we're still quite far from target, keep hitting
        if current_value < target - 5:
            return "HIT"
        elif current_value < target - 2:
            # 50/50 chance to hit when reasonably close to target
            return "HIT" if random.random() < 0.5 else "STAY"
        else:
            return "STAY"
    
    # Default strategy: hit unless we're fairly close to target
    if current_value < target - 3:
        return "HIT"
    elif current_value < target - 1:
        return "HIT" if random.random() < 0.3 else "STAY"
    else:
        return "STAY"
