
from typing import List, Tuple, Optional

# Backgammon policy:
# Return legal move string in format "<ORDER>:<FROM1>,<FROM2>"

def policy(state: dict) -> str:
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = int(state['my_bar'])
    opp_bar = int(state['opp_bar'])
    my_off = int(state['my_off'])
    opp_off = int(state['opp_off'])
    dice = list(state['dice'])

    # No dice / no moves
    if len(dice) == 0:
        return "H:P,P"

    # Normalize to two dice for search. If one die, treat other as absent.
    if len(dice) == 1:
        d1 = d2 = dice[0]
        one_die_only = True
    else:
        d1, d2 = dice[0], dice[1]
        one_die_only = False

    high = max(d1, d2)
    low = min(d1, d2)

    initial = (my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off)

    # Generate candidate legal actions.
    actions = []

    if one_die_only:
        # A single die roll: order char can be H safely.
        die = dice[0]
        first_moves = legal_single_moves(initial, die)
        if not first_moves:
            return "H:P,P"
        for fm in first_moves:
            from1, s1, info1 = fm
            act = ("H", token_from(from1), "P", s1, [info1])
            actions.append(act)
    else:
        # Try both orderings. The legality rules are enforced by generation;
        # later we keep only actions that satisfy "both if possible", "higher if only one", etc.
        # Order H: high then low
        acts_H = gen_ordered_actions(initial, high, low, "H")
        # Order L: low then high
        acts_L = gen_ordered_actions(initial, low, high, "L")

        all_acts = acts_H + acts_L

        # Determine maximum number of playable dice among all sequences.
        max_used = 0
        for a in all_acts:
            used = count_used(a[4])
            if used > max_used:
                max_used = used

        if max_used == 0:
            return "H:P,P"

        # If only one die can be played, must play higher die when possible.
        if max_used == 1:
            filtered = []
            for a in all_acts:
                infos = a[4]
                if count_used(infos) != 1:
                    continue
                used_die = next(info['die'] for info in infos if info['used'])
                if used_die == high:
                    filtered.append(a)
            actions = filtered if filtered else [a for a in all_acts if count_used(a[4]) == 1]
        else:
            actions = [a for a in all_acts if count_used(a[4]) == 2]

    if not actions:
        return "H:P,P"

    # Score actions using resulting states and move features.
    best_score = None
    best_move = None

    for order, f1, f2, end_state, infos in actions:
        score = evaluate_action(initial, end_state, infos)
        # Tiny tie-breakers for determinism / style
        score += tie_break(order, f1, f2, infos)
        move = f"{order}:{f1},{f2}"
        if best_score is None or score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move is not None else "H:P,P"


def token_from(fr: Optional[int]) -> str:
    if fr is None:
        return "P"
    if fr == -1:
        return "B"
    return f"A{fr}"


def count_used(infos: List[dict]) -> int:
    return sum(1 for x in infos if x['used'])


def gen_ordered_actions(initial_state, die1: int, die2: int, order_char: str):
    actions = []

    first_moves = legal_single_moves(initial_state, die1)
    if not first_moves:
        # Could still possibly play only second die in the other ordering, but for this fixed ordering,
        # it's a pass on first step.
        actions.append((order_char, "P", "P", initial_state, [
            {'used': False, 'die': die1},
            {'used': False, 'die': die2},
        ]))
        return actions

    for from1, s1, info1 in first_moves:
        second_moves = legal_single_moves(s1, die2)
        if not second_moves:
            actions.append((order_char, token_from(from1), "P", s1, [
                info1,
                {'used': False, 'die': die2},
            ]))
        else:
            for from2, s2, info2 in second_moves:
                actions.append((order_char, token_from(from1), token_from(from2), s2, [
                    info1,
                    info2,
                ]))
    return actions


