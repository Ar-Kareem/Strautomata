
def policy(hand: list[str], target: int) -> str:
    # Calculate the current hand value
    def get_hand_value(hand):
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
    
    current_value = get_hand_value(hand)
    
    # If we already busted, we have to stay
    if current_value > target:
        return "STAY"
    
    # If we're at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're far from target, take risks
    if current_value <= target - 10:
        return "HIT"
    
    # If target is low (10-15), be more aggressive
    if target <= 15:
        if current_value <= 10:
            return "HIT"
        elif current_value <= 15:
            # 50% chance to hit
            import random
            return "HIT" if random.random() < 0.5 else "STAY"
        else:
            return "STAY"
    
    # If target is moderate (16-20), be conservative
    if target <= 20:
        if current_value <= 15:
            return "HIT"
        elif current_value <= 18:
            # 30% chance to hit
            import random
            return "HIT" if random.random() < 0.3 else "STAY"
        else:
            return "STAY"
    
    # If target is high (21-30), be even more conservative
    if target > 20:
        if current_value <= 18:
            return "HIT"
        elif current_value <= 22:
            # 20% chance to hit
            import random
            return "HIT" if random.random() < 0.2 else "STAY"
        else:
            return "STAY"
    
    # Fallback - always take a risk when we're far from target
    return "HIT"
