
import random

def evaluate_hand(cards):
    """Evaluate the strength of a hand (list of cards) and return a score."""
    if not cards:
        return 0

    ranks = [card['rank'] for card in cards]
    suits = [card['suit'] for card in cards]

    # Check for pairs, three of a kind, etc.
    rank_counts = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    # Check for flush (all cards of the same suit)
    is_flush = len(set(suits)) == 1

    # Check for straight (5 consecutive ranks)
    unique_ranks = sorted(list(set(ranks)))
    is_straight = len(unique_ranks) >= 5 and (unique_ranks[-1] - unique_ranks[0] == 4)

    # Calculate hand strength score
    score = 0
    if is_straight and is_flush:
        score = 8  # Straight flush
    elif len(rank_counts) == 2 and 4 in rank_counts.values():
        score = 7  # Four of a kind
    elif len(rank_counts) == 2 and 3 in rank_counts.values() and 2 in rank_counts.values():
        score = 6  # Full house
    elif is_flush:
        score = 5  # Flush
    elif is_straight:
        score = 4  # Straight
    elif len(rank_counts) == 3 and 3 in rank_counts.values():
        score = 3  # Three of a kind
    elif len(rank_counts) == 3 and list(rank_counts.values()).count(2) == 2:
        score = 2  # Two pair
    elif len(rank_counts) == 4 and 2 in rank_counts.values():
        score = 1  # One pair
    else:
        score = 0  # High card

    return score

def policy(state):
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']

    # Combine private and public cards to evaluate hand strength
    all_cards = private_cards + public_cards
    hand_strength = evaluate_hand(all_cards)

    # Calculate pot odds
    pot_odds = pot / (to_call + 1e-6) if to_call > 0 else float('inf')

    # Decide action based on hand strength and pot odds
    if 'all-in' in allowed_actions and hand_strength >= 6 and random.random() < 0.7:
        return 'all-in'
    elif 'raise' in allowed_actions and hand_strength >= 4 and pot_odds > 2:
        return 'raise'
    elif 'call' in allowed_actions and (hand_strength >= 2 or pot_odds > 3):
        return 'call'
    elif 'fold' in allowed_actions:
        return 'fold'
    else:
        # Fallback to call if no other actions are available
        return 'call'
