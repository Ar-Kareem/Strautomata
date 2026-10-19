
from typing import List, Dict, Union, Tuple

Source = Union[int, str]  # int point index, 'B', or 'P'


def _copy_state(state: Dict) -> Dict:
    return {
        'my_pts': list(state['my_pts']),
        'opp_pts': list(state['opp_pts']),
        'my_bar': int(state['my_bar']),
        'opp_bar': int(state['opp_bar']),
        'my_off': int(state['my_off']),
        'opp_off': int(state['opp_off']),
    }


def _all_in_home(my_pts: List[int], my_bar: int) -> bool:
    return my_bar == 0 and sum(my_pts[6:]) == 0


def _can_bear_off(my_pts: List[int], my_bar: int, p: int, die: int) -> bool:
    if my_bar > 0 or p < 0 or p > 5 or my_pts[p] <= 0:
        return False
    if sum(my_pts[6:]) > 0:
        return False
    if die == p + 1:
        return True
    if die > p + 1:
        return sum(my_pts[p + 1:6]) == 0
    return False


def _legal_sources(state: Dict, die: int) -> List[Source]:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']

    if die < 1 or die > 6:
        return []

    # Bar checkers must enter first.
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            return ['B']
        return []

    out: List[Source] = []
    for p in range(24):
        if my_pts[p] <= 0:
            continue
        dest = p - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                out.append(p)
        else:
            if _can_bear_off(my_pts, my_bar, p, die):
                out.append(p)
    return out


def _apply_move(state: Dict, src: Source, die: int) -> Dict:
    ns = _copy_state(state)

    if src == 'B':
        ns['my_bar'] -= 1
        dest = 24 - die
    else:
        p = int(src)
        ns['my_pts'][p] -= 1
        dest = p - die

    if dest >= 0:
        if ns['opp_pts'][dest] == 1:
            ns['opp_pts'][dest] = 0
            ns['opp_bar'] += 1
        ns['my_pts'][dest] += 1
    else:
        ns['my_off'] += 1

    return ns


def _src_token(src: Source) -> str:
    if src == 'B':
        return 'B'
    if src == 'P':
        return 'P'
    return f"A{int(src)}"


def _encode_action(action: Tuple[str, Source, Source, Dict]) -> str:
    order, s1, s2, _ = action
    return f"{order}:{_src_token(s1)},{_src_token(s2)}"


def _my_pip_count(state: Dict) -> int:
    return sum((i + 1) * n for i, n in enumerate(state['my_pts'])) + 25 * state['my_bar']


def _opp_pip_count(state: Dict) -> int:
    return sum((24 - i) * n for i, n in enumerate(state['opp_pts'])) + 25 * state['opp_bar']


def _longest_made_run(my_pts: List[int]) -> int:
    best = 0
    cur = 0
    for n in my_pts:
        if n >= 2:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def _contact_exists(state: Dict) -> bool:
    if state['my_bar'] > 0 or state['opp_bar'] > 0:
        return True

    my_back = -1
    for i in range(23, -1, -1):
        if state['my_pts'][i] > 0:
            my_back = i
            break

    opp_front = 24
    for i in range(24):
        if state['opp_pts'][i] > 0:
            opp_front = i
            break

    return my_back > opp_front


def _threat_dice_count_to_blot(p: int, opp_pts: List[int], opp_bar: int) -> int:
    shots = set()

    # Direct hits by a checker already on board.
    for d in range(1, 7):
        q = p - d
        if 0 <= q < 24 and opp_pts[q] > 0:
            shots.add(d)

    # Direct hit from opponent bar entry.
    if opp_bar > 0 and 0 <= p <= 5:
        shots.add(p + 1)

    return len(shots)


def _blot_penalty(state: Dict, contact: bool) -> float:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    opp_bar = state['opp_bar']

    pen = 0.0
    for p, n in enumerate(my_pts):
        if n != 1:
            continue

        if contact:
            pen += 1.5

        k = _threat_dice_count_to_blot(p, opp_pts, opp_bar)
        if k > 0:
            prob = 1.0 - ((6.0 - k) / 6.0) ** 2
            zone = 1.0
            if p >= 18:
                zone += 0.35
            elif p >= 6:
                zone += 0.15
            if opp_bar > 0 and p <= 5:
                zone += 0.25
            pen += 14.0 * prob * zone

    return pen