def legal_single_moves(state, die: int):
    my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off = unpack_state(state)
    moves = []

    # Must enter from bar first if any on bar.
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest <= 23 and opp_pts[dest] < 2:
            n_my = my_pts[:]
            n_opp = opp_pts[:]
            n_my_bar = my_bar - 1
            n_opp_bar = opp_bar
            n_my_off = my_off
            hit = 0
            if n_opp[dest] == 1:
                n_opp[dest] = 0
                n_opp_bar += 1
                hit = 1
            n_my[dest] += 1
            ns = (n_my, n_opp, n_my_bar, n_opp_bar, n_my_off, opp_off)
            moves.append((-1, ns, {'used': True, 'die': die, 'from': -1, 'hit': hit, 'bear': 0}))
        return moves

    can_bear = all_in_home(my_pts, my_bar)

    for src in range(24):
        if my_pts[src] <= 0:
            continue
        dest = src - die

        # Normal move on board
        if dest >= 0:
            if opp_pts[dest] >= 2:
                continue
            n_my = my_pts[:]
            n_opp = opp_pts[:]
            n_my[src] -= 1
            n_opp_bar = opp_bar
            hit = 0
            if n_opp[dest] == 1:
                n_opp[dest] = 0
                n_opp_bar += 1
                hit = 1
            n_my[dest] += 1
            ns = (n_my, n_opp, my_bar, n_opp_bar, my_off, opp_off)
            moves.append((src, ns, {'used': True, 'die': die, 'from': src, 'hit': hit, 'bear': 0}))
        else:
            # Bearing off
            if not can_bear:
                continue
            if src <= 5:
                exact = (src - die == -1)
                if exact:
                    n_my = my_pts[:]
                    n_my[src] -= 1
                    ns = (n_my, opp_pts[:], my_bar, opp_bar, my_off + 1, opp_off)
                    moves.append((src, ns, {'used': True, 'die': die, 'from': src, 'hit': 0, 'bear': 1}))
                else:
                    # Oversized die can bear off only from highest occupied point in home board
                    # i.e., no checker on higher home points than src.
                    if src - die < -1:
                        higher_exists = False
                        for j in range(src + 1, 6):
                            if my_pts[j] > 0:
                                higher_exists = True
                                break
                        if not higher_exists:
                            n_my = my_pts[:]
                            n_my[src] -= 1
                            ns = (n_my, opp_pts[:], my_bar, opp_bar, my_off + 1, opp_off)
                            moves.append((src, ns, {'used': True, 'die': die, 'from': src, 'hit': 0, 'bear': 1}))
    return moves


def unpack_state(state):
    return state[0], state[1], state[2], state[3], state[4], state[5]


def all_in_home(my_pts: List[int], my_bar: int) -> bool:
    if my_bar > 0:
        return False
    # Home board is points 0..5
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True


def pip_count(my_pts: List[int], my_bar: int) -> int:
    # Distance to bear off for our orientation: point i needs i+1 pips
    total = my_bar * 25
    for i, n in enumerate(my_pts):
        total += n * (i + 1)
    return total


def opponent_pip_count(opp_pts: List[int], opp_bar: int) -> int:
    # Opponent moves 0 -> 23, so distance to bear off is 24-i
    total = opp_bar * 25
    for i, n in enumerate(opp_pts):
        total += n * (24 - i)
    return total


def blot_penalty(my_pts: List[int], opp_pts: List[int], my_bar: int) -> float:
    # Penalize exposed single checkers, more if many opponent attackers exist.
    penalty = 0.0
    if my_bar > 0:
        penalty += 15.0 * my_bar

    for i in range(24):
        if my_pts[i] == 1:
            attackers = 0
            # Opponent comes from lower index to higher index; to hit our blot at i,
            # opp checker can start at j in [i-6, i-1]
            lo = max(0, i - 6)
            hi = i - 1
            for j in range(lo, hi + 1):
                if opp_pts[j] > 0:
                    attackers += opp_pts[j]
            # Also bar entries can hit on points 18..23 with die 6..1
            if i >= 18:
                attackers += opp_pts and 0  # no direct attacker count from opp bar under unknown roll
                if True:
                    attackers += 0.6 * 1  # generic extra danger near entry zone
            penalty += 2.0 + 1.2 * min(attackers, 6)
            if i >= 18:
                penalty += 1.2
            if i <= 5:
                penalty += 0.4
    return penalty


def block_value(my_pts: List[int]) -> float:
    v = 0.0
    for i in range(24):
        if my_pts[i] >= 2:
            v += 1.5
            if i <= 5:
                v += 1.0
            if 18 <= i <= 23:
                v += 0.8
    # Prime bonus for consecutive made points
    run = 0
    best = 0
    for i in range(24):
        if my_pts[i] >= 2:
            run += 1
            if run > best:
                best = run
        else:
            run = 0
    v += 1.2 * max(0, best - 1)
    return v


