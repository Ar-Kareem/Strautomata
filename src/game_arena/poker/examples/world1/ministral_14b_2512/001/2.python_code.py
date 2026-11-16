
import math

def policy(state: dict) -> str:
    # Extract state information
    private_card = state['private_cards'][0]
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    my_stack = my_spent + (pot - my_spent - opponent_spent)  # Approximate remaining stack (not directly given)

    # Helper function to evaluate hand strength (simplified for 1 card)
    def evaluate_hand_strength(card, public_cards):
        rank = card['rank']
        suit = card['suit']
        strength = 0

        # High card strength (Ace high, then K, Q, etc.)
        strength += rank * 2

        # Suited cards have potential for flushes
        if len(public_cards) > 0:
            public_suits = {c['suit'] for c in public_cards}
            if suit in public_suits:
                strength += 5  # Bonus for suited to board

        # Potential for straight draws (simplified)
        if len(public_cards) >= 3:
            public_ranks = sorted([c['rank'] for c in public_cards])
            for i in range(len(public_ranks) - 2):
                if (public_ranks[i+1] - public_ranks[i] == 1 and
                    public_ranks[i+2] - public_ranks[i+1] == 1):
                    if (rank == public_ranks[i] - 1 or rank == public_ranks[i+2] + 1):
                        strength += 10  # Potential straight draw

        return strength

    hand_strength = evaluate_hand_strength(private_card, public_cards)

    # Pot odds calculation (probability needed to call is to_call / (pot + to_call))
    pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0
    implied_odds = 0.2  # Assume we win 20% of the time with this hand (simplified)

    # Decide action based on hand strength, pot odds, and stack size
    if 'fold' in allowed_actions:
        # Fold weak hands unless pot odds are very favorable
        if hand_strength < 10 and pot_odds > 0.3:
            return 'call'
        elif hand_strength < 5:
            return 'fold'

    if 'call' in allowed_actions:
        # Call if pot odds justify it (simplified)
        if pot_odds < implied_odds and hand_strength > 5:
            return 'call'

    if 'raise' in allowed_actions:
        # Raise with strong hands or if opponent shows weakness (small bet)
        if hand_strength > 15 or (opponent_spent < 10 and hand_strength > 10):
            return 'raise'

    if 'all-in' in allowed_actions:
        # Go all-in with very strong hands or if stack is small
        if hand_strength > 20 or (my_stack < 20 and hand_strength > 15):
            return 'all-in'

    # Default to call if no other action is clearly better
    if 'call' in allowed_actions:
        return 'call'

    # Fallback (should not happen per problem constraints)
    return 'call'
