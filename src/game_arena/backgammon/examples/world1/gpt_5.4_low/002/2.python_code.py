
from typing import List, Tuple, Dict

def policy(state: dict) -> str:
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = int(state['my_bar'])
    opp_bar = int(state['opp_bar'])
    my_off = int(state['my_off'])
    opp_off = int(state['opp_off'])
    dice = list(state['dice'])

    def clone(s):
        return {
            'my_pts': s['my_pts'][:],
            'opp_pts': s['opp_pts'][:],
            'my_bar': s['my_bar'],
            'opp_bar': s['opp_bar'],
            'my_off': s['my_off'],
            'opp_off': s['opp_off'],
        }

    init_state = {
        'my_pts': my_pts,
        'opp_pts': opp_pts,
        'my_bar': my_bar,
        'opp_bar': opp_bar,
        'my_off': my_off,
        'opp_off': opp_off,
    }

    def all_in_home(s):
        if s['my_bar'] > 0:
            return False
        for i in range(6, 24):
            if s['my_pts'][i] > 0:
                return False
        return True

    def legal_sources_for_die(s, die: int) -> List[str]:
        res = []
        if s['my_bar'] > 0:
            dest = 24 - die
            if 0 <= dest <= 23 and s['opp_pts'][dest] < 2:
                res.append('B')
            return res

        for p in range(24):
            if s['my_pts'][p] <= 0:
                continue
            dest = p - die
            if dest >= 0:
                if s['opp_pts'][dest] < 2:
                    res.append(f"A{p}")
            else:
                if all_in_home(s):
                    if die == p + 1:
                        res.append(f"A{p}")
                    elif die > p + 1:
                        higher_exists = False
                        for q in range(p + 1, 6):
                            if s['my_pts'][q] > 0:
                                higher_exists = True
                                break
                        if not higher_exists:
                            res.append(f"A{p}")
        return res

    def apply_move(s, src: str, die: int):
        ns = clone(s)
        if src == 'P':
            return ns
        if src == 'B':
            ns['my_bar'] -= 1
            dest = 24 - die
        else:
            p = int(src[1:])
            ns['my_pts'][p] -= 1
            dest = p - die

        if dest < 0:
            ns['my_off'] += 1
            return ns

        if ns['opp_pts'][dest] == 1:
            ns['opp_pts'][dest] = 0
            ns['opp_bar'] += 1

        ns['my_pts'][dest] += 1
        return ns

    def gen_sequences_for_order(s, dice_order: List[int], idx: int = 0):
        if idx == len(dice_order):
            return [([], s)]
        die = dice_order[idx]
        srcs = legal_sources_for_die(s, die)
        out = []
        if not srcs:
            for tail, end_state in gen_sequences_for_order(s, dice_order, idx + 1):
                out.append((['P'] + tail, end_state))
        else:
            for src in srcs:
                ns = apply_move(s, src, die)
                for tail, end_state in gen_sequences_for_order(ns, dice_order, idx + 1):
                    out.append(([src] + tail, end_state))
        return out

    def pip_count_my(s):
        total = 25 * s['my_bar']
        for i, n in enumerate(s['my_pts']):
            total += (i + 1) * n
        return total

    def pip_count_opp(s):
        total = 25 * s['opp_bar']
        for i, n in enumerate(s['opp_pts']):
            total += (24 - i) * n
        return total

    def has_contact(s):
        my_indices = [i for i, n in enumerate(s['my_pts']) if n > 0]
        opp_indices = [i for i, n in enumerate(s['opp_pts']) if n > 0]
        if not my_indices or not opp_indices:
            return False
        return max(my_indices) > min(opp_indices)

    def blot_exposure_penalty(s):
        penalty = 0.0
        opp_positions = [i for i, n in enumerate(s['opp_pts']) if n > 0]
        for p in range(24):
            if s['my_pts'][p] == 1:
                exposed = False
                threats = 0
                for j in opp_positions:
                    dist = p - j
                    if 1 <= dist <= 6:
                        exposed = True
                        threats += min(2, s['opp_pts'][j])
                if exposed:
                    penalty += 14 + 3 * threats
                    if p < 6:
                        penalty += 6
                    if p >= 18:
                        penalty += 3
        return penalty

    def point_structure_score(s):
        score = 0.0
        for p in range(24):
            n = s['my_pts'][p]
            if n >= 2:
                score += 8
                if 0 <= p <= 5:
                    score += 6
                if 6 <= p <= 11:
                    score += 3
                if 18 <= p <= 23:
                    score += 4
                if n >= 3:
                    score += 1.5
                if n >= 4:
                    score += 1.0
        return score

    def prime_score(s):
        score = 0.0
        run = 0
        for p in range(23, -1, -1):
            if s['my_pts'][p] >= 2:
                run += 1
            else:
                if run >= 2:
                    score += run * run * 3
                run = 0
        if run >= 2:
            score += run * run * 3
        return score

    def anchor_score(s):
        score = 0.0
        for p in range(18, 24):
            if s['my_pts'][p] >= 2:
                score += 7
        return score

    def home_board_strength(s):
        pts = 0
        for p in range(6):
            if s['my_pts'][p] >= 2:
                pts += 1
        return pts

    def eval_state(s):
        score = 0.0
        score += 140 * s['my_off']
        score -= 140 * s['opp_off']
        score -= 120 * s['my_bar']
        score += 90 * s['opp_bar']

        my_pip = pip_count_my(s)
        opp_pip = pip_count_opp(s)
        contact = has_contact(s)

        if contact:
            score += 1.2 * (opp_pip - my_pip)
        else:
            score += 2.0 * (opp_pip - my_pip)

        score += point_structure_score(s)
        score += prime_score(s)
        score += anchor_score(s)
        score += 10 * home_board_strength(s)

        score -= blot_exposure_penalty(s)

        for p in range(24):
            if s['opp_pts'][p] == 1:
                if 0 <= p <= 5:
                    score += 2
                elif 18 <= p <= 23:
                    score += 1

        if not contact:
            score += 6 * s['my_off']
            score -= 4 * sum(1 for p in range(24) if s['my_pts'][p] == 1)

        return score

    def fmt(order_label: str, srcs: List[str]) -> str:
        if len(srcs) == 0:
            return f"{order_label}:P,P"
        if len(srcs) == 1:
            return f"{order_label}:{srcs[0]},P"
        return f"{order_label}:{srcs[0]},{srcs[1]}"

    if len(dice) == 0:
        return "H:P,P"

    if len(dice) == 1:
        d = dice[0]
        seqs = gen_sequences_for_order(init_state, [d])
        legal = []
        for srcs, end_state in seqs:
            legal.append(("H", srcs, end_state, [d]))
        best = max(legal, key=lambda x: eval_state(x[2]))
        return fmt(best[0], best[1])

    d1, d2 = dice[0], dice[1]
    hi = max(d1, d2)
    lo = min(d1, d2)

    candidates = []
    seen = set()

    orders = [("H", [hi, lo])]
    if hi != lo:
        orders.append(("L", [lo, hi]))

    for label, order_dice in orders:
        seqs = gen_sequences_for_order(init_state, order_dice)
        for srcs, end_state in seqs:
            key = (label, tuple(srcs))
            if key in seen:
                continue
            seen.add(key)
            candidates.append((label, srcs, end_state, order_dice))

    if not candidates:
        return "H:P,P"

    max_moves = max(sum(1 for s in srcs if s != 'P') for _, srcs, _, _ in candidates)
    candidates = [c for c in candidates if sum(1 for s in c[1] if s != 'P') == max_moves]

    if max_moves == 1 and hi != lo:
        high_playable = []
        for c in candidates:
            _, srcs, _, order_dice = c
            moved_die = None
            for i, s in enumerate(srcs):
                if s != 'P':
                    moved_die = order_dice[i]
                    break
            if moved_die == hi:
                high_playable.append(c)
        if high_playable:
            candidates = high_playable

    best = max(candidates, key=lambda x: eval_state(x[2]))
    return fmt(best[0], best[1])
