
import random

def policy(state: dict) -> str:
    # --- Helper Functions ---

    def get_card_rank(card):
        return card['rank']

    def get_card_suit(card):
        return card['suit']

    def evaluate_5_card_hand(cards):
        """
        Returns (hand_strength, tie_breaker_values)
        hand_strength: 0=HighCard, 1=Pair, 2=TwoPair, 3=Trips, 4=Straight, 5=Flush, 6=FullHouse, 7=Quads, 8=StrFlush
        tie_breaker: list of ranks for tie-breaking
        """
        if len(cards) < 5:
            return (0, [])

        ranks = sorted([c['rank'] for c in cards], reverse=True)
        suits = [c['suit'] for c in cards]

        # Check Flush
        flush = False
        flush_suit = -1
        for s in set(suits):
            if suits.count(s) >= 5:
                flush = True
                flush_suit = s
                break
        
        # Check Straight
        straight = False
        straight_high = 0
        unique_ranks = sorted(list(set(ranks)), reverse=True)
        # Handle Ace low straight (A, 2, 3, 4, 5) - assuming rank 14 for Ace, but need to check 1 as well if present
        # In this game, ranks are ints, usually 2-14 (Ace). Let's assume standard 2-14.
        
        # Check standard straight
        if len(unique_ranks) >= 5:
            for i in range(len(unique_ranks) - 4):
                if unique_ranks[i] - unique_ranks[i+4] == 4:
                    straight = True
                    straight_high = unique_ranks[i]
                    break
        
        # Check Straight Flush
        if flush and straight:
            # Filter ranks by flush suit
            flush_ranks = sorted([c['rank'] for c in cards if c['suit'] == flush_suit], reverse=True)
            unique_flush_ranks = sorted(list(set(flush_ranks)), reverse=True)
            if len(unique_flush_ranks) >= 5:
                for i in range(len(unique_flush_ranks) - 4):
                    if unique_flush_ranks[i] - unique_flush_ranks[i+4] == 4:
                        return (8, [unique_flush_ranks[i]]) # StrFlush

        if flush:
            # Return 5 highest flush cards
            flush_cards = sorted([c['rank'] for c in cards if c['suit'] == flush_suit], reverse=True)
            return (5, flush_cards[:5])

        if straight:
            return (4, [straight_high])

        # Multiples
        rank_counts = {r: ranks.count(r) for r in set(ranks)}
        sorted_counts = sorted(rank_counts.items(), key=lambda x: (-x[1], -x[0]))

        # Quads
        if sorted_counts[0][1] == 4:
            kicker = [r for r in ranks if r != sorted_counts[0][0]][0]
            return (7, [sorted_counts[0][0], kicker])
        
        # Full House
        if sorted_counts[0][1] == 3 and len(sorted_counts) > 1 and sorted_counts[1][1] >= 2:
            return (6, [sorted_counts[0][0], sorted_counts[1][0]])
        
        # Trips
        if sorted_counts[0][1] == 3:
            kickers = [r for r in ranks if r != sorted_counts[0][0]][:2]
            return (3, [sorted_counts[0][0]] + kickers)
        
        # Two Pair
        if sorted_counts[0][1] == 2 and sorted_counts[1][1] == 2:
            kicker = [r for r in ranks if r not in [sorted_counts[0][0], sorted_counts[1][0]]][0]
            return (2, [sorted_counts[0][0], sorted_counts[1][0], kicker])
        
        # Pair
        if sorted_counts[0][1] == 2:
            kickers = [r for r in ranks if r != sorted_counts[0][0]][:3]
            return (1, [sorted_counts[0][0]] + kickers)
        
        # High Card
        return (0, ranks[:5])

    def calculate_equity(my_card, public_cards, n_opponents=1):
        """
        Approximate equity using Monte Carlo simulation.
        Simulates the remaining 4 cards (since we have 1 private + x public).
        """
        # If river is full, equity is showdown calculation
        if len(public_cards) == 5:
            my_hand_cards = public_cards + [my_card]
            my_strength = evaluate_5_card_hand(my_hand_cards)
            # We can't know opponent cards, but we can estimate based on how many cards beat us?
            # This is complex. For river, we rely on raw hand strength logic in main flow.
            return -1 

        # Simulation setup
        # Generate deck
        ranks = list(range(2, 15)) * 4
        suits = [0, 1, 2, 3] * 13
        deck = [{'rank': r, 'suit': s} for r, s in zip(ranks, suits)]
        
        # Remove known cards
        for c in [my_card] + public_cards:
            deck = [d for d in deck if not (d['rank'] == c['rank'] and d['suit'] == c['suit'])]

        if len(deck) < (5 - len(public_cards)): # Should not happen
            return 0.0

        wins = 0
        trials = 150  # Restricted for 1s CPU limit
        
        for _ in range(trials):
            random.shuffle(deck)
            board_needed = 5 - len(public_cards)
            simulated_board = public_cards + deck[:board_needed]
            used_deck = deck[board_needed:]
            
            # My 5 card hand
            my_5 = simulated_board + [my_card]
            my_str, my_tie = evaluate_5_card_hand(my_5)
            
            # Simulate opponent hands (assume random distribution of 1 hole card)
            opp_wins = False
            # Check against a few random opponent cards to estimate
            opp_samples = min(n_opponents * 2, len(used_deck)) 
            
            for i in range(0, opp_samples, 1):
                if i+1 >= len(used_deck): break
                opp_card = used_deck[i]
                opp_5 = simulated_board + [opp_card]
                opp_str, opp_tie = evaluate_5_card_hand(opp_5)
                
                if opp_str > my_str:
                    opp_wins = True
                    break
                elif opp_str == my_str:
                    # Compare tie breakers
                    if my_tie < opp_tie: # Lists are comparable in python
                         opp_wins = True
                         break
            
            if not opp_wins:
                wins += 1
                
        return wins / trials

    # --- Main Policy Logic ---

    # Extract State
    my_card = state['private_cards'][0]
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opp_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed = state['allowed_actions']

    # Determine Street
    street = "preflop"
    if len(public_cards) >= 3: street = "flop"
    if len(public_cards) == 4: street = "turn"
    if len(public_cards) == 5: street = "river"

    # Evaluate Current Hand
    current_hand_cards = public_cards + [my_card] if len(public_cards) > 0 else [my_card]
    hand_strength, tie_breaker = evaluate_5_card_hand(current_hand_cards)
    # Simplified Hand Categories
    is_monster = hand_strength >= 6 # Full House or better
    is_strong = hand_strength == 5 or hand_strength == 4 # Flush or Straight
    is_pair = hand_strength == 1
    high_card_rank = my_card['rank']

    # Board Texture
    board_ranks = [c['rank'] for c in public_cards]
    board_suits = [c['suit'] for c in public_cards]
    is_paired_board = len(set(board_ranks)) < len(board_ranks)
    is_flush_possible = len(set(board_suits)) == 1 if board_suits else False

    # Equity Approximation (only if not at showdown)
    equity = 0.0
    if street != "river":
        equity = calculate_equity(my_card, public_cards, 1)
    
    # Pot Odds
    total_to_call = to_call
    total_pot_after_call = pot + to_call
    pot_odds = total_to_call / total_pot_after_call if total_pot_after_call > 0 else 0
    
    # --- Decision Making ---

    # 1. Action Available: Fold
    if 'fold' in allowed and to_call > 0:
        # Tight Folding Rules
        if street == "preflop":
            # Only fold low cards preflop
            if high_card_rank <= 10 and not (my_card['rank'] > 10 and to_call < pot * 0.3):
                return 'fold'
        
        if street == "flop":
            # Fold if we missed and facing aggression
            if hand_strength == 0 and to_call > pot * 0.2:
                return 'fold'
            # Fold if opponent bets big on paired board and we have high card only
            if is_paired_board and hand_strength <= 1 and to_call > pot * 0.4:
                return 'fold'

        if street == "turn":
            # Fold if we have nothing
            if hand_strength == 0:
                return 'fold'
            # Fold Draws if price is too high (Equity < Pot Odds)
            if hand_strength < 4 and equity < pot_odds:
                return 'fold'
            # Fold weak pairs against large bets
            if is_pair and to_call > pot * 0.5 and equity < 0.4:
                return 'fold'

        if street == "river":
            # Bluff Catching logic
            if hand_strength == 0: 
                return 'fold'
            if is_pair and tie_breaker[0] < 12 and to_call > pot * 0.5:
                 # Folding weak pairs to big river bets
                 return 'fold'

    # 2. Action: Raise / All-In
    if 'raise' in allowed or 'all-in' in allowed:
        # Aggression Triggers
        
        # Preflop Aggression
        if street == "preflop":
            # Raise with high cards or good implied odds
            if high_card_rank >= 12:
                return 'raise'
            if high_card_rank >= 10:
                # Randomize to prevent being exploitable
                if random.random() < 0.5: return 'raise'
                return 'call'
            # Bluff raise if villain limps (to_call == small)
            if to_call > 0 and to_call < pot * 0.3:
                 return 'raise'

        # Postflop Aggression
        if street != "preflop":
            
            # Value Betting
            if is_monster:
                return 'all-in' if 'all-in' in allowed else 'raise'
            
            if is_strong:
                # If we have the flush/straight, we are likely winning. Raise.
                return 'raise'
            
            if hand_strength == 3: # Trips
                return 'raise'

            # Semi-Bluffs (Draws)
            if hand_strength < 4 and equity > 0.45:
                # Good draw equity
                if street == "flop" or street == "turn":
                    return 'raise' # Charge opponents
            
            # Bluffs (Air with initiative or scary board)
            if hand_strength == 0 or (is_pair and tie_breaker[0] < 8):
                # Only bluff if we can fold out better hands
                # Scary board = straight/flush possible
                scary = False
                if len(public_cards) >= 3:
                    # Check for 4 to a straight/flush
                    if len(set(board_suits)) == 1: scary = True
                    # Simple straight check logic
                    if len(set(board_ranks)) >= 3:
                         sorted_r = sorted(board_ranks)
                         if sorted_r[-1] - sorted_r[0] >= 4: scary = True
                
                if scary and random.random() < 0.4:
                    return 'raise'
                
                # If opponent checked (to_call == 0) and we are last to act, steal
                if to_call == 0:
                    return 'raise'

    # 3. Action: Call / Check
    if 'call' in allowed:
        # If facing a bet
        
        # Check if we have a draw worth calling
        if hand_strength < 4 and street != "river":
            if equity >= pot_odds:
                return 'call'
            # Call small bets with backdoor equity
            if to_call < pot * 0.2:
                return 'call'

        # Call with value (Pair+)
        if hand_strength >= 1:
            # Don't call massive overbets with marginal hands
            if to_call > pot * 0.6 and not is_strong and not is_monster:
                return 'fold' # Safety catch if logic above didn't fold
            return 'call'

        # Call if checked (Free card)
        if to_call == 0:
            return 'call'

    # Fallback / Safety
    if 'call' in allowed:
        return 'call'
    if 'fold' in allowed:
        return 'fold'
    
    return 'fold'
