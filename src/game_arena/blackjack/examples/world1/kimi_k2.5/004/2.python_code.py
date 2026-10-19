
from functools import lru_cache

ALL_CARDS = ('A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K')

def _hand_sum(hand, target):
    """Calculate the best possible sum of the hand (maximizing without busting)."""
    n_aces = hand.count('A')
    base = 0
    for c in hand:
        if c == 'A':
            base += 1
        elif c in ('J', 'Q', 'K'):
            base += 10
        elif c == '10':
            base += 10
        else:
            base += int(c)
    
    # Upgrade Aces from 1 to 11 (add 10) greedily while possible
    for _ in range(n_aces):
        if base + 10 <= target:
            base += 10
        else:
            break
    return base

def _get_remaining(hand_set):
    """Return list of cards remaining in the deck."""
    return [c for c in ALL_CARDS if c not in hand_set]

@lru_cache(maxsize=None)
def _max_exp_value(hand_tuple, target):
    """
    Compute the maximum expected final score achievable from this state
    by playing optimally to maximize expected score (single-player optimal).
    """
    hand = list(hand_tuple)
    s = _hand_sum(hand, target)
    
    if s > target:
        return 0
    
    stay = s
    remaining = _get_remaining(hand_tuple)
    if not remaining:
        return stay
    
    hit_val = sum(_max_exp_value(tuple(sorted(hand + [c])), target) for c in remaining) / len(remaining)
    return max(stay, hit_val)

@lru_cache(maxsize=32)
def _get_opp_dist(target):
    """
    Compute the probability distribution of final scores for an opponent
    who plays the max-expected-score strategy.
    Returns a dict: {score: probability}
    """
    @lru_cache(maxsize=None)
    def dist(hand_tuple):
        hand = list(hand_tuple)
        s = _hand_sum(hand, target)
        if s > target:
            return frozenset({(0, 1.0)})  # 0 represents bust
        
        remaining = _get_remaining(hand_tuple)
        if not remaining:
            return frozenset({(s, 1.0)})
        
        # Determine if max_exp strategy would hit or stay
        hit_val = sum(_max_exp_value(tuple(sorted(hand + [c])), target) for c in remaining) / len(remaining)
        
        if s >= hit_val:
            return frozenset({(s, 1.0)})
        else:
            d = {}
            for c in remaining:
                sub = dict(dist(tuple(sorted(hand + [c]))))
                for val, prob in sub.items():
                    d[val] = d.get(val, 0) + prob / len(remaining)
            return frozenset(d.items())
    
    return dict(dist(tuple()))

_win_prob_cache = {}

def policy(hand, target):
    """
    Choose action to maximize probability of winning against an opponent
    using the max-expectation strategy.
    """
    hand_tuple = tuple(sorted(hand))
    current_sum = _hand_sum(hand, target)
    
    if current_sum > target:
        return "STAY"
    
    opp_dist = _get_opp_dist(target)
    
    # Calculate win probability if we stay now
    wp_stay = 0.0
    for opp_s, prob in opp_dist.items():
        if current_sum > opp_s:
            wp_stay += prob
        elif current_sum == opp_s:
            wp_stay += 0.5 * prob
    
    remaining = _get_remaining(hand_tuple)
    if not remaining:
        return "STAY"
    
    if target not in _win_prob_cache:
        _win_prob_cache[target] = {}
    cache = _win_prob_cache[target]
    
    def get_wp_state(ht):
        """Recursive win probability from state ht assuming optimal play."""
        if ht in cache:
            return cache[ht]
        
        h = list(ht)
        s = _hand_sum(h, target)
        if s > target:
            return 0.0
        
        rem = _get_remaining(ht)
        if not rem:
            wp = 0.0
            for os, p in opp_dist.items():
                if s > os:
                    wp += p
                elif s == os:
                    wp += 0.5 * p
            cache[ht] = wp
            return wp
        
        # Win prob if stay
        wp_stay_local = 0.0
        for os, p in opp_dist.items():
            if s > os:
                wp_stay_local += p
            elif s == os:
                wp_stay_local += 0.5 * p
        
        # Win prob if hit (average over next cards)
        wp_hit_local = sum(get_wp_state(tuple(sorted(h + [c]))) for c in rem) / len(rem)
        
        best = max(wp_stay_local, wp_hit_local)
        cache[ht] = best
        return best
    
    # Calculate expected win probability if we hit now
    wp_hit = sum(get_wp_state(tuple(sorted(hand + [c]))) for c in remaining) / len(remaining)
    
    return "HIT" if wp_hit > wp_stay else "STAY"
