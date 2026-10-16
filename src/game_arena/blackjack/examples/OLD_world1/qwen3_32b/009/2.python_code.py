
import math

def policy(hand: list[str], target: int) -> str:
    def calculate_value(hand_val, target_val):
        total = 0
        aces = 0
        for card in hand_val:
            if card == 'A':
                total += 11
                aces += 1
            elif card in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(card)
        if total <= target_val:
            return (total, False)
        else:
            delta = total - target_val
            k = math.ceil(delta / 10)
            if k <= aces:
                adjusted = total - 10 * k
                return (adjusted, False)
            else:
                adjusted = total - 10 * aces
                if adjusted <= target_val:
                    return (adjusted, False)
                else:
                    return (0, True)
    
    current_value, is_bust = calculate_value(hand, target)
    if is_bust:
        return "STAY"
    
    full_deck = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining_cards = [card for card in full_deck if card not in hand]
    
    if not remaining_cards:
        return "STAY"
    
    total_ev = 0.0
    count = 0
    for card in remaining_cards:
        new_hand = hand + [card]
        new_value, new_bust = calculate_value(new_hand, target)
        if new_bust:
            contribution = -1.0
        else:
            contribution = float(new_value)
        total_ev += contribution
        count += 1
    
    ev_hit = total_ev / count if count else 0.0
    
    if ev_hit > current_value:
        return "HIT"
    else:
        return "STAY"
