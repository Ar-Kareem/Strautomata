
import numpy as np
from itertools import combinations

def policy(state: dict) -> str:
    # Constants
    private_card = state['private_cards'][0]
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']

    # Bias towards conservative play in early rounds
    num_public = len(public_cards)
    if to_call <= 0 and 'call' in allowed_actions:
        return 'call'

    # Estimate hand strength
    def hand_strength(card1, card2, card3=None, card4=None, card5=None):
        # Takes one private card and up to 5 public cards to evaluate hand strength (1 = high, 0 = very low)
        all_cards = [card1] + (public_cards if card3 is None else [card3, card4, card5])
        rank = private_card['rank']
        suit = private_card['suit']
        suits = [card['suit'] for card in all_cards]
        suits_match = suits.count(suit) >= 2

        # High card strength based on rank
        strength = rank / 14.0  # Normalize 2-Ace to 0-1
        if num_public == 3:
            # On the flop, premium cards should play aggressively
            if strength >= 0.8:  # Ace or King
                strength += 0.1
            if strength >= 0.7 and suits_match:
                strength += 0.15  # Flush draw
        elif num_public >= 4:
            # On turn/river, all public cards are out
            suits = [card['suit'] for card in all_cards]
            ranks = [card['rank'] for card in all_cards]
            for c in combinations(ranks, 2):
                if max(c) - min(c) <= 4:  # Rough straight potential
                    strength += 0.1
            if suits.count(suit) >= 4:
                strength += 0.3  # High flush potential
            if strength >= 0.9:
                strength += 0.1

        return strength

    strength = hand_strength(private_card, public_cards)

    if to_call > 0 and pot > opponent_spent:
        pot_odds = pot / to_call
        win_chance_threshold = 0.40  # If this hand has 40%+ chance to win, consider it
        if strength > win_chance_threshold:
            if 'raise' in allowed_actions:
                return 'raise'
            elif 'all-in' in allowed_actions:
                return 'all-in'
            else:
                return 'call'
        else:
            return 'fold'
    elif to_call > 0 and 'call' in allowed_actions:
        # Very low chance to win, only call if the pot is large.
        if pot > 200 or strength > 0.7:
            return 'call'
        else:
            return 'fold'
    elif 'call' in allowed_actions:
        return 'call'
    elif 'all-in' in allowed_actions and strength > 0.9:
        return 'all-in'
    elif 'raise' in allowed_actions:
        return 'raise'
    else:
        return 'call'  # Fallback in case of missing allowed_actions