def _structure_score(state: Dict, contact: bool) -> float:
    my_pts = state['my_pts']
    opp_bar = state['opp_bar']
    score = 0.0

    home_blocks = 0
    anchors = 0
    back_checkers = 0

    for i, n in enumerate(my_pts):
        if n >= 2:
            if i < 6:
                score += 10.0
                home_blocks += 1
            elif i < 18:
                score += 6.0
            else:
                score += 5.0
                anchors += 1

        if n > 3:
            score -= 1.5 * (n - 3)

        if i >= 18:
            back_checkers += n

    run = _longest_made_run(my_pts)
    score += 2.5 * run * run

    if opp_bar > 0:
        score += 6.0 * home_blocks

    if contact:
        score += 2.0 * anchors
        score -= 1.2 * back_checkers

    return score


def _race_smoothing_bonus(state: Dict) -> float:
    my_pts = state['my_pts']
    val = 0.0
    for i in range(6):
        if my_pts[i] > 2:
            val -= 0.7 * (my_pts[i] - 2)
    return val


def _evaluate(state: Dict) -> float:
    my_pip = _my_pip_count(state)
    opp_pip = _opp_pip_count(state)
    contact = _contact_exists(state)

    score = 0.0
    score += 125.0 * (state['my_off'] - state['opp_off'])
    score += 58.0 * state['opp_bar']
    score -= 72.0 * state['my_bar']
    score += 0.75 * (opp_pip - my_pip)
    score += _structure_score(state, contact)
    score -= _blot_penalty(state, contact)

    if not contact:
        score += 0.55 * (opp_pip - my_pip)
        score += _race_smoothing_bonus(state)

    if _all_in_home(state['my_pts'], state['my_bar']):
        score += 12.0 * state['my_off']
        score -= 0.15 * my_pip

    return score


def _generate_actions(state: Dict) -> List[Tuple[str, Source, Source, Dict]]:
    dice = list(state.get('dice', []))

    if len(dice) == 0:
        return [('H', 'P', 'P', _copy_state(state))]

    if len(dice) == 1:
        d = int(dice[0])
        srcs = _legal_sources(state, d)
        if not srcs:
            return [('H', 'P', 'P', _copy_state(state))]
        return [('H', s, 'P', _apply_move(state, s, d)) for s in srcs]

    d1, d2 = int(dice[0]), int(dice[1])

    # Equal dice: at most two moves in this arena format.
    if d1 == d2:
        d = d1
        firsts = _legal_sources(state, d)
        if not firsts:
            return [('H', 'P', 'P', _copy_state(state))]

        two_moves: List[Tuple[str, Source, Source, Dict]] = []
        one_move: List[Tuple[str, Source, Source, Dict]] = []

        for s1 in firsts:
            st1 = _apply_move(state, s1, d)
            seconds = _legal_sources(st1, d)
            if seconds:
                for s2 in seconds:
                    st2 = _apply_move(st1, s2, d)
                    two_moves.append(('H', s1, s2, st2))
            else:
                one_move.append(('H', s1, 'P', st1))

        return two_moves if two_moves else one_move

    high = max(d1, d2)
    low = min(d1, d2)

    # If both dice can be played, they must both be played.
    both: List[Tuple[str, Source, Source, Dict]] = []

    for s1 in _legal_sources(state, high):
        st1 = _apply_move(state, s1, high)
        for s2 in _legal_sources(st1, low):
            st2 = _apply_move(st1, s2, low)
            both.append(('H', s1, s2, st2))

    for s1 in _legal_sources(state, low):
        st1 = _apply_move(state, s1, low)
        for s2 in _legal_sources(st1, high):
            st2 = _apply_move(st1, s2, high)
            both.append(('L', s1, s2, st2))

    if both:
        # Deduplicate by encoded action.
        uniq = {}
        for a in both:
            uniq[_encode_action(a)] = a
        return list(uniq.values())

    # Otherwise, if only one die can be played, must play the higher die when possible.
    high_srcs = _legal_sources(state, high)
    if high_srcs:
        return [('H', s, 'P', _apply_move(state, s, high)) for s in high_srcs]

    low_srcs = _legal_sources(state, low)
    if low_srcs:
        return [('L', s, 'P', _apply_move(state, s, low)) for s in low_srcs]

    return [('H', 'P', 'P', _copy_state(state))]


def policy(state: dict) -> str:
    try:
        actions = _generate_actions(state)
    except Exception:
        return "H:P,P"

    if not actions:
        return "H:P,P"

    # If the only action is pass, return it directly.
    if len(actions) == 1 and actions[0][1] == 'P' and actions[0][2] == 'P':
        return "H:P,P"

    best_action = None
    best_score = None
    best_code = None

    for action in actions:
        code = _encode_action(action)
        try:
            sc = _evaluate(action[3])
        except Exception:
            sc = float('-inf')

        if (
            best_action is None
            or sc > best_score
            or (sc == best_score and code < best_code)
        ):
            best_action = action
            best_score = sc
            best_code = code

    if best_action is None:
        # Fallback to first legal action.
        return _encode_action(actions[0])

    return _encode_action(best_action)
