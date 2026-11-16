
import math
import random
from copy import deepcopy

# ------------------------------------------------------------
# Backgammon move generator and evaluator (policy)
# ------------------------------------------------------------

def policy(state: dict) -> str:
    # Extract state
    my_pts = state['my_pts'][:]
    opp_pts = state['opp_pts'][:]
    my_bar = int(state['my_bar'])
    opp_bar = int(state['opp_bar'])
    my_off = int(state['my_off'])
    opp_off = int(state['opp_off'])
    dice = list(state['dice'])
    if len(dice) == 0:
        # No dice: must pass
        return "H:P,P"

    # If only one die is provided, we must play that one die.
    # Engine will enforce "higher die when possible"; we enforce pass if no move.
    # If two dice (can be equal), we will try to play both.
    dice = sorted([int(d) for d in dice], reverse=True)
    die1, die2 = dice[0], dice[1] if len(dice) == 2 else dice[0]

    # Generate all legal FROM choices for the dice
    # Each choice is (order_char, from1_token, from2_token, sim_state)
    choices = []

    if len(dice) == 1:
        # Must play the single die; second token must be P
        candidates = list(generate_from_for_single_die(my_pts, opp_pts, my_bar, my_off, die1))
        if not candidates:
            return "H:P,P"
        best = None
        best_score = -1e18
        for from1 in candidates:
            new_state = apply_move_single_die(my_pts, opp_pts, my_bar, my_off, from1, die1)
            sc = evaluate_state(new_state)
            if sc > best_score:
                best_score = sc
                best = ("H", from1, "P", new_state)
        return f"{best[0]}:{best[1]},{best[2]}"

    else:
        # Try to play both dice; allow pass only if no combination possible
        first_choices = list(generate_from_for_die(my_pts, opp_pts, my_bar, my_off, die1))
        if not first_choices:
            # Can't play the first die at all => must pass
            return "H:P,P"

        best = None
        best_score = -1e18
        for from1 in first_choices:
            # Apply first die
            s1 = apply_move_single_die(my_pts, opp_pts, my_bar, my_off, from1, die1)
            # Generate legal FROM for the second die on the resulting state
            second_choices = list(generate_from_for_die(
                s1['my_pts'], s1['opp_pts'], s1['my_bar'], s1['my_off'], die2))
            if not second_choices:
                continue  # can't play both dice => skip this branch
            for from2 in second_choices:
                s2 = apply_move_single_die(
                    s1['my_pts'], s1['opp_pts'], s1['my_bar'], s1['my_off'], from2, die2)
                # Compose a consistent FROM token string for reporting (not used by engine)
                sc = evaluate_state(s2)
                # Prefer ORDER=H when equal score, and fewer exposed blots
                order_pref = 0  # prefer H
                exposed = count_exposed_blots(s2['my_pts'], s2['opp_pts'])
                key = (sc, order_pref, -exposed)
                if key > (best_score, 0 if best is None else 0, -1e9 if best is None else count_exposed_blots(best[3]['my_pts'], best[3]['opp_pts']) if best else -1e9):
                    best_score = key[0]
                    best = ("H", from1, from2, s2)

        if best is not None:
            return f"{best[0]}:{best[1]},{best[2]}"

        # If we reach here, we cannot play both dice in any combination.
        # In standard backgammon you would play the higher die if possible.
        # Enforced by engine, but we choose the best single-die move to maximize score.
        candidates = list(generate_from_for_single_die(my_pts, opp_pts, my_bar, my_off, die1))
        if not candidates:
            # No move at all (including higher die)
            return "H:P,P"
        best_single = None
        best_score = -1e18
        for from1 in candidates:
            new_state = apply_move_single_die(my_pts, opp_pts, my_bar, my_off, from1, die1)
            sc = evaluate_state(new_state)
            exposed = count_exposed_blots(new_state['my_pts'], new_state['opp_pts'])
            key = (sc, 0, -exposed)  # prefer H implicitly
            if key > (best_score, 0, -1e18 if best_single is None else count_exposed_blots(best_single[1]['my_pts'], best_single[1]['opp_pts']) if best_single else -1e18):
                best_score = key[0]
                best_single = (from1, new_state)
        return f"H:{best_single[0]},P"


# ------------------------------------------------------------
# Utility: FROM token generation (legal start positions)
# ------------------------------------------------------------

def point_token(i: int) -> str:
    return f"A{i}"


def parse_point_token(tok: str) -> int:
    # tok is like 'A3'
    return int(tok[1:])


def in_home_board(idx: int) -> bool:
    # Points 0..5 are my home board (from my perspective)
    return 0 <= idx <= 5


def generate_from_for_die(my_pts, opp_pts, my_bar, my_off, die):
    """
    Yield all legal FROM tokens (strings) to play this single die from the current state.
    Engine enforces rules; we only generate legal candidates:
    - If any of my checkers are on the bar, only 'B' is legal.
    - Otherwise, from any point idx with my checker, where die lands on an unblocked point (opp<=1).
    - Additionally, allow bear-off from home points (0..5) when permitted by standard rules.
    """
    # Bar entry constraint
    if my_bar > 0:
        # Only 'B' can be played, subject to legal entry
        entry_index = die - 1
        if 0 <= entry_index < 24:
            if opp_pts[entry_index] <= 1:
                yield "B"
        return

    # Not on the bar; try to move from points
    for idx in range(24):
        if my_pts[idx] == 0:
            continue
        # Check blocking
        dst = idx - die
        if dst < 0:
            # potential bear-off or shift within home
            if in_home_board(idx):
                # allowed to bear off or shift if legal
                # Let engine decide exact legality; yield as candidate
                yield point_token(idx)
            # else moving beyond board not allowed
            continue
        else:
            # standard move; check block
            if opp_pts[dst] <= 1:
                yield point_token(idx)

    # Also consider bear-off shifts in home when exact bear-off not possible:
    # We have already yielded the higher points as candidates; engine handles correctness.


