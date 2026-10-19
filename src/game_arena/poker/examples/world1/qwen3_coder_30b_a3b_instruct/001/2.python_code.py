
import random

def policy(state):
    # Extract all relevant information from the state
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    
    # Simple hand strength evaluation based on single private card
    # For a single card, we'll use rank as a proxy for strength
    my_rank = private_cards[0]['rank']
    
    # Calculate pot odds
    pot_odds = to_call / (pot + to_call) if pot + to_call > 0 else 0
    
    # Determine hand strength (simplified)
    hand_strength = 0.0
    
    # Evaluate potential based on rank
    if my_rank >= 10:  # High cards (10+)
        hand_strength = 0.8
    elif my_rank >= 7:  # Medium-high cards
        hand_strength = 0.5
    elif my_rank >= 4:  # Medium cards
        hand_strength = 0.3
    else:  # Low cards
        hand_strength = 0.1
    
    # If we have no public cards, potential is lower
    if len(public_cards) == 0:
        hand_strength *= 0.5
        
    # Add a small boost for higher ranks even without public cards
    if len(public_cards) == 0 and my_rank >= 8:
        hand_strength = min(1.0, hand_strength + 0.3)
    
    # Adjust for board cards (if any)
    if len(public_cards) > 0:
        # Assume some draw possibilities or stronger combinations
        board_ranks = [card['rank'] for card in public_cards]
        if len(set(board_ranks)) == len(board_ranks):
            # All different ranks (less likely to form strong hands)
            hand_strength = min(1.0, hand_strength + 0.15)
        else:
            # Some duplicates (better odds for combinations)
            hand_strength = min(1.0, hand_strength + 0.25)
    
    # Consider pot odds
    # If pot odds are very favorable, more likely to call/raise
    if pot_odds < 0.25 and hand_strength > 0.5:  # Pot odds < 25% and strong hand
        pot_factor = 1.5
    elif pot_odds < 0.4 and hand_strength > 0.3:  # Pot odds < 40% and medium hand
        pot_factor = 1.2
    else:
        pot_factor = 1.0
    
    # Calculate adjusted strength
    adjusted_strength = hand_strength * pot_factor
    
    # Basic action selection logic
    if 'fold' in allowed_actions and to_call > 0:
        # If opponent bet is too high relative to our hand and we have no good reason to call
        if to_call > pot / 3 and adjusted_strength < 0.3:
            return 'fold'
        
        # If our pot odds are bad and we're in a weak position
        if pot_odds > 0.5 and adjusted_strength < 0.4:
            # But not the first round in a game where both play 100 chips
            if pot < 200:  # First round scenario
                pass  # Allow playing through it
            elif random.random() < 0.6:  # 60% chance to fold when weak hand and bad pot odds
                return 'fold'
    
    # If we can raise and have good strength and pot odds
    if 'raise' in allowed_actions and adjusted_strength >= 0.5:
        # Also consider raising even with moderate strength if we think we can get value
        if random.random() < adjusted_strength:  # Raise with increasing likelihood as strength increases
            return 'raise'
    
    # If we have a strong hand or good pot odds, consider all-in when possible
    if 'all-in' in allowed_actions and adjusted_strength >= 0.7:
        return 'all-in'
    
    # If we can check or call, check if strong enough to raise or call
    if to_call == 0:
        # If we have a decent hand or good draw, check and be ready to raise
        if adjusted_strength >= 0.4:
            return 'call'  # Actually "check" in this case since to_call is 0
        else:
            return 'call'  # Still check to see more board cards
    
    # If opponent bet is manageable and our hand strength is decent
    if to_call <= pot / 4 and adjusted_strength >= 0.3:
        return 'call'
    
    # If we have a good reason to bluff or are on a draw
    if to_call < pot / 2:
        # Random bluffing factor if we have a chance (we don't have enough card info for true draws)
        bluff_chance = adjusted_strength * 0.25 + (0.3 if len(public_cards) == 0 else 0.1)
        if random.random() < bluff_chance and 'raise' in allowed_actions:
            return 'raise'
    
    # Default to call when nothing else is appropriate
    if 'call' in allowed_actions and to_call > 0:
        # We might want to call if pot odds are somewhat favorable
        if pot_odds <= 0.4 or adjusted_strength > 0.3:
            return 'call'
    
    # If we can only fold, fold
    if 'fold' in allowed_actions:
        return 'fold'
        
    # Fallback if we have no better option
    return 'call'
