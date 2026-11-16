
import itertools
import random
from typing import List, Tuple

# Precompute standard deck
STANDARD_DECK = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def card_value(card: str, aces_high: bool) -> int:
    if card == "A":
        return 11 if aces_high else 1
    if card in ["J", "Q", "K"]:
        return 10
    return int(card)

def get_hand_scores(cards: List[str]) -> List[int]:
    """
    Returns a list of possible scores for a hand.
    Handles Aces dynamically.
    """
    aces = cards.count("A")
    base_sum = sum(card_value(c, True) for c in cards if c != "A")
    scores = set()
    # Iterate through all combinations of aces being high or low
    # There are 2^aces combinations, but usually small (max 4 aces)
    for i in range(aces + 1):
        s = base_sum + (aces - i) * 11 + i * 1
        scores.add(s)
    return sorted(list(scores))

def get_best_score_under_target(cards: List[str], target: int) -> int:
    """
    Returns the highest score <= target from a hand.
    Returns -1 if all scores are > target (bust).
    """
    scores = get_hand_scores(cards)
    valid_scores = [s for s in scores if s <= target]
    if not valid_scores:
        return -1
    return max(valid_scores)

def get_remaining_deck(known_cards: List[str]) -> List[str]:
    """Returns a list of cards not in known_cards."""
    counts = {c: STANDARD_DECK.count(c) for c in STANDARD_DECK}
    for c in known_cards:
        counts[c] -= 1
    remaining = []
    for card, count in counts.items():
        remaining.extend([card] * count)
    return remaining

def simulate_opponent(opp_deck: List[str], target: int, our_best_score: int, iterations: int = 200) -> Tuple[float, float, float]:
    """
    Simulates opponent drawing cards optimally (hits until score is >= some threshold or bust).
    Since we don't know opponent's hand, we assume they start with 0 cards and draw randomly.
    Returns (win_prob, draw_prob, loss_prob).
    """
    if not opp_deck:
        # If opponent has no cards (shouldn't happen in full game setup), treat as 0 score
        if our_best_score >= 0:
            return 1.0, 0.0, 0.0
        return 0.0, 1.0, 0.0

    wins = 0
    draws = 0
    losses = 0
    
    # We can't simulate all permutations of 13 cards efficiently.
    # We sample random draws of up to, say, 5 cards (likely scenario).
    # Actually, since we assume opponent plays optimally, we can try a standard strategy:
    # Hit if score < target and score < 21.
    
    # To speed up: We randomly sample outcomes from the deck rather than full permutations.
    # We assume the opponent starts with a random hand, or 0 cards. 
    # Let's assume the opponent starts with 0 cards for the simulation, as no info is given.
    
    sample_size = min(iterations, 1000) 
    
    for _ in range(sample_size):
        random.shuffle(opp_deck)
        opp_hand = []
        for card in opp_deck:
            opp_hand.append(card)
            scores = get_hand_scores(opp_hand)
            
            # Opponent Strategy: Maximize score without busting
            best_opp = max([s for s in scores if s <= target], default=-1)
            bust = best_opp == -1
            
            if bust:
                losses += 1
                break
            
            # Opponent stops if close to target (usually stay if score >= 17 or close to target)
            # Let's assume opponent stays if score >= 17 or score >= target - 4
            # But strictly, we don't know their strategy. 
            # Let's assume they keep hitting until they have a good hand.
            if best_opp >= 17 or best_opp >= target: 
                # Opponent stays
                if our_best_score == -1:
                    losses += 1 # We busted, they didn't
                elif best_opp > our_best_score:
                    losses += 1
                elif best_opp == our_best_score:
                    draws += 1
                else:
                    wins += 1
                break
        else: # Deck exhausted without stopping
            best_opp = max([s for s in get_hand_scores(opp_hand) if s <= target], default=-1)
            if best_opp == -1:
                losses += 1
            elif our_best_score == -1:
                losses += 1
            elif best_opp > our_best_score:
                losses += 1
            elif best_opp == our_best_score:
                draws += 1
            else:
                wins += 1

    total = wins + draws + losses
    if total == 0: return 0.0, 0.0, 0.0
    return wins/total, draws/total, losses/total

