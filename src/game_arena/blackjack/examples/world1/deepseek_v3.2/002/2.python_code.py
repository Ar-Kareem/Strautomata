
import random
from typing import List

# Precompute optimal threshold L for each target T
def add_card(total: int, card: str, target: int) -> int:
    """Return new total after adding card."""
    if card == 'A':
        if total + 11 <= target:
            return total + 11
        else:
            return total + 1
    elif card in ('J', 'Q', 'K'):
        return total + 10
    else:
        return total + int(card)

def simulate_player(target: int, L: int) -> int:
    """Simulate one player using threshold L.
    Returns final total (may be > target if busted)."""
    deck = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    random.shuffle(deck)
    total = 0
    for card in deck:
        total = add_card(total, card, target)
        if total > target:
            return total  # bust
        if total >= L:
            return total
    return total

def compute_win_rate(target: int, L: int, trials: int = 2000) -> float:
    """Compute win rate for a player using threshold L against another using same L."""
    wins = 0
    for _ in range(trials):
        p1 = simulate_player(target, L)
        p2 = simulate_player(target, L)
        if p1 > target and p2 > target:
            # both bust -> draw
            wins += 0.5
        elif p1 > target:
            # p1 bust, p2 not bust -> p2 wins
            pass
        elif p2 > target:
            # p2 bust, p1 not bust -> p1 wins
            wins += 1
        else:
            # neither bust
            d1 = abs(target - p1)
            d2 = abs(target - p2)
            if d1 < d2:
                wins += 1
            elif d1 == d2:
                wins += 0.5
    return wins / trials

# Precompute L for each target from 10 to 30
L_T = {}
for target in range(10, 31):
    best_L = target
    best_rate = -1.0
    # Try thresholds from 0 to target+1
    for L in range(0, target + 2):
        rate = compute_win_rate(target, L, trials=1000)  # fewer trials for speed
        if rate > best_rate:
            best_rate = rate
            best_L = L
    L_T[target] = best_L

def hand_value(hand: List[str], target: int) -> int:
    """Compute current hand value according to target-dependent Ace rule."""
    total = 0
    has_ace = False
    for card in hand:
        if card == 'A':
            has_ace = True
        elif card in ('J', 'Q', 'K'):
            total += 10
        else:
            total += int(card)
    if has_ace:
        if total + 11 <= target:
            total += 11
        else:
            total += 1
    return total

def policy(hand: List[str], target: int) -> str:
    # Determine remaining cards
    all_cards = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}
    hand_set = set(hand)
    remaining = list(all_cards - hand_set)
    
    # If no cards left, must stay
    if not remaining:
        return "STAY"
    
    current_total = hand_value(hand, target)
    
    # If already at or above threshold, stay
    if current_total >= L_T[target]:
        return "STAY"
    
    # Check if all remaining cards would cause a bust
    bust_count = 0
    for card in remaining:
        new_total = add_card(current_total, card, target)
        if new_total > target:
            bust_count += 1
    if bust_count == len(remaining):
        return "STAY"
    
    # Otherwise hit
    return "HIT"
