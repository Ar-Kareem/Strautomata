
from typing import List, Tuple

NUM_POINTS = 24


def policy(state: dict) -> str:
    my_pts = list(state["my_pts"])
    opp_pts = list(state["opp_pts"])
    my_bar = int(state["my_bar"])
    opp_bar = int(state["opp_bar"])
    my_off = int(state["my_off"])
    opp_off = int(state["opp_off"])
    dice = list(state["dice"])

    if len(dice) == 0:
        return "H:P,P"

    legal = generate_legal_actions(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, dice)
    if not legal:
        return "H:P,P"

    best_action = None
    best_score = None
    for act, pos in legal:
        score = evaluate_position(*pos)
        if best_score is None or score > best_score:
            best_score = score
            best_action = act

    return best_action


def generate_legal_actions(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, dice):
    d1, d2 = dice[0], dice[1]
    high = max(d1, d2)
    low = min(d1, d2)

    results_both = []

    # Order H: high first, then low
    first_moves_h = legal_single_moves(my_pts, opp_pts, my_bar, my_off, high)
    for tok1, s1 in first_moves_h:
        second_moves = legal_single_moves(s1[0], s1[1], s1[2], s1[3], low)
        for tok2, s2 in second_moves:
            results_both.append((f"H:{tok1},{tok2}", (s2[0], s2[1], s2[2], opp_bar + s2[4], s2[3], opp_off)))

    # Order L: low first, then high
    first_moves_l = legal_single_moves(my_pts, opp_pts, my_bar, my_off, low)
    for tok1, s1 in first_moves_l:
        second_moves = legal_single_moves(s1[0], s1[1], s1[2], s1[3], high)
        for tok2, s2 in second_moves:
            results_both.append((f"L:{tok1},{tok2}", (s2[0], s2[1], s2[2], opp_bar + s2[4], s2[3], opp_off)))

    if results_both:
        dedup = {}
        for act, pos in results_both:
            dedup[act] = pos
        return list(dedup.items())

    # If both dice cannot be played, must play one die; if only one can be played, must play higher die when possible.
    high_moves = legal_single_moves(my_pts, opp_pts, my_bar, my_off, high)
    if high_moves:
        return [(f"H:{tok},P", (s[0], s[1], s[2], opp_bar + s[4], s[3], opp_off)) for tok, s in high_moves]

    low_moves = legal_single_moves(my_pts, opp_pts, my_bar, my_off, low)
    if low_moves:
        return [(f"L:{tok},P", (s[0], s[1], s[2], opp_bar + s[4], s[3], opp_off)) for tok, s in low_moves]

    return [("H:P,P", (my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off))]


def legal_single_moves(my_pts: List[int], opp_pts: List[int], my_bar: int, my_off: int, die: int):
    moves = []

    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            n_my = my_pts[:]
            n_opp = opp_pts[:]
            hit = 0
            if n_opp[dest] == 1:
                n_opp[dest] = 0
                hit = 1
            n_my[dest] += 1
            moves.append(("B", (n_my, n_opp, my_bar - 1, my_off, hit)))
        return moves

    can_bear = all(my_pts[i] == 0 for i in range(6, 24))

    for src in range(24):
        if my_pts[src] <= 0:
            continue

        dest = src - die

        if dest >= 0:
            if opp_pts[dest] >= 2:
                continue
            n_my = my_pts[:]
            n_opp = opp_pts[:]
            n_my[src] -= 1
            hit = 0
            if n_opp[dest] == 1:
                n_opp[dest] = 0
                hit = 1
            n_my[dest] += 1
            moves.append((f"A{src}", (n_my, n_opp, my_bar, my_off, hit)))
        else:
            if not can_bear:
                continue
            # Exact bear off
            if dest == -1 or src == die - 1:
                n_my = my_pts[:]
                n_my[src] -= 1
                moves.append((f"A{src}", (n_my, opp_pts[:], my_bar, my_off + 1, 0)))
            else:
                # Oversized bear off only from highest occupied point in home board
                higher_exists = any(my_pts[i] > 0 for i in range(src + 1, 6))
                if not higher_exists:
                    n_my = my_pts[:]
                    n_my[src] -= 1
                    moves.append((f"A{src}", (n_my, opp_pts[:], my_bar, my_off + 1, 0)))

    return moves


def evaluate_position(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off):
    score = 0.0

    score += 120.0 * my_off
    score -= 120.0 * opp_off

    score -= 90.0 * my_bar
    score += 85.0 * opp_bar

    # Race / pip count
    my_pip = my_bar * 25 + sum((i + 1) * my_pts[i] for i in range(24))
    opp_pip = opp_bar * 25 + sum((24 - i) * opp_pts[i] for i in range(24))
    score += 1.2 * (opp_pip - my_pip)

    # Made points, anchors, primes, blots
    made_points = 0
    home_made = 0
    advanced_made = 0
    blots = 0
    exposed_blots = 0

    for i in range(24):
        c = my_pts[i]
        if c >= 2:
            made_points += 1
            if 0 <= i <= 5:
                home_made += 1
            if 18 <= i <= 23:
                advanced_made += 1
        elif c == 1:
            blots += 1
            if blot_is_exposed(i, opp_pts):
                exposed_blots += 1

    opp_blots = 0
    hittable_opp_blots = 0
    for i in range(24):
        c = opp_pts[i]
        if c == 1:
            opp_blots += 1
            if opp_blot_hittable_by_me(i, my_pts, my_bar):
                hittable_opp_blots += 1

    score += 12.0 * made_points
    score += 9.0 * home_made
    score += 7.0 * advanced_made

    score -= 9.0 * blots
    score -= 11.0 * exposed_blots

    score += 6.0 * opp_blots
    score += 10.0 * hittable_opp_blots

    # Prime potential / connectivity
    consec = longest_prime(my_pts)
    score += 8.0 * consec

    # Stack penalty: too many on one point is inflexible
    for i in range(24):
        if my_pts[i] > 3:
            score -= 1.5 * (my_pts[i] - 3)

    return score


def blot_is_exposed(i: int, opp_pts: List[int]) -> bool:
    # Opponent moves upward. A blot at i is threatened by opp checker from j=i-6..i-1.
    lo = max(0, i - 6)
    for j in range(lo, i):
        if opp_pts[j] > 0:
            return True
    if i <= 5:
        return True  # opponent can enter from bar to home board points 5..0
    return False


def opp_blot_hittable_by_me(i: int, my_pts: List[int], my_bar: int) -> bool:
    # I move downward. Opp blot at i can be hit from j=i+1..i+6
    hi = min(23, i + 6)
    for j in range(i + 1, hi + 1):
        if my_pts[j] > 0:
            return True
    if my_bar > 0 and 18 <= i <= 23:
        return True
    return False


def longest_prime(my_pts: List[int]) -> int:
    best = 0
    cur = 0
    for i in range(24):
        if my_pts[i] >= 2:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best
