
import random
import math

def get_hand_strength(state):
    """Evaluate the strength of our hand"""
    private_card = state['private_cards'][0]
    public_cards = state['public_cards']
    
    # Base strength from private card rank (Ace=14, King=13, etc.)
    base_strength = private_card['rank'] / 14.0
    
    # If there are community cards, check for potential pairs
    if public_cards:
        for card in public_cards:
            if card['rank'] == private_card['rank']:
                # We have a pair
                return max(0.6, base_strength + 0.2)
        
        # Check for potential flush (same suit)
        suited_cards = sum(1 for card in public_cards if card['suit'] == private_card['suit'])
        if suited_cards >= 2:
            # Good flush draw
            return max(0.4, base_strength + 0.1)
        
        # Check for potential straight
        ranks = sorted([private_card['rank']] + [card['rank'] for card in public_cards])
        gaps = sum(1 for i in range(len(ranks)-1) if ranks[i+1] - ranks[i] > 1)
        if len(ranks) >= 3 and gaps <= 1:
            # Good straight draw
            return max(0.4, base_strength + 0.1)
    
    return base_strength

def policy(state):
    # Get game state
    private_card = state['private_cards'][0]
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    pot = state['pot']
    allowed_actions = state['allowed_actions']
    
    # Calculate hand strength
    hand_strength = get_hand_strength(state)
    
    # Calculate pot odds if facing a call
    pot_odds = 0
    if to_call > 0 and pot > 0:
        pot_odds = to_call / (pot + to_call)
    
    # Determine action based on hand strength and game context
    if 'fold' in allowed_actions:
        # Never fold in the first round when both have 100 chips
        if pot == 200 and my_spent == 100 and opponent_spent == 100:
            # Check or call
            if 'call' in allowed_actions:
                return 'call'
            elif 'raise' in allowed_actions:
                # Raise with decent hand
                if hand_strength > 0.6:
                    return 'raise'
                else:
                    return 'call'
        
        # Consider folding if hand is weak and pot odds are bad
        if hand_strength < 0.3 and pot_odds > 0.4:
            return 'fold'
    
    if 'raise' in allowed_actions:
        # Aggressive play with strong hands
        if hand_strength > 0.8:
            return 'raise'
        # Semi-bluff with decent hand and good position
        elif hand_strength > 0.5 and to_call == 0:
            return 'raise'
    
    if 'all-in' in allowed_actions:
        # All-in with very strong hands or when strategically necessary
        if hand_strength > 0.9:
            return 'all-in'
        # All-in as a bluff when opponent shows weakness
        elif hand_strength > 0.4 and to_call > 0 and pot_odds < 0.2:
            return 'all-in'
    
    if 'call' in allowed_actions:
        # Call with decent hand or good pot odds
        if hand_strength > 0.4 or (to_call > 0 and pot_odds < 0.33):
            return 'call'
    
    # Default to call if available
    if 'call' in allowed_actions:
        return 'call'
    
    # If nothing else, fold (shouldn't happen if API guarantees valid actions)
    return 'fold'
