
import random

def evaluate_hand(private_cards, public_cards):
    """Evaluate hand strength based on current cards"""
    all_cards = private_cards + public_cards
    if not all_cards:
        return 0

    # For one-card hands, just use the rank
    if len(all_cards) == 1:
        return all_cards[0]['rank']

    # For multiple cards, simple evaluation
    ranks = [card['rank'] for card in all_cards]
    max_rank = max(ranks)

    # Check for pairs
    if len(ranks) > 1 and len(set(ranks)) < len(ranks):
        return max_rank * 2  # Pair is worth more

    # High card evaluation
    return max_rank + (sum(sorted(ranks, reverse=True)[:2]) * 0.1)

def policy(state):
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    to_call = state['to_call']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    allowed_actions = state['allowed_actions']

    hand_strength = evaluate_hand(private_cards, public_cards)
    pot_odds = pot / (to_call + 1e-6) if to_call > 0 else float('inf')

    # Never fold on first round (when both have 100 chips)
    if 'fold' in allowed_actions and (my_spent > 0 or opponent_spent > 0):
        # Consider folding very weak hands
        if hand_strength < 5 and to_call > pot * 0.3:
            return 'fold'

    # Check if we can raise
    if 'raise' in allowed_actions:
        # Strong hands - raise
        if hand_strength > 10 or (hand_strength > 7 and pot_odds > 3):
            return 'raise'

        # Occasional bluff (10% chance) with weak hands when pot is small
        if hand_strength < 4 and pot < 200 and random.random() < 0.1:
            return 'raise'

    # Check if we should go all-in
    if 'all-in' in allowed_actions:
        # Very strong hands or good pot odds
        if hand_strength > 12 or (hand_strength > 8 and pot_odds > 5):
            return 'all-in'

    # Default to call/check
    if 'call' in allowed_actions:
        return 'call'

    # Fallback (shouldn't reach here as per problem statement)
    return allowed_actions[0]
