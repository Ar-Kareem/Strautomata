
import random
from collections import Counter

def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to HIT or STAY in a simplified Blackjack game.
    
    Strategy:
    1. Calculates the current score and identifies valid cards remaining in the deck.
    2. If Hitting is guaranteed safe (cannot bust), returns HIT.
    3. Simulates the opponent's gameplay (assuming a rational threshold strategy) 
       to generate a probability distribution of opponent scores.
    4. Calculates the Expected Value (Win Probability) of Staying at the current score.
    5. Calculates the Expected Value of Hitting by averaging the EV of the resulting scores
       from all possible next card draws.
    6. Returns the action with the higher Expected Value.
    """

    # --- Game Constants & Helper Functions ---
    
    full_deck_ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

    def get_card_value(card: str) -> int:
        if card in ["J", "Q", "K", "10"]:
            return 10
        elif card == "A":
            return 1  # Soft logic handled in calculate_score
        else:
            return int(card)

    def calculate_score(cards: list[str], t: int) -> int:
        total = 0
        ace_count = 0
        for c in cards:
            val = get_card_value(c)
            if c == "A":
                ace_count += 1
            total += val
        
        # If we have an Ace and using it as 11 keeps us <= target, do it.
        # Note: With only 1 Ace per deck, we only need to check adding 10 once.
        if ace_count > 0 and total + 10 <= t:
            return total + 10
        return total

    # --- State Analysis ---

    current_score = calculate_score(hand, target)
    
    # If we have already busted (shouldn't happen on input), we must stay.
    if current_score > target:
        return "STAY"

    # Identify remaining cards in our specific 13-card deck
    deck_counts = Counter(full_deck_ranks)
    for card in hand:
        deck_counts[card] -= 1
    
    remaining_deck = []
    for card, count in deck_counts.items():
        if count > 0:
            remaining_deck.append(card)

    if not remaining_deck:
        return "STAY"

    # --- Free Roll Check ---
    
    # If drawing any remaining card keeps us under or equal to target, HIT immediately.
    can_bust = False
    for card in remaining_deck:
        if calculate_score(hand + [card], target) > target:
            can_bust = True
            break
    
    if not can_bust:
        return "HIT"

    # --- Opponent Simulation ---
    
    # We estimate the distribution of the opponent's final score.
    # Assumption: Opponent plays a standard strategy of "Stand on Target - 5".
    # Valid range for Opponent Stand Threshold is clamped to reasonable bounds.
    opp_stand_threshold = max(target - 5, 11)
    
    sim_scores = []
    SIMULATIONS = 400
    
    for _ in range(SIMULATIONS):
        # Opponent plays from a fresh full deck
        opp_deck = list(full_deck_ranks)
        random.shuffle(opp_deck)
        opp_hand = []
        
        while True:
            # Opponent checks score
            op_scr = calculate_score(opp_hand, target)
            
            if op_scr > target:
                sim_scores.append(-1)  # -1 represents Bust
                break
            
            if op_scr >= opp_stand_threshold:
                sim_scores.append(op_scr)
                break
            
            if not opp_deck:
                sim_scores.append(op_scr)
                break
            
            # Opponent Hits
            opp_hand.append(opp_deck.pop())

    # --- Expected Value Calculation ---

    def get_win_probability(my_final_score: int) -> float:
        """
        Calculates the probability of winning/drawing against the simulated opponent distribution.
        Utility: Win = 1.0, Draw = 0.5, Loss = 0.0
        """
        # Case: I Busted
        if my_final_score > target:
            # If I bust, I only 'tie' (draw) if the opponent also busts. Otherwise I lose.
            opp_bust_count = sim_scores.count(-1)
            return 0.5 * (opp_bust_count / len(sim_scores))
        
        wins = 0.0
        for op_s in sim_scores:
            if op_s == -1:          # Opponent busted, I didn't -> Win
                wins += 1.0
            elif my_final_score > op_s: # My score higher -> Win
                wins += 1.0
            elif my_final_score == op_s: # Scores equal -> Draw
                wins += 0.5
            # else opponent higher -> Loss
            
        return wins / len(sim_scores)

    # EV of Staying
    ev_stay = get_win_probability(current_score)

    # EV of Hitting (Greedy 1-step Lookahead)
    # We average the utility of likely next states.
    ev_hit_sum = 0.0
    for card in remaining_deck:
        next_score = calculate_score(hand + [card], target)
        ev_hit_sum += get_win_probability(next_score)
    
    ev_hit = ev_hit_sum / len(remaining_deck)

    # --- Decision ---
    
    if ev_hit > ev_stay:
        return "HIT"
    else:
        return "STAY"
