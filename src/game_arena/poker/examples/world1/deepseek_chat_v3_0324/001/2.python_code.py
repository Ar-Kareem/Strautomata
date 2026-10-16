
import numpy as np

def policy(state: dict) -> str:
    # Calculate hand strength (0-1)
    def calculate_hand_strength():
        private_rank = state['private_cards'][0]['rank']
        base_strength = min(1.0, private_rank / 13.0)  # Normalize rank to 0-1
        
        # Adjust for potential flush/straight if public cards exist
        if state['public_cards']:
            suits = [c['suit'] for c in state['public_cards']] + [state['private_cards'][0]['suit']]
            flush_potential = max(suits.count(s) for s in set(suits)) / 5.0
            
            ranks = [c['rank'] for c in state['public_cards']] + [private_rank]
            unique_ranks = sorted(set(ranks))
            straight_potential = 0
            for i in range(len(unique_ranks)-4):
                if unique_ranks[i+4] - unique_ranks[i] <= 4:
                    straight_potential = 0.5
            
            base_strength = max(base_strength, flush_potential, straight_potential)
        
        return base_strength
    
    hand_strength = calculate_hand_strength()
    
    # Calculate pot odds
    pot_total = state['pot']
    to_call = state['to_call']
    pot_odds = to_call / (pot_total + to_call) if (pot_total + to_call) > 0 else 0
    
    # Opponent aggression factor (higher means more aggressive)
    opponent_aggression = min(1.0, state['opponent_spent'] / (state['pot'] + 1))
    
    # Decision thresholds
    fold_threshold = 0.3 - (0.1 * opponent_aggression)
    call_threshold = 0.5 - (0.1 * opponent_aggression)
    raise_threshold = 0.7 + (0.1 * (1 - opponent_aggression))
    
    # Special case: very strong hand
    if hand_strength > 0.9 and 'raise' in state['allowed_actions']:
        return 'raise'
    
    # Check if we should fold
    if (hand_strength < fold_threshold or 
        (hand_strength < 0.5 and pot_odds > 0.5)) and 'fold' in state['allowed_actions']:
        return 'fold'
    
    # Consider raising
    if (hand_strength > raise_threshold or 
        (hand_strength > 0.6 and np.random.random() < 0.3)) and 'raise' in state['allowed_actions']:
        return 'raise'
    
    # Default to call/check
    if 'call' in state['allowed_actions']:
        return 'call'
    
    # Fallback to all-in if no other options (shouldn't happen per rules)
    return 'all-in'
