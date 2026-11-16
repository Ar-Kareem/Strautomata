
# blackjack_policy.py
# A smart HIT/STAY policy for the simplified finite-deck Blackjack-like game.

from __future__ import annotations

from typing import List, Dict

# Card universe (single suit, distinct ranks)
RANKS: List[str] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANK_TO_INDEX: Dict[str, int] = {r: i for i, r in enumerate(RANKS)}
FULL_MASK: int = (1 << 13) - 1

# Values treating Ace as 11 initially; later we "soften" by -10 if needed.
CARD_VALUES: List[int] = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
ACE_BIT: int = 1 << RANK_TO_INDEX["A"]

# Precompute masks grouped by popcount for efficient acyclic DP.
MASKS_BY_COUNT: List[List[int]] = [[] for _ in range(14)]
for m in range(1 << 13):
    MASKS_BY_COUNT[m.bit_count()].append(m)

# Precompute hard sums and "has ace" for every mask (Ace counted as 11 in hard_sum).
HARD_SUM: List[int] = [0] * (1 << 13)
HAS_ACE: List[int] = [0] * (1 << 13)
for m in range(1, 1 << 13):
    lsb = m & -m
    prev = m ^ lsb
    idx = lsb.bit_length() - 1
    HARD_SUM[m] = HARD_SUM[prev] + CARD_VALUES[idx]
    HAS_ACE[m] = HAS_ACE[prev] | (1 if (lsb == ACE_BIT) else 0)


def _hand_value(mask: int, target: int) -> int:
    """Compute hand value with the game's Ace adjustment relative to 'target'."""
    total = HARD_SUM[mask]
    if total > target and HAS_ACE[mask]:
        total -= 10  # Ace becomes 1 instead of 11
    return total


def _opponent_distribution_threshold(target: int, k: int) -> List[float]:
    """
    Compute opponent terminal distribution under a fixed rule:
    HIT while value < (target - k), otherwise STAY.
    Output vector of length (target+2): indices 0..target for exact totals, last index is BUST.
    """
    threshold = target - k
    if threshold < 0:
        threshold = 0

    bust_idx = target + 1
    dist = [0.0] * (target + 2)

    # prob[mask] is probability of being at this mask while still "in play" (not yet terminal)
    prob = [0.0] * (1 << 13)
    prob[0] = 1.0

    # Process masks in increasing size; transitions only go to larger masks (acyclic).
    for cnt in range(14):
        for mask in MASKS_BY_COUNT[cnt]:
            p = prob[mask]
            if p == 0.0:
                continue

            v = _hand_value(mask, target)
            if v > target:
                dist[bust_idx] += p
                continue

            rem = FULL_MASK ^ mask
            if v >= threshold or rem == 0:
                dist[v] += p
                continue

            n = rem.bit_count()
            share = p / n
            tmp = rem
            while tmp:
                lsb = tmp & -tmp
                tmp -= lsb
                prob[mask | lsb] += share

    return dist


def _build_policy_for_target(target: int) -> bytearray:
    """
    Build a HIT(1)/STAY(0) table indexed by mask for a given target.
    The objective is to maximize win probability vs an opponent modeled as a mixture of thresholds.
    """
    # Mixture over plausible opponent "stay-within-k" thresholds for robustness.
    # (k small = aggressive; k larger = conservative)
    mixture = [
        (0, 0.05),
        (1, 0.10),
        (2, 0.20),
        (3, 0.25),
        (4, 0.20),
        (5, 0.15),
        (6, 0.05),
    ]

    bust_idx = target + 1
    opp_mix = [0.0] * (target + 2)
    for k, w in mixture:
        d = _opponent_distribution_threshold(target, k)
        for i in range(target + 2):
            opp_mix[i] += w * d[i]

    # Convert opponent distribution into our terminal win-probability payoff.
    pbust = opp_mix[bust_idx]
    prefix = [0.0] * (target + 1)
    run = 0.0
    for s in range(target + 1):
        run += opp_mix[s]
        prefix[s] = run

    winprob = [0.0] * (target + 1)  # winprob[s] if we stay with total s (s <= target)
    for s in range(target + 1):
        less = prefix[s - 1] if s > 0 else 0.0
        winprob[s] = pbust + less + 0.5 * opp_mix[s]

    winprob_bust = 0.5 * pbust  # if we bust, we only "win" when opponent also busts (draw counts as 0.5)

    # Backward induction over masks to compute optimal action maximizing expected win probability.
    value = [0.0] * (1 << 13)
    action_hit = bytearray(1 << 13)  # 1 => HIT, 0 => STAY

    for cnt in range(13, -1, -1):
        for mask in MASKS_BY_COUNT[cnt]:
            v = _hand_value(mask, target)

            if v > target:
                value[mask] = winprob_bust
                action_hit[mask] = 0
                continue

            stay = winprob[v]
            rem = FULL_MASK ^ mask
            if rem == 0:
                hit = stay
            else:
                n = rem.bit_count()
                acc = 0.0
                tmp = rem
                while tmp:
                    lsb = tmp & -tmp
                    tmp -= lsb
                    newmask = mask | lsb
                    nv = _hand_value(newmask, target)
                    if nv > target:
                        acc += winprob_bust
                    else:
                        acc += value[newmask]
                hit = acc / n

            # Tie-break slightly toward STAY to reduce unnecessary variance.
            if hit > stay + 1e-12:
                value[mask] = hit
                action_hit[mask] = 1
            else:
                value[mask] = stay
                action_hit[mask] = 0

    return action_hit


# Precompute action tables for all valid targets.
_ACTION_TABLE: Dict[int, bytearray] = {}
for _T in range(10, 31):
    _ACTION_TABLE[_T] = _build_policy_for_target(_T)


def policy(hand: list[str], target: int) -> str:
    """
    Required API: return "HIT" or "STAY".
    """
    # Safety: if target is out of expected range, fall back to a simple conservative rule.
    if target not in _ACTION_TABLE:
        # Compute value with the same ace adjustment logic, but from raw hand.
        mask = 0
        for c in hand:
            idx = RANK_TO_INDEX.get(c)
            if idx is not None:
                mask |= (1 << idx)
        v = _hand_value(mask, target)
        if v > target:
            return "STAY"
        return "HIT" if v < target - 3 else "STAY"

    # Build mask of current hand.
    mask = 0
    for c in hand:
        idx = RANK_TO_INDEX.get(c)
        if idx is not None:
            mask |= (1 << idx)

    # If already bust (should usually not be queried), always STAY (legal action).
    if _hand_value(mask, target) > target:
        return "STAY"

    return "HIT" if _ACTION_TABLE[target][mask] else "STAY"
