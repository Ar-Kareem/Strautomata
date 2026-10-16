
import numpy as np

def evaluate_hand(private_cards, public_cards):
    # Combine private and public cards
    all_cards = private_cards + public_cards
    ranks = [card['rank'] for card in all_cards]
    suits = [card['suit'] for card in all_cards]

    # Check for pairs, flushes, straights, etc.
    rank_counts = np.bincount(ranks, minlength=14)
    suit_counts = np.bincount(suits, minlength=4)

    # Check for flush
    flush = np.max(suit_counts) >= 5

    # Check for straight
    unique_ranks = sorted(set(ranks))
    straight = False
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i+4] - unique_ranks[i] == 4:
            straight = True
            break

    # Check for pairs, three of a kind, etc.
    pairs = np.sum(rank_counts == 2)
    three_of_a_kind = np.sum(rank_counts == 3)
    four_of_a_kind = np.sum(rank_counts == 4)

    # Evaluate hand strength (simplified)
    hand_strength = 0
    if flush and straight:
        hand_strength = 8  # Straight flush
    elif four_of_a_kind:
        hand_strength = 7
    elif three_of_a_kind and pairs >= 1:
        hand_strength = 6  # Full house
    elif flush:
        hand_strength = 5
    elif straight:
        hand_strength = 4
    elif three_of_a_kind:
        hand_strength = 3
    elif pairs == 2:
        hand_strength = 2
    elif pairs == 1:
        hand_strength = 1
    else:
        hand_strength = 0  # High card

    return hand_strength

def policy(state):
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']

    hand_strength = evaluate_hand(private_cards, public_cards)

    # First round: cannot fold
    if 'fold' not in allowed_actions:
        allowed_actions.remove('fold')

    # Decide action based on hand strength and pot odds
    if hand_strength >= 6:  # Very strong hand
        if 'raise' in allowed_actions:
            return 'raise'
        elif 'all-in' in allowed_actions:
            return 'all-in'
        else:
            return 'call'
    elif hand_strength >= 3:  # Moderate hand
        if to_call == 0:
            return 'call'
        elif to_call / pot < 0.3:  # Good pot odds
            return 'call'
        else:
            return 'fold'
    else:  # Weak hand
        if to_call == 0:
            return 'call'
        else:
            return 'fold'
