
import random

def evaluate_hand_strength(my_card, board_cards):
    """
    Computes a heuristic strength score for the player's hand given one private card and board.
    Score is between 0 (worst) and 1 (best).
    """
    if len(board_cards) == 0:
        # Preflop — only one card, so base on rank and suit (for flush potential)
        rank = my_card['rank']
        # Scale: 2=0, ..., Ace=12; normalize to [0,1]
        rank_score = (rank - 2) / 12.0
        # Slight bonus for suited potential (not powerful alone)
        return rank_score * 0.7 + random.random() * 0.05  # slight randomness to avoid predictability

    all_cards = [my_card] + board_cards
    ranks = sorted([c['rank'] for c in all_cards])
    suits = [c['suit'] for c in all_cards]

    # Count rank and suit frequencies
    rank_count = {}
    suit_count = {}
    for r in ranks:
        rank_count[r] = rank_count.get(r, 0) + 1
    for s in suits:
        suit_count[s] = suit_count.get(s, 0) + 1

    # Check for flush
    max_suit = max(suit_count.values())
    has_flush = max_suit >= 5

    # Check for straight
    unique_ranks = sorted(set(ranks))
    straight_high = 0
    seq = 1
    for i in range(1, len(unique_ranks)):
        if unique_ranks[i] == unique_ranks[i-1] + 1:
            seq += 1
            if seq >= 5:
                straight_high = unique_ranks[i]
        else:
            seq = 1

    has_straight = straight_high > 0

    # Check pairs and stronger
    max_rank_count = max(rank_count.values())
    has_pair = max_rank_count >= 2
    has_two_pair = sum(1 for v in rank_count.values() if v >= 2) >= 2
    has_trips = max_rank_count >= 3
    has_full_house = has_trips and sum(1 for v in rank_count.values() if v >= 2) >= 2
    has_quads = max_rank_count >= 4

    # Determine hand category value
    if has_quads:
        hand_value = 8
    elif has_full_house:
        hand_value = 7
    elif has_flush and has_straight:
        hand_value = 8  # straight flush — use higher of two
    elif has_flush:
        hand_value = 5
    elif has_straight:
        hand_value = 4
    elif has_trips:
        hand_value = 3
    elif has_two_pair:
        hand_value = 2
    elif has_pair:
        hand_value = 1
    else:
        # High card: use highest card not on board, if my card is high
        my_rank = my_card['rank']
        board_ranks = [c['rank'] for c in board_cards]
        if my_rank == max(ranks):  # my card is the high card
            hand_value = (my_rank - 2) / 12.0 * 0.9  # scaled
        else:
            hand_value = 0.1  # weak high card

    # Normalize hand_value to [0,1]
    if hand_value >= 2:  # made hand
        score = 0.5 + (hand_value - 2) * 0.1
    else:
        score = hand_value * 0.4

    # Add draw potential
    draw_bonus = 0.0
    if max_suit == 4:  # 4 to a flush
        draw_bonus = 0.2
    if not has_straight and not has_flush:
        # Check for open-ended straight draw
        gap_seq = 0
        potential = set()
        for r in unique_ranks:
            potential.add(r - 1)
            potential.add(r + 1)
        for p in potential:
            if p < 2 or p > 14:
                continue
            extended = unique_ranks + [p]
            extended = sorted(set(extended))
            seq = 1
            for i in range(1, len(extended)):
                if extended[i] == extended[i-1] + 1:
                    seq += 1
                    if seq == 4:  # one more card makes straight
                        draw_bonus = max(draw_bonus, 0.15)
                else:
                    seq = 1
    score += draw_bonus

    # Cap score
    score = min(score, 0.95)
    return score

def policy(state: dict) -> str:
    # Extract state
    my_card = state['private_cards'][0]
    board = state['public_cards']
    to_call = state['to_call']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    allowed = state['allowed_actions']

    # Calculate effective stack (assuming 1000 starting stack)
    starting_stack = 1000
    my_bet = my_spent
    opponent_bet = opponent_spent
    my_stack = starting_stack - my_bet
    opponent_stack = starting_stack - opponent_bet
    total_pot = pot

    # Estimate hand strength
    strength = evaluate_hand_strength(my_card, board)

    # Determine round
    round_name = "preflop"
    if len(board) == 3:
        round_name = "flop"
    elif len(board) == 4:
        round_name = "turn"
    elif len(board) == 5:
        round_name = "river"

    # Pot odds: what fraction of pot do I need to call?
    if to_call == 0:
        pot_odds = 0
    elif to_call + pot > 0:
        pot_odds = to_call / (pot + to_call)
    else:
        pot_odds = 0

    # Thresholds for action
    call_threshold = pot_odds * 0.7  # Be willing to call if strength > scaled pot odds
    raise_threshold = 0.4  # Minimum strength to consider raising
    all_in_threshold = 0.7  # Strong hand

    # Decision logic
    if 'fold' not in allowed and 'call' in allowed:
        # Must call or all-in (opponent raised)
        if strength > pot_odds * 1.5:  # Looser calling standards with draws
            if 'raise' in allowed and strength > raise_threshold and random.random() < 0.8:
                return 'raise'
            elif strength > all_in_threshold and my_stack < opponent_stack * 1.5:
                return 'all-in'
            else:
                return 'call'
        else:
            # Should fold, but cannot, so call as bluff or hope
            return 'call'

    # Normal decision point: can fold, call, raise, etc.
    if to_call == 0:
        # Checking opportunity
        if strength > raise_threshold and 'raise' in allowed and random.random() < 0.7:
            return 'raise'
        else:
            return 'call'  # check

    # Facing a bet
    if strength < call_threshold:
        # Not getting good odds, and weak hand
        if 'fold' in allowed:
            return 'fold'
        else:
            return 'call'

    if strength > pot_odds + 0.3 or (strength > 0.6 and 'raise' in allowed):
        # Strong hand or great implied odds
        if strength > all_in_threshold and my_stack <= 200:
            return 'all-in'
        elif 'raise' in allowed and random.random() < 0.8:
            return 'raise'
        else:
            return 'call'

    # Default: call if can't raise
    if 'call' in allowed:
        return 'call'
    elif 'fold' in allowed:
        return 'fold'
    else:
        return 'all-in'  # last resort
