
import random
import numpy as np

def evaluate_hand_strength(private_card, public_cards):
    """Evaluate hand strength based on private card and public cards."""
    if not public_cards:
        # Pre-flop evaluation - only considering card rank
        rank = private_card['rank']
        if rank >= 12:  # Ace or King
            return 0.9
        elif rank >= 10:  # Queen or Jack
            return 0.7
        elif rank >= 8:  # 10 or 9
            return 0.5
        else:
            return 0.3
    else:
        # Post-flop evaluation - consider potential pairs, straights, flushes
        ranks = [c['rank'] for c in public_cards] + [private_card['rank']]
        suits = [c['suit'] for c in public_cards] + [private_card['suit']]
        
        # Count pairs and higher combinations
        unique_ranks = len(set(ranks))
        pair_strength = (len(ranks) - unique_ranks) / 2.0
        
        # Check for flush potential
        suit_counts = {}
        for s in suits:
            suit_counts[s] = suit_counts.get(s, 0) + 1
        max_suit = max(suit_counts.values())
        flush_potential = max_suit / (len(public_cards) + 1)
        
        # Check for straight potential
        sorted_ranks = sorted(ranks)
        straight_potential = 0
        for i in range(len(sorted_ranks) - 1):
            if sorted_ranks[i+1] - sorted_ranks[i] == 1:
                straight_potential += 0.2
        
        # Combine factors
        strength = 0.4 * pair_strength + 0.3 * flush_potential + 0.3 * straight_potential
        return min(max(strength, 0.1), 0.95)

def calculate_pot_odds(state):
    """Calculate pot odds for calling decision."""
    to_call = state['to_call']
    pot_after_call = state['pot'] + to_call
    if to_call == 0:
        return float('inf')
    return pot_after_call / to_call

def should_bluff(state, hand_strength):
    """Determine whether to bluff based on game state and hand strength."""
    # Bluff more when opponent has invested less
    opponent_investment_ratio = state['opponent_spent'] / (state['pot'] + 0.1)
    bluff_prob = 0.2 * (1 - opponent_investment_ratio) * (1 - hand_strength)
    return random.random() < bluff_prob

def policy(state):
    # Evaluate hand strength
    private_card = state['private_cards'][0]
    public_cards = state['public_cards']
    hand_strength = evaluate_hand_strength(private_card, public_cards)
    
    # Calculate pot odds
    pot_odds = calculate_pot_odds(state)
    
    # Determine allowed actions
    allowed_actions = set(state['allowed_actions'])
    
    # Premium hands - always go all-in if possible
    if hand_strength >= 0.8 and 'all-in' in allowed_actions:
        return 'all-in'
    
    # Strong hands - raise or all-in
    if hand_strength >= 0.6:
        if 'raise' in allowed_actions and random.random() < 0.7:
            return 'raise'
        elif 'all-in' in allowed_actions and random.random() < 0.5:
            return 'all-in'
        else:
            return 'call'
    
    # Marginal hands - consider pot odds and bluff
    if hand_strength >= 0.4:
        # If pot odds are good, call
        if pot_odds >= 3 and 'call' in allowed_actions:
            return 'call'
        # Consider bluffing
        if should_bluff(state, hand_strength):
            if 'raise' in allowed_actions and random.random() < 0.4:
                return 'raise'
            elif 'all-in' in allowed_actions and random.random() < 0.2:
                return 'all-in'
        # Otherwise call if pot odds are reasonable
        if pot_odds >= 2 and 'call' in allowed_actions:
            return 'call'
    
    # Weak hands - fold unless pot odds are excellent or we can check
    if state['to_call'] == 0 and 'call' in allowed_actions:
        return 'call'  # free check
    if pot_odds >= 4 and 'call' in allowed_actions:
        return 'call'
    if 'fold' in allowed_actions:
        return 'fold'
    
    # Default fallback - call if possible
    if 'call' in allowed_actions:
        return 'call'
    
    # If all else fails, return first available action
    return state['allowed_actions'][0]