def generate_from_for_single_die(my_pts, opp_pts, my_bar, my_off, die):
    # For a single die, treat same as generate_from_for_die
    return generate_from_for_die(my_pts, opp_pts, my_bar, my_off, die)


# ------------------------------------------------------------
# State transitions (apply a single die move given a FROM token)
# ------------------------------------------------------------

def apply_move_single_die(my_pts, opp_pts, my_bar, my_off, from_token, die):
    """
    Apply a legal single-die move from 'from_token' and produce a new state dict.
    Only changes counts at from_token, destination, bar, and off.
    Assumes the move is legal per engine rules.
    """
    s = {
        'my_pts': my_pts[:],
        'opp_pts': opp_pts[:],
        'my_bar': int(my_bar),
        'opp_bar': int(opp_bar),
        'my_off': int(my_off),
        'opp_off': int(opp_off),
    }
    opp_pts = s['opp_pts']  # local alias (reads only)

    # Determine source index
    if from_token == "B":
        src = None
        s['my_bar'] -= 1
        dst = die - 1
        # Enter from bar to opponent's home board point (dst)
        # Hits allowed only if opp has 1 there
        if opp_pts[dst] == 1:
            opp_pts[dst] = 0
            s['opp_bar'] += 1
        # Place my checker on dst
        s['my_pts'][dst] += 1
        return s
    else:
        src = parse_point_token(from_token)
        s['my_pts'][src] -= 1
        dst = src - die
        if dst < 0:
            # Bear off
            s['my_off'] += 1
            return s
        # Normal move
        if opp_pts[dst] == 1:
            opp_pts[dst] = 0
            s['opp_bar'] += 1
        s['my_pts'][dst] += 1
        return s


# ------------------------------------------------------------
# Heuristic evaluation
# ------------------------------------------------------------

def pip_count(pts, bar, off):
    total = 0
    for i, c in enumerate(pts):
        total += c * (i + 1)
    # A checker on bar is effectively at 0; borne off is 0
    total += bar * 0
    total += off * 0
    return total


def evaluate_state(state) -> float:
    """
    A heuristic score favoring:
    - winning races (higher pip lead),
    - safe primes and blockades,
    - advanced checkers in opponent's home,
    - hitting exposed blots,
    - fewer of our blots exposed,
    - having men off.
    """
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']

    # Basic race
    my_pips = pip_count(my_pts, my_bar, my_off)
    opp_pips = pip_count(opp_pts, opp_bar, opp_off)
    race = (opp_pips - my_pips) * 0.7

    # Advanced checkers in opponent's home (points 18..23)
    adv = sum(my_pts[i] for i in range(18, 24)) * 3.0

    # Blockade: points with 2+ checkers; geometric falloff towards my home
    blockade = 0.0
    for i in range(24):
        c = my_pts[i]
        if c >= 2:
            # weight slightly more for higher indices (towards opponent's side)
            weight = 1.0 + (i / 23.0)
            blockade += (c - 1) * 1.5 * weight

    # Primes: detect up to 5-point contiguous strong stacks
    prime_bonus = detect_prime_bonus(my_pts)

    # Hitting exposed opponent blots (opp has exactly 1 at a point)
    hit_opportunities = 0.0
    for i in range(24):
        if opp_pts[i] == 1:
            # value of hitting a blot increases the closer to our home it is
            hit_opportunities += (1.0 + (23 - i) / 23.0) * 2.0

    # Our exposed blots
    our_blots = sum(1 for c in my_pts if c == 1)
    exposed_penalty = -our_blots * 1.2

    # Bonus for bearing off
    bear_off_bonus = my_off * 4.0
    opp_bear_off_penalty = -opp_off * 3.0

    # Danger in our home: opponent men bearing off soon is bad
    opp_home_adv = sum(opp_pts[i] for i in range(0, 6)) * 0.5
    opp_adv_total = opp_home_adv + sum(opp_pts[i] * ((i + 1) / 24.0) for i in range(6, 24))

    score = (race + adv + blockade + prime_bonus + hit_opportunities +
             exposed_penalty + bear_off_bonus + opp_bear_off_penalty - opp_adv_total)
    return score


def detect_prime_bonus(pts):
    # Detect up to 5-point prime segments (2+ checkers) anywhere; slightly favor higher indices
    max_bonus = 0.0
    n = 24
    i = 0
    while i < n - 4:
        if pts[i] >= 2:
            length = 1
            j = i + 1
            while j < n and pts[j] >= 2:
                length += 1
                j += 1
            if length >= 5:
                # Strong prime
                # Weight primes towards the opponent's side a bit more
                center = (i + j - 1) / 2.0
                bonus = 6.0 + (center / 23.0) * 3.0
                if bonus > max_bonus:
                    max_bonus = bonus
            i = j
        else:
            i += 1
    return max_bonus


def count_exposed_blots(my_pts, opp_pts):
    # Count opponent blots (opp has 1) that are "in front" of my checkers
    # i.e., consider for each opponent blot, how many of my checkers are at >= blot index
    exposed = 0
    for i in range(24):
        if opp_pts[i] == 1:
            # If I have any checker at or beyond this point, I can hit it next turn
            ahead = sum(my_pts[j] for j in range(i, 24))
            if ahead > 0:
                exposed += 1
    return exposed
