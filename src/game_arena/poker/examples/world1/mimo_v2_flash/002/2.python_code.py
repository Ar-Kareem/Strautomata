
import random

def policy(state: dict) -> str:
    # Extract state variables
    my_card = state['private_cards'][0]
    public_cards = state['public_cards']
    pot = state['pot']
    to_call = state['to_call']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    allowed_actions = state['allowed_actions']

    # Helper to get rank and suit
    my_rank = my_card['rank']
    my_suit = my_card['suit']

    # --- 1. Helper Functions for Analysis ---
    
    def get_board_stats():
        """Analyze the board texture."""
        if not public_cards:
            return {"count": 0, "high_cards": 0, "low_cards": 0, "max_rank": 0}
        
        ranks = [c['rank'] for c in public_cards]
        max_rank = max(ranks)
        high_cards = sum(1 for r in ranks if r >= 10) # 10, J, Q, K, A
        low_cards = len(ranks) - high_cards
        return {"count": len(public_cards), "high_cards": high_cards, "low_cards": low_cards, "max_rank": max_rank}

    def get_pot_odds():
        """Calculate pot odds to call."""
        if to_call == 0:
            return 999.0 # Infinite odds
        total_to_call = to_call
        total_pot_after_call = pot + total_to_call
        if total_to_call == 0: return 999.0
        return total_pot_after_call / total_to_call

    def is_sufficient_stack_for_allin():
        """Check if stack is shallow enough to justify Nash all-in play."""
        # In this specific arena structure (100 starting, pot grows), 
        # All-in is typically allowed when stacks are low relative to pot.
        # We approximate: if to_call > 30 or my_spent > 50, we are deep in the hand.
        # However, we only use all-in if we have the raw equity or blocker advantage.
        return 'all-in' in allowed_actions

    board = get_board_stats()
    pot_odds = get_pot_odds()

    # --- 2. Hand Strength & Range Assessment ---

    # "Strength Score": A heuristic metric (0-100) estimating raw hand strength + blockers.
    # 2-7 are "Monsters" (Blockers to nothing, meaning opponent is likely weak).
    # A, K, Q, J, 10 are "Bluff Catchers/Value" (Blockers to strong hands, but vulnerable).
    strength_score = 0
    
    # Preflop Logic (No public cards)
    if board['count'] == 0:
        if my_rank <= 7:
            # Low cards are very strong heads-up (Blockers to pairs/highs).
            # We treat them as premium speculative hands.
            strength_score = 85 
        elif my_rank >= 11:
            # High cards (A, K, Q, J) are good, but prone to kicker issues.
            strength_score = 65
        elif my_rank == 10:
            strength_score = 50
        else:
            strength_score = 30
            
    # Postflop Logic
    else:
        # Are we holding a high card?
        is_high = my_rank >= 10
        
        # Does the board have high cards?
        if board['high_cards'] > 0:
            if is_high:
                # We likely block the nuts (A, K, Q on board). Good bluffing/semi-value.
                strength_score = 60 + (my_rank - 10) * 5
            else:
                # We have a low card (2-7) on a high board. We likely missed.
                # We are a total bluff catcher.
                strength_score = 10
        else:
            # Board is low (2-9).
            if is_high:
                # Overcards. We have raw high card value but no pair.
                strength_score = 40
            else:
                # We have a low card on a low board.
                # Did we hit? If we match one of the ranks, we have a pair.
                if my_rank in [c['rank'] for c in public_cards]:
                    strength_score = 95 # Pair
                else:
                    # We are drawing thin or have a high card kicker disadvantage.
                    strength_score = 35
                     
    # --- 3. Action Policy ---

    # STRATEGY: GTO / Exploitative Hybrid
    
    # Phase 1: The All-in Scenario (Commitment or Shove Spot)
    if is_sufficient_stack_for_allin():
        # If we have a hand that is "better than random" (score > 50), we want to commit.
        # In a heads-up single-card game, the equilibrium push frequency is very wide.
        # If opponent bets big (to_call is high), we call with almost any card.
        
        if strength_score > 60:
            return 'all-in' if 'all-in' in allowed_actions else 'call' # Maximize value
        elif to_call > pot * 0.4:
            # If facing a large bet, we need raw equity. 
            # Since 2-7 are strong blockers, we call with them even if we missed.
            if my_rank <= 7:
                return 'all-in' if 'all-in' in allowed_actions else 'call'
            # High cards are often just draws here, fold unless we have direct odds.
            if pot_odds > 2.5:
                 return 'call'
            else:
                 return 'fold'
        else:
            # Small bet, we can call with almost anything to see the flip.
            return 'call'

    # Phase 2: Standard Play (Non All-in)

    if to_call == 0:
        # We are first to act or opponent checked.
        
        if board['count'] == 0:
            # Preflop: 
            # - Premium (A, K, Q): Bet to build pot (Raise).
            # - Speculative (2-7): Bet to bluff/steal (Raise).
            # - Junk (8, 9, 10): Check (Call) or small bet.
            
            if my_rank <= 7 or my_rank >= 13:
                return 'raise' # Bluff (Low cards) or Value (A, K)
            else:
                return 'call' # Check / Call (Keep pot small)
        
        else:
            # Postflop:
            # - Strong equity (Pair, Strong Draw, Blocker to Nuts): Bet (Raise).
            # - Weak/Missed: Check (Call).
            
            if strength_score > 70:
                return 'raise'
            elif strength_score > 40:
                return 'call'
            else:
                return 'call' # Defensive check-call
    
    else:
        # Facing a bet (to_call > 0)
        
        # 1. The "Bluff Catcher" Rule:
        # If opponent bets huge (> 70% pot), they are polarized.
        # We need strength to call.
        
        if to_call > pot * 0.6:
            if strength_score > 55:
                return 'call' # We have a hand
            elif my_rank <= 7 and board['count'] == 0:
                # Preflop: 2-7 is a monster blocker, call wide.
                return 'call'
            else:
                return 'fold'
                
        # 2. The "Standard Bet" Rule:
        # If opponent bets modestly, we defend wide.
        
        else:
            if board['count'] == 0:
                # Preflop: Defend BB with top 40% of range roughly.
                # Low cards (2-7) are calling stations.
                # High cards (A-K) are calls.
                return 'call'
            
            else:
                # Postflop:
                # If we have a hand (Score > 40), we call.
                # If we have a blocker (High card on low board, or Low card on high board with high strength score), call.
                if strength_score > 40:
                    return 'call'
                
                # Strategic Raise: 
                # If we have a monster (Score > 80) and it's a raise round, we can punish the bet.
                if strength_score > 80 and 'raise' in allowed_actions:
                    return 'raise'
                
                return 'fold'

    # Fallback (should not be reached but required for safety)
    return 'fold'
