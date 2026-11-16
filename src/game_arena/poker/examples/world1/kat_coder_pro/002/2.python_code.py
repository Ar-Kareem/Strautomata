
import random
import math

def policy(state: dict) -> str:
    # Constants
    DECK_SIZE = 52
    RANKS = 13
    SUITS = 4
    
    # Extract state information
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    
    # Calculate total chips in the game (assuming 200 chips each initially)
    # This is an assumption since the initial stack is not provided in the state
    initial_stack = 200
    my_stack = initial_stack - my_spent
    opponent_stack = initial_stack - opponent_spent
    
    # Calculate pot odds
    if to_call > 0:
        pot_odds = to_call / (pot + to_call)
    else:
        pot_odds = 0
    
    # Calculate hand strength
    hand_strength = evaluate_hand_strength(private_cards, public_cards)
    
    # Determine action based on hand strength and pot odds
    if 'fold' in allowed_actions and hand_strength < 0.3:
        return 'fold'
    
    if hand_strength > 0.8:
        # Strong hand: raise or all-in
        if 'all-in' in allowed_actions:
            return 'all-in'
        elif 'raise' in allowed_actions:
            return 'raise'
        else:
            return 'call'
    elif hand_strength > 0.5:
        # Medium hand: call or raise
        if 'raise' in allowed_actions:
            return 'raise'
        else:
            return 'call'
    else:
        # Weak hand: fold or call
        if 'fold' in allowed_actions:
            return 'fold'
        else:
            return 'call'

def evaluate_hand_strength(private_cards, public_cards):
    """
    Evaluate the strength of the hand based on the private cards and public cards.
    Returns a value between 0 and 1, where 1 is the strongest hand.
    """
    # This is a simplified hand evaluation
    # In a real implementation, you would use a more sophisticated algorithm
    
    # Count the number of high cards (10, J, Q, K, A)
    high_cards = 0
    for card in private_cards + public_cards:
        if card['rank'] >= 9:  # 9 is 10, 10 is J, 11 is Q, 12 is K, 13 is A
            high_cards += 1
    
    # Calculate the probability of having a high card
    hand_strength = high_cards / (len(private_cards) + len(public_cards))
    
    # Add a random factor to make the policy less predictable
    random_factor = random.uniform(0.9, 1.1)
    hand_strength *= random_factor
    
    # Ensure the hand strength is between 0 and 1
    hand_strength = max(0, min(1, hand_strength))
    
    return hand_strength
