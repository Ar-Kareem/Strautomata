
import random
from itertools import combinations

def policy(state: dict) -> str:
    # Extract state information
    my_card = state['private_cards'][0]
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    
    # Calculate effective stack size
    effective_stack = min(100 - my_spent, 100 - opponent_spent)
    
    # Calculate pot odds
    if to_call > 0:
        pot_odds = to_call / (pot + to_call)
    else:
        pot_odds = 0
    
    # Determine hand strength
    hand_strength = evaluate_hand_strength(my_card, public_cards)
    
    # Calculate equity (simplified)
    equity = calculate_equity(my_card, public_cards)
    
    # Determine action based on game state and hand strength
    if len(public_cards) == 0:  # Preflop
        action = preflop_strategy(my_card, equity, pot_odds, effective_stack, allowed_actions)
    else:  # Postflop
        action = postflop_strategy(my_card, public_cards, equity, pot_odds, effective_stack, allowed_actions)
    
    # Ensure the action is legal
    if action not in allowed_actions:
        # If our preferred action is not allowed, choose the next best legal action
        if action == 'raise' and 'call' in allowed_actions:
            action = 'call'
        elif action in ['fold', 'call'] and 'raise' in allowed_actions:
            action = 'raise'
        elif action == 'all-in' and 'raise' in allowed_actions:
            action = 'raise'
    
    return action

def evaluate_hand_strength(my_card, public_cards):
    """Evaluate the strength of the current hand."""
    if not public_cards:
        # Preflop hand strength based on card rank
        return my_card['rank'] / 13.0
    
    # Count potential pairs
    pairs = 0
    for card in public_cards:
        if card['rank'] == my_card['rank']:
            pairs += 1
    
    # Count potential flush draws
    flush_suits = {}
    for card in [my_card] + public_cards:
        suit = card['suit']
        if suit in flush_suits:
            flush_suits[suit] += 1
        else:
            flush_suits[suit] = 1
    
    max_flush = max(flush_suits.values()) if flush_suits else 0
    
    # Count potential straight draws
    ranks = sorted([c['rank'] for c in [my_card] + public_cards])
    straight_draws = 0
    for i in range(len(ranks) - 1):
        if ranks[i+1] - ranks[i] <= 2:
            straight_draws += 1
    
    # Combine factors
    strength = pairs * 0.3 + (max_flush / 5.0) * 0.3 + (straight_draws / 4.0) * 0.2 + (my_card['rank'] / 13.0) * 0.2
    
    return min(strength, 1.0)

def calculate_equity(my_card, public_cards):
    """Calculate the equity of the hand."""
    if not public_cards:
        # Preflop equity approximation
        return my_card['rank'] / 13.0
    
    # Simplified equity calculation based on hand strength
    return evaluate_hand_strength(my_card, public_cards)

def preflop_strategy(my_card, equity, pot_odds, effective_stack, allowed_actions):
    """Determine preflop action."""
    # High card threshold for raising
    if equity > 0.7 and 'raise' in allowed_actions:
        return 'raise'
    elif equity > 0.5 and 'raise' in allowed_actions:
        return 'raise'
    elif equity > 0.3:
        return 'call'
    else:
        return 'fold'

def postflop_strategy(my_card, public_cards, equity, pot_odds, effective_stack, allowed_actions):
    """Determine postflop action."""
    # If we have a strong hand (equity > 0.7), be aggressive
    if equity > 0.7:
        if 'raise' in allowed_actions and effective_stack > pot:
            return 'raise'
        else:
            return 'call'
    # If we have a decent hand (equity > 0.5), be moderately aggressive
    elif equity > 0.5:
        if 'raise' in allowed_actions and effective_stack > pot * 2:
            return 'raise'
        elif pot_odds < equity:
            return 'call'
        else:
            return 'fold'
    # If we have a weak hand, be cautious
    else:
        if pot_odds < equity and equity > 0.3:
            return 'call'
        else:
            return 'fold'
