
import numpy as np

def policy(state: dict) -> str:
    # Extract state variables
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    
    # Extract our single private card
    our_rank = private_cards[0]['rank'] if len(private_cards) > 0 else 2  # fallback
    our_suit = private_cards[0]['suit'] if len(private_cards) > 0 else 0
    
    # Calculate current betting amounts
    current_bet = opponent_spent
    my_contribution = my_spent
    pot_after_call = pot + to_call
    
    # Evaluate hand strength (0 to 1 scale)
    hand_strength = 0.0
    
    # Base strength from high card
    if our_rank >= 14:  # Ace
        hand_strength = 0.95
    elif our_rank >= 13:  # King
        hand_strength = 0.85
    elif our_rank >= 12:  # Queen
        hand_strength = 0.75
    elif our_rank >= 11:  # Jack
        hand_strength = 0.65
    elif our_rank >= 10:  # 10
        hand_strength = 0.55
    elif our_rank >= 9:   # 9
        hand_strength = 0.45
    elif our_rank >= 8:   # 8
        hand_strength = 0.35
    else:  # 2-7
        hand_strength = 0.2 + (our_rank - 2) * 0.05  # 0.2 to 0.35
    
    # Adjust for public cards (if any) - implied potential
    if len(public_cards) > 0:
        # Check for potential flush or straight draws
        # Simple adjustment: if public cards include high cards, increase strength
        public_ranks = [card['rank'] for card in public_cards]
        high_public = sum(1 for r in public_ranks if r >= 10)
        
        # If we have Ace or King and public has high cards, increase strength
        if our_rank >= 12 and high_public >= 1:
            hand_strength += 0.1
        # If our card matches a public card (pair), significantly boost strength
        if our_rank in public_ranks:
            hand_strength = min(1.0, hand_strength + 0.3)
        
        # If multiple public cards and our card is medium/high, add some draw equity
        if len(public_cards) >= 2 and our_rank >= 8:
            hand_strength += 0.05
    
    # Estimate win probability (simplified model)
    # We're playing against a random hand
    # Use hand_strength as a proxy for equity in showdown
    win_probability = hand_strength
    
    # Adjustment for the number of public cards
    # More public cards = more known info = more accurate equity
    # Less public cards = more uncertainty, we are more likely to bluff or get lucky
    if len(public_cards) == 0:
        # Pre-flop equivalent: add some bluffing multiplier
        win_probability = max(0.2, win_probability - 0.1)  # We're less confident pre-flop
    elif len(public_cards) == 1:
        win_probability = win_probability + 0.05
    elif len(public_cards) == 2:
        win_probability = win_probability + 0.1
    else:  # 3 or more public cards
        win_probability = win_probability + 0.15
    
    # Cap at 1.0
    win_probability = min(1.0, win_probability)
    
    # Calculate pot odds
    if to_call > 0:
        pot_odds = to_call / (pot_after_call + to_call)
    else:
        pot_odds = 0  # We can check
    
    # Defense against going all-in needlessly
    # Estimate opponent's range based on their commitment
    opponent_commitment_ratio = opponent_spent / (pot if pot > 0 else 1)
    is_opponent_aggressive = opponent_commitment_ratio > 0.8  # Seems like they're forcing
    is_opponent_folding = opponent_commitment_ratio < 0.3  # They've checked many times
    
    # Decision logic
    
    # Always fold if not allowed to do anything else and fold is only option
    if 'fold' in allowed_actions and len(allowed_actions) == 1:
        return 'fold'
    
    # Check if we can check (to_call == 0) and we have poor hand
    if to_call == 0:
        if hand_strength < 0.4 and len(public_cards) > 0:
            # Weak hand on flop/turn - check
            return 'call'  # This is check
        if hand_strength < 0.3:
            # Very weak hand, check
            return 'call'
        if hand_strength >= 0.7:
            # Strong hand, raise to build pot
            if 'raise' in allowed_actions:
                return 'raise'
            else:
                return 'call'
        return 'call'  # Default to check
    
    # We have to call or raise
    if win_probability > pot_odds + 0.15:  # Good equity + margin
        # Consider raising if we have strong hand
        if hand_strength >= 0.7:
            if 'raise' in allowed_actions:
                return 'raise'
            else:
                return 'call'
        elif hand_strength >= 0.5:
            # Medium hand with good odds
            if 'raise' in allowed_actions and not is_opponent_aggressive:
                # Don't raise against someone who's strongly committed (they might have better)
                return 'call'
            else:
                return 'call'
        else:
            # Weakish hand with good pot odds
            if win_probability > pot_odds:
                return 'call'
            else:
                return 'fold'
    else:
        # Pot odds are bad
        if hand_strength > 0.8:  # Very strong hand
            if 'raise' in allowed_actions:
                return 'raise'
            elif 'all-in' in allowed_actions:
                return 'all-in'
            else:
                return 'call'
        elif hand_strength > 0.6 and is_opponent_folding:
            # Bluff opportunity - opponent looks weak
            if 'raise' in allowed_actions:
                return 'raise'
            elif 'all-in' in allowed_actions:
                return 'all-in'
            else:
                return 'fold'
        else:
            # Weak hand, bad odds - fold
            return 'fold'

    # Fallback (should not reach here)
    if 'call' in allowed_actions:
        return 'call'
    elif 'fold' in allowed_actions:
        return 'fold'
    elif 'raise' in allowed_actions:
        return 'raise'
    elif 'all-in' in allowed_actions:
        return 'all-in'
    else:
        return 'fold'
