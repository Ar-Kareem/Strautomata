
import random

def policy(state: dict) -> str:
    """
    Smart policy for 1-card Poker.
    Evaluates hand strength based on rank and pot odds.
    """
    # Basic data extraction
    my_card = state['private_cards'][0]
    rank = my_card['rank']  # Usually 2-14 (where 14 is Ace)
    to_call = state['to_call']
    pot = state['pot']
    allowed = state['allowed_actions']
    
    # Calculate relative hand strength (1-card context)
    # Rank 14 = Ace, 13 = King, etc.
    is_high_tier = rank >= 12
    is_mid_tier = rank >= 8
    
    # Calculate Pot Odds: if to_call is small relative to pot, we are more likely to stay in
    pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0
    
    # 1. High Tier Strategy (Aces, Kings, Queens)
    if is_high_tier:
        if 'raise' in allowed:
            # If we have a very strong hand, we want to build the pot
            return 'raise'
        elif 'all-in' in allowed and rank == 14:
            return 'all-in'
        return 'call'

    # 2. Mid Tier Strategy (8s through Jacks)
    if is_mid_tier:
        if to_call == 0:
            # Check/Call
            return 'call'
        elif pot_odds < 0.4:
            # If it's not too expensive, stay in
            return 'call'
        else:
            # Over-aggressive opponent, might be a bluff or they have a high-tier
            return 'fold' if 'fold' in allowed else 'call'

    # 3. Low Tier Strategy (Below 8)
    if to_call == 0:
        return 'call' # Always check if free
    
    # Fold if it costs more than a small fraction of the pot
    if pot_odds > 0.2:
        if 'fold' in allowed:
            return 'fold'
        return 'call'
    
    # Fallback to call if it's very cheap
    if 'call' in allowed:
        return 'call'
        
    # Final emergency fallback: return the first allowed action
    return allowed[0]