def distribution_flex(my_pts: List[int]) -> float:
    # Prefer fewer stacks > 3, mild distribution bonus
    val = 0.0
    for n in my_pts:
        if n >= 2:
            val += 0.3
        if n > 3:
            val -= 0.6 * (n - 3)
    return val


def back_checker_penalty(my_pts: List[int]) -> float:
    # Penalize very deep anchors/back checkers in racing-ish terms.
    pen = 0.0
    for i in range(18, 24):
        if my_pts[i] > 0:
            pen += 0.8 * my_pts[i] * (i - 17)
    return pen


def anchor_value(my_pts: List[int]) -> float:
    # Deep advanced anchors are useful while contact remains.
    val = 0.0
    for i in range(18, 24):
        if my_pts[i] >= 2:
            val += 1.0 + 0.25 * (i - 18)
    return val


def evaluate_position(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off) -> float:
    my_pip = pip_count(my_pts, my_bar)
    opp_pip = opponent_pip_count(opp_pts, opp_bar)
    race_edge = opp_pip - my_pip

    score = 0.0
    score += 12.0 * my_off
    score -= 12.0 * opp_off
    score += 0.22 * race_edge
    score -= 18.0 * my_bar
    score += 14.0 * opp_bar
    score += block_value(my_pts)
    score -= 0.7 * block_value(opp_pts)
    score -= blot_penalty(my_pts, opp_pts, my_bar)
    score += 0.35 * blot_penalty(opp_pts, my_pts, opp_bar)
    score += distribution_flex(my_pts)
    score -= 0.4 * distribution_flex(opp_pts)
    score -= back_checker_penalty(my_pts)
    score += 0.5 * back_checker_penalty(opp_pts)
    score += 0.7 * anchor_value(my_pts)
    return score


def evaluate_action(initial_state, end_state, infos: List[dict]) -> float:
    my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, opp_off0 = unpack_state(initial_state)
    my_pts1, opp_pts1, my_bar1, opp_bar1, my_off1, opp_off1 = unpack_state(end_state)

    score = evaluate_position(my_pts1, opp_pts1, my_bar1, opp_bar1, my_off1, opp_off1)

    # Action-local bonuses
    hits = sum(info.get('hit', 0) for info in infos if info.get('used'))
    bears = sum(info.get('bear', 0) for info in infos if info.get('used'))
    used = count_used(infos)

    score += 10.0 * hits
    score += 8.0 * bears
    score += 1.0 * used

    # Strongly favor entering from bar
    if my_bar0 > my_bar1:
        score += 12.0 * (my_bar0 - my_bar1)

    # Prefer making points / reducing blots compared to previous state
    before_made = sum(1 for n in my_pts0 if n >= 2)
    after_made = sum(1 for n in my_pts1 if n >= 2)
    score += 3.0 * (after_made - before_made)

    before_blots = sum(1 for n in my_pts0 if n == 1)
    after_blots = sum(1 for n in my_pts1 if n == 1)
    score += 1.6 * (before_blots - after_blots)

    # Escaping back checkers
    back0 = sum(my_pts0[i] for i in range(18, 24))
    back1 = sum(my_pts1[i] for i in range(18, 24))
    score += 1.1 * (back0 - back1)

    return score


def tie_break(order: str, f1: str, f2: str, infos: List[dict]) -> float:
    t = 0.0
    # Slight preference to use higher die first when equal
    if order == "H":
        t += 0.01
    # Prefer non-pass
    if f1 != "P":
        t += 0.005
    if f2 != "P":
        t += 0.003
    # Prefer bar entry first if tied
    if f1 == "B":
        t += 0.002
    # Deterministic lexical tiny tie-break
    t += (100 - lexical_rank(f1)) * 1e-6
    t += (100 - lexical_rank(f2)) * 1e-7
    return t


def lexical_rank(tok: str) -> int:
    if tok == "P":
        return 100
    if tok == "B":
        return 99
    try:
        return int(tok[1:])
    except Exception:
        return 100


if __name__ == "__main__":
    # Simple manual sanity check
    st = {
        'my_pts': [0]*24,
        'opp_pts': [0]*24,
        'my_bar': 0,
        'opp_bar': 0,
        'my_off': 0,
        'opp_off': 0,
        'dice': [3, 5],
    }
    st['my_pts'][23] = 2
    print(policy(st))