def evaluate_hit(hand: List[str], target: int, opp_deck: List[str]) -> float:
    """
    Simulates hitting one card and estimates win probability.
    """
    remaining = get_remaining_deck(hand)
    if not remaining:
        return 0.0 # No cards left, cannot hit
    
    total_prob = 0.0
    unique_cards = set(remaining)
    
    for card in unique_cards:
        count = remaining.count(card)
        prob_draw = count / len(remaining)
        
        # Evaluate outcome of drawing this card
        new_hand = hand + [card]
        scores = get_hand_scores(new_hand)
        best_score = max([s for s in scores if s <= target], default=-1)
        
        if best_score == -1:
            # We bust with this card.
            # We lose unless opponent busts.
            # We simulate opponent briefly to check if they might bust.
            # But for speed, assume we lose 90% of the time if we bust, 
            # unless we know opponent deck is tough.
            # Let's be precise: simulate opponent.
            w, d, l = simulate_opponent(opp_deck, target, -1, iterations=50)
            # If we bust, we only win if opponent busts (losses for us is wins here)
            # simulate_opponent returns (Win prob for us, Draw, Loss for us)
            # If we bust, our score is -1. simulate_opponent compares our -1 vs opp.
            # We need to force our score as -1.
            
            # Hack: simulate_opponent uses our_best_score. If we busted, we lost.
            # But we can win if opponent also busts.
            # Let's adjust: simulate_opponent returns probabilities assuming we HAVE a score.
            # If we busted, our win prob is prob(opponent busts).
            w_opp, d_opp, l_opp = simulate_opponent(opp_deck, target, 1000, iterations=50) 
            # If we set our score to 1000 (impossible), simulate_opponent gives us loss prob (opponent win) etc.
            # We want: Opponent Busts = Win for us.
            # simulate_opponent(opp, target, our_score) returns (OppScore < OurScore).
            # If we busted, we win if OppBusts.
            # Let's call simulate_opponent treating our score as > T.
            # If our score is > T (bust), we win if opponent busts.
            # simulate_opponent returns (win, draw, loss).
            # If we set our score to Target+100 (bust), we win if opponent busts.
            # So w_opp is prob(opponent busts).
            prob_win = w_opp
        else:
            # We have a valid score `best_score`.
            # We stop here (simulating optimal play where we might stop or continue is complex).
            # Heuristic: Assume we stop if we hit a good score, or simulate further.
            # To keep it simple and fast: Simulate opponent outcome against this specific score.
            w, d, l = simulate_opponent(opp_deck, target, best_score, iterations=50)
            prob_win = w + d/2 # Draw is half a win? Or 0? Usually 0.5 for tiebreak.
            # Let's treat Draw as 0.5 win for simplicity in Expected Value.
            prob_win = w + 0.5 * d

        total_prob += prob_draw * prob_win
        
    return total_prob

def evaluate_stay(hand: List[str], target: int, opp_deck: List[str]) -> float:
    best_score = get_best_score_under_target(hand, target)
    # If we busted (should not be called if we busted, but defensive)
    if best_score == -1:
        return 0.0
    
    w, d, l = simulate_opponent(opp_deck, target, best_score, iterations=200)
    return w + 0.5 * d

def policy(hand: List[str], target: int) -> str:
    # 1. Analyze current hand
    current_best = get_best_score_under_target(hand, target)
    
    # If we have already busted (current_best == -1), we cannot make a move.
    # The game state handles this, but policy is called. Return STAY to be safe.
    if current_best == -1:
        return "STAY"
        
    # If we are at the target, STAY.
    if current_best == target:
        return "STAY"
        
    # 2. Determine remaining deck (opponent deck)
    # We assume opponent has a full deck unless we know cards.
    # In this simplified game, we only know our own cards.
    # The problem states: "You have your own 13-card deck... opponent has their own separate 13-card deck."
    # So we do not know opponent's cards.
    opp_deck = STANDARD_DECK[:] # Full deck
    
    # 3. Evaluate STAY
    # We can calculate exact probability for STAY against a random opponent draw
    prob_stay = evaluate_stay(hand, target, opp_deck)
    
    # 4. Evaluate HIT
    # We simulate hitting the next card.
    # To speed up, we look ahead 1 step. 
    # If we hit and bust, we lose (unless opp busts).
    # If we hit and stay valid, we might hit again?
    # The evaluate_hit function simulates a single hit and then assumes we stop (or estimates).
    # This is a greedy 1-step lookahead.
    # To be more robust, we should check if we should continue drawing.
    # A good heuristic: if (target - current_best) > 10, we MUST hit.
    # If (target - current_best) is small, we might STAY.
    
    prob_hit = evaluate_hit(hand, target, opp_deck)
    
    # Debug print (not allowed in final output usually, but useful here)
    # print(f"Hand: {hand}, Target: {target}, Stay: {prob_stay:.3f}, Hit: {prob_hit:.3f}")

    # Decision
    # Add a small epsilon to Hit to prefer action if equal, unless we are very close to target.
    # If we are very close to target, staying is usually safer if Hit risks busting.
    
    if prob_hit > prob_stay + 0.01: # Hysteresis
        return "HIT"
    else:
        return "STAY"
