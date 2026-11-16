
import numpy as np

def policy(state):
    # Map rank integers to actual ranks for readability
    rank_map = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: '10', 9: '9', 8: '8', 7: '7', 6: '6', 5: '5', 4: '4', 3: '3', 2: '2'}
    
    # Extract key state variables
    hole = state['private_cards'][0]  # Single hole card (as per problem statement)
    board = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opp_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed = state['allowed_actions']
    
    # Calculate current pot size and my stack
    current_pot = pot + my_spent + opp_spent
    my_stack = current_pot - my_spent
    
    # Hand strength evaluation
    def hand_strength():
        ranks = [card['rank'] for card in board]
        suits = [card['suit'] for card in board]
        hole_rank = hole['rank']
        
        # Check for straight potential
        def check_straight():
            ranks.append(hole_rank)
            sorted_ranks = sorted(ranks)
            for i in range(len(sorted_ranks) - 4):
                if sorted_ranks[i+4] - sorted_ranks[i] == 4:
                    return True
            return False
        
        # Check for flush potential
        def check_flush():
            return len(set(suits)) == 1
        
        # Check for pair in hole cards
        hole_pair = hole_rank in ranks
        
        # Evaluate hand strength
        if check_straight() or check_flush():
            return 8  # Straight/flush
        elif hole_pair:
            return 7  # Pair
        elif hole_rank >= 10:
            return 6  # High card
        else:
            return 5  # Low card
    
    # Calculate pot odds
    def pot_odds():
        return to_call / (pot + to_call)
    
    # Determine action based on hand strength and pot odds
    strength = hand_strength()
    odds = pot_odds()
    
    # Aggressive scaling based on hand strength
    aggression = 1.0 + (strength - 5) * 0.5
    
    # Action decision matrix
    if 'raise' in allowed:
        if strength >= 7:  # Strong hands
            return 'raise'
        elif strength == 6 and odds < 0.3:  # Premium hands with favorable odds
            return 'raise'
    if 'call' in allowed:
        if strength >= 5:  # Moderate hands
            return 'call'
        elif strength == 4 and odds < 0.4:  # Marginal hands with good odds
            return 'call'
    if 'fold' in allowed:
        if strength <= 3:  # Weak hands
            return 'fold'
    
    # Default to call if no other action available
    return 'call'
