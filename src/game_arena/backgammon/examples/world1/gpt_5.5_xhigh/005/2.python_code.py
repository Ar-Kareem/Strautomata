
import time

# ---------- Roll tables ----------

_ROLLS = []
_ROLL_WEIGHT = {}
_CONTAINING_CODES = {d: [] for d in range(1, 7)}

for _a in range(1, 7):
    for _b in range(_a, 7):
        _w = 1 if _a == _b else 2
        _code = _a * 8 + _b
        _ROLLS.append((_a, _b, _w, _code))
        _ROLL_WEIGHT[_code] = _w

for _d in range(1, 7):
    for _a, _b, _w, _code in _ROLLS:
        if _a == _d or _b == _d:
            _CONTAINING_CODES[_d].append(_code)


# ---------- Heuristic constants ----------

_POINT_WEIGHTS = (
    1.6, 2.3, 3.1, 4.0, 5.1, 5.0,
    4.6, 3.8, 3.1, 2.5, 2.1, 1.8,
    1.8, 2.0, 2.3, 2.7, 3.1, 3.5,
    3.8, 4.3, 4.9, 4.6, 3.8, 3.0,
)

_ANCHOR_WEIGHTS = (2.0, 3.4, 5.1, 5.4, 4.0, 2.5)
_HOME_BLOCK_WEIGHTS = (3.2, 3.6, 4.0, 4.4, 4.8, 5.2)


# ---------- Public API ----------

def policy(state: dict) -> str:
    """
    Return a legal move string in the format ORDER:FROM1,FROM2.
    """
    try:
        board = _board_from_state(state)
        dice = _clean_dice(state.get("dice", []))
        actions = _generate_legal_actions_for_board(board, dice)

        if not actions:
            return "H:P,P"
        if len(actions) == 1:
            return actions[0][0]

        # Winning immediately dominates everything.
        winning = [x for x in actions if x[1][4] >= 15]
        if winning:
            winning.sort(key=lambda x: _static_eval(x[1], fast=False), reverse=True)
            return winning[0][0]

        scored = [(_static_eval(b, fast=False), m, b) for (m, b) in actions]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_static_move = scored[0][1]

        # In pure races, static racing/bearoff evaluation is usually enough.
        if not _should_lookahead(board, actions):
            return best_static_move

        deadline = time.perf_counter() + 0.82
        candidates = _candidate_items(scored, board)

        best_move = best_static_move
        best_value = -1.0e100
        best_tiebreak = -1.0e100
        searched_any = False

        for static_score, move, result_board in candidates:
            if time.perf_counter() > deadline:
                break
            ev = _expected_after_opponent(result_board, deadline)
            if ev is None:
                break

            # Blend immediate quality with one-opponent-turn expectation.
            final_score = 0.85 * ev + 0.15 * static_score

            if (
                not searched_any
                or final_score > best_value + 1e-9
                or (abs(final_score - best_value) <= 1e-9 and static_score > best_tiebreak)
            ):
                best_value = final_score
                best_tiebreak = static_score
                best_move = move
                searched_any = True

        return best_move if searched_any else best_static_move

    except Exception:
        # Last-resort fallback: still try to return a generated legal move.
        try:
            board = _board_from_state(state)
            dice = _clean_dice(state.get("dice", []))
            actions = _generate_legal_actions_for_board(board, dice)
            if actions:
                return actions[0][0]
        except Exception:
            pass
        return "H:P,P"


# ---------- State normalization ----------

def _points_from_state(state, key):
    raw = state.get(key, [0] * 24)
    try:
        vals = list(raw)
    except Exception:
        vals = [0] * 24

    if len(vals) < 24:
        vals = vals + [0] * (24 - len(vals))
    elif len(vals) > 24:
        vals = vals[:24]

    out = []
    for x in vals:
        try:
            v = int(x)
        except Exception:
            v = 0
        out.append(v if v > 0 else 0)
    return out


def _nonneg_int(x):
    try:
        v = int(x)
    except Exception:
        return 0
    return v if v > 0 else 0


def _board_from_state(state):
    return (
        _points_from_state(state, "my_pts"),
        _points_from_state(state, "opp_pts"),
        _nonneg_int(state.get("my_bar", 0)),
        _nonneg_int(state.get("opp_bar", 0)),
        _nonneg_int(state.get("my_off", 0)),
        _nonneg_int(state.get("opp_off", 0)),
    )


def _clean_dice(dice):
    if dice is None:
        return []
    try:
        seq = list(dice)
    except Exception:
        seq = [dice]

    out = []
    for d in seq:
        try:
            x = int(d)
        except Exception:
            continue
        if 1 <= x <= 6:
            out.append(x)
            if len(out) == 2:
                break
    return out


# ---------- Legal move generation ----------

def _loc_token(loc):
    return "B" if loc < 0 else "A%d" % loc


def _all_home_for_my(my_pts, my_bar):
    if my_bar > 0:
        return False
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True


def _can_bear_off_from(my_pts, my_bar, i, die):
    if my_bar > 0 or i < 0 or i > 5:
        return False
    for j in range(6, 24):
        if my_pts[j] > 0:
            return False

    if die == i + 1:
        return True
    if die > i + 1:
        for j in range(i + 1, 6):
            if my_pts[j] > 0:
                return False
        return True
    return False


def _legal_locs(board, die):
    if die < 1 or die > 6:
        return []

    my, opp, my_bar, opp_bar, my_off, opp_off = board

    # Bar checkers must enter before anything else.
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp[dest] < 2:
            return [-1]
        return []

    locs = []
    all_home = True
    for j in range(6, 24):
        if my[j] > 0:
            all_home = False
            break

    for i, c in enumerate(my):
        if c <= 0:
            continue

        dest = i - die
        if dest >= 0:
            if opp[dest] < 2:
                locs.append(i)
        else:
            if all_home and i <= 5:
                if die == i + 1:
                    locs.append(i)
                elif die > i + 1:
                    higher = False
                    for j in range(i + 1, 6):
                        if my[j] > 0:
                            higher = True
                            break
                    if not higher:
                        locs.append(i)

    return locs


def _apply_single_loc(board, die, loc):
    my, opp, my_bar, opp_bar, my_off, opp_off = board

    if die < 1 or die > 6:
        return None

    if loc < 0:
        if my_bar <= 0:
            return None
        dest = 24 - die
        if dest < 0 or dest >= 24 or opp[dest] >= 2:
            return None

        nmy = my.copy()
        nopp = opp.copy()
        n_my_bar = my_bar - 1
        n_opp_bar = opp_bar

        if nopp[dest] == 1:
            nopp[dest] = 0
            n_opp_bar += 1
        nmy[dest] += 1

        return (nmy, nopp, n_my_bar, n_opp_bar, my_off, opp_off)

    if loc < 0 or loc >= 24 or my_bar > 0 or my[loc] <= 0:
        return None

    dest = loc - die

    if dest >= 0:
        if opp[dest] >= 2:
            return None

        nmy = my.copy()
        nopp = opp.copy()
        n_opp_bar = opp_bar

        nmy[loc] -= 1
        if nopp[dest] == 1:
            nopp[dest] = 0
            n_opp_bar += 1
        nmy[dest] += 1

        return (nmy, nopp, my_bar, n_opp_bar, my_off, opp_off)

    if not _can_bear_off_from(my, my_bar, loc, die):
        return None

    nmy = my.copy()
    nmy[loc] -= 1
    return (nmy, opp, my_bar, opp_bar, my_off + 1, opp_off)


def _add_action(out, seen, text, board):
    if text not in seen:
        seen.add(text)
        out.append((text, board))


def _generate_legal_actions_for_board(board, dice):
    if not dice:
        return [("H:P,P", board)]

    if len(dice) == 1:
        d = dice[0]
        starts = _legal_locs(board, d)
        if not starts:
            return [("H:P,P", board)]

        out = []
        seen = set()
        for loc in starts:
            nb = _apply_single_loc(board, d, loc)
            if nb is not None:
                _add_action(out, seen, "H:%s,P" % _loc_token(loc), nb)
        return out if out else [("H:P,P", board)]

    high = max(dice[0], dice[1])
    low = min(dice[0], dice[1])

    orders = [("H", high, low)]
    if high != low:
        orders.append(("L", low, high))

    # First try to play both dice. If any two-die play exists, all one-die
    # plays are illegal under the rules.
    out = []
    seen = set()
    for order, first_die, second_die in orders:
        for loc1 in _legal_locs(board, first_die):
            b1 = _apply_single_loc(board, first_die, loc1)
            if b1 is None:
                continue
            for loc2 in _legal_locs(b1, second_die):
                b2 = _apply_single_loc(b1, second_die, loc2)
                if b2 is None:
                    continue
                text = "%s:%s,%s" % (order, _loc_token(loc1), _loc_token(loc2))
                _add_action(out, seen, text, b2)

    if out:
        return out

    # No two-die play exists. Use the higher die if it can be played.
    starts = _legal_locs(board, high)
    if starts:
        out = []
        seen = set()
        for loc in starts:
            nb = _apply_single_loc(board, high, loc)
            if nb is not None:
                _add_action(out, seen, "H:%s,P" % _loc_token(loc), nb)
        return out if out else [("H:P,P", board)]

    # Otherwise use the lower die if possible.
    starts = _legal_locs(board, low)
    if starts:
        out = []
        seen = set()
        for loc in starts:
            nb = _apply_single_loc(board, low, loc)
            if nb is not None:
                _add_action(out, seen, "L:%s,P" % _loc_token(loc), nb)
        return out if out else [("H:P,P", board)]

    return [("H:P,P", board)]


# ---------- Board transforms ----------

def _mirror_board(board):
    my, opp, my_bar, opp_bar, my_off, opp_off = board
    return (
        list(reversed(opp)),
        list(reversed(my)),
        opp_bar,
        my_bar,
        opp_off,
        my_off,
    )


# ---------- Static evaluation ----------

def _pip_counts(board):
    my, opp, my_bar, opp_bar, my_off, opp_off = board
    my_pips = 25 * my_bar
    opp_pips = 25 * opp_bar

    for i, c in enumerate(my):
        if c:
            my_pips += c * (i + 1)
    for i, c in enumerate(opp):
        if c:
            opp_pips += c * (24 - i)

    return my_pips, opp_pips


def _has_contact(board):
    my, opp, my_bar, opp_bar, my_off, opp_off = board
    if my_bar > 0 or opp_bar > 0:
        return True

    max_my = -1
    for i, c in enumerate(my):
        if c > 0:
            max_my = i

    min_opp = 24
    for i, c in enumerate(opp):
        if c > 0:
            min_opp = i
            break

    return max_my > min_opp


def _home_made_side(pts):
    n = 0
    for i in range(6):
        if pts[i] >= 2:
            n += 1
    return n


def _home_prime_strength(pts):
    s = 0.0
    for i in range(6):
        if pts[i] >= 2:
            s += _HOME_BLOCK_WEIGHTS[i]
    return s


def _blot_count(pts):
    n = 0
    for c in pts:
        if c == 1:
            n += 1
    return n


def _bearoff_shape(pts):
    highest = -1
    for i in range(5, -1, -1):
        if pts[i] > 0:
            highest = i
            break
    if highest < 0:
        return 0.0

    gaps = 0
    for i in range(highest + 1):
        if pts[i] == 0:
            gaps += 1

    stack_pen = 0.0
    for i in range(6):
        if pts[i] > 3:
            stack_pen += 0.25 * (pts[i] - 3)

    return -0.30 * gaps - stack_pen


def _run_score(length, start, end, enemy_prefix):
    s = 0.55 * length * length
    if length >= 4:
        s += 1.5 * (length - 3)
    if length >= 6:
        s += 8.0

    # A prime is much less valuable if no enemy checkers are behind it.
    if enemy_prefix is not None:
        upto = end + 1
        if upto < 0:
            upto = 0
        elif upto > 24:
            upto = 24
        if enemy_prefix[upto] <= 0:
            s *= 0.35

    return s


def _side_structure(pts, contact, all_home, enemy_pts=None):
    score = 0.0

    for i, c in enumerate(pts):
        if c >= 2:
            w = _POINT_WEIGHTS[i]
            if not contact:
                w *= 0.45 if i <= 5 else 0.25
            if all_home and i <= 5:
                w *= 0.65
            score += w

        if c >= 4:
            excess = c - 3
            pen = 0.75 * excess + 0.25 * excess * excess
            if all_home and i <= 5:
                pen *= 0.45
            score -= pen

        elif c == 1 and contact:
            # Small builder value; blot risk is handled separately.
            if 6 <= i <= 17:
                score += 0.25
            elif i <= 5:
                score += 0.10

    if contact:
        enemy_prefix = None
        if enemy_pts is not None:
            enemy_prefix = [0] * 25
            running = 0
            for i in range(24):
                running += enemy_pts[i]
                enemy_prefix[i + 1] = running

        run = 0
        start = 0
        for i in range(24):
            if pts[i] >= 2:
                if run == 0:
                    start = i
                run += 1
            else:
                if run >= 2:
                    score += _run_score(run, start, i - 1, enemy_prefix)
                run = 0
        if run >= 2:
            score += _run_score(run, start, 23, enemy_prefix)

        for k, i in enumerate(range(18, 24)):
            if pts[i] >= 2:
                score += _ANCHOR_WEIGHTS[k]

    return score


def _shot_probability_against_up(victim_pts, attacker_pts, attacker_bar):
    """
    Approximate probability that the attacker, moving upward, can hit at least
    one victim blot next turn. Used only as a heuristic.
    """
    roll_codes = set()
    blockers = [c >= 2 for c in victim_pts]

    allow_board_sources = attacker_bar <= 0

    for i, c in enumerate(victim_pts):
        if c != 1:
            continue

        # Hits directly from the bar: upward-moving side enters on d-1.
        if attacker_bar > 0:
            if 0 <= i <= 5:
                roll_codes.update(_CONTAINING_CODES[i + 1])

            # With exactly one checker on the bar, it may enter and continue.
            if attacker_bar == 1:
                for a, b, w, code in _ROLLS:
                    entry = a - 1
                    if entry + b == i and not blockers[entry]:
                        roll_codes.add(code)
                        continue
                    if a != b:
                        entry = b - 1
                        if entry + a == i and not blockers[entry]:
                            roll_codes.add(code)

        if not allow_board_sources:
            continue

        # Direct hits with one die.
        for d in range(1, 7):
            src = i - d
            if src >= 0 and attacker_pts[src] > 0:
                roll_codes.update(_CONTAINING_CODES[d])

        # Same-checker two-die hits.
        for a, b, w, code in _ROLLS:
            src = i - a - b
            if src < 0 or attacker_pts[src] <= 0:
                continue

            inter = src + a
            if inter < 24 and not blockers[inter]:
                roll_codes.add(code)
                continue

            if a != b:
                inter = src + b
                if inter < 24 and not blockers[inter]:
                    roll_codes.add(code)

    if not roll_codes:
        return 0.0

    total = 0
    for code in roll_codes:
        total += _ROLL_WEIGHT[code]
    return total / 36.0


def _static_eval(board, fast=False):
    my, opp, my_bar, opp_bar, my_off, opp_off = board
    my_pips, opp_pips = _pip_counts(board)

    if my_off >= 15:
        return 100000.0 + 1000.0 * (15 - opp_off) + (opp_pips - my_pips)
    if opp_off >= 15:
        return -100000.0 - 1000.0 * (15 - my_off) + (opp_pips - my_pips)

    contact = _has_contact(board)
    opp_side = list(reversed(opp))
    my_mirror = list(reversed(my))

    my_all_home = _all_home_for_my(my, my_bar)
    opp_all_home = _all_home_for_my(opp_side, opp_bar)

    race_lead = opp_pips - my_pips  # positive means we are ahead in the race.

    if not contact:
        pip_w = 1.45
    elif my_all_home or opp_all_home:
        pip_w = 1.15
    else:
        pip_w = 0.85
        if race_lead > 15:
            pip_w += 0.15
        elif race_lead < -15:
            pip_w -= 0.10

    score = pip_w * race_lead

    off_w = 5.5
    if not contact:
        off_w = 8.0
    if my_all_home or opp_all_home:
        off_w = 9.0
    score += off_w * (my_off - opp_off)

    my_home_made = _home_made_side(my)
    opp_home_made = _home_made_side(opp_side)

    score += opp_bar * (15.0 + 4.5 * my_home_made + (18.0 if my_home_made >= 6 else 0.0))
    score -= my_bar * (15.0 + 4.5 * opp_home_made + (18.0 if opp_home_made >= 6 else 0.0))

    struct_factor = 1.0 if contact else 0.30
    score += struct_factor * _side_structure(my, contact, my_all_home, opp)
    score -= struct_factor * _side_structure(opp_side, contact, opp_all_home, my_mirror)

    if opp_bar > 0:
        score += 2.2 * _home_prime_strength(my)
    if my_bar > 0:
        score -= 2.2 * _home_prime_strength(opp_side)

    if my_all_home:
        score += _bearoff_shape(my)
    if opp_all_home:
        score -= _bearoff_shape(opp_side)

    if contact:
        if fast:
            my_blots = _blot_count(my)
            opp_blots = _blot_count(opp_side)
            safety = 0.8 + max(0.0, race_lead) / 100.0
            score -= safety * my_blots
            score += 0.35 * opp_blots
        else:
            my_danger = _shot_probability_against_up(my, opp, opp_bar)
            opp_danger = _shot_probability_against_up(opp_side, my_mirror, my_bar)

            safety_w = 22.0 + max(0.0, race_lead) * 0.10
            if race_lead < -20.0:
                safety_w *= 0.75
            score -= safety_w * my_danger

            attack_w = 9.0 + max(0.0, -race_lead) * 0.04
            score += attack_w * opp_danger

            score -= 0.70 * _blot_count(my)
            score += 0.35 * _blot_count(opp_side)

    return score


# ---------- Lookahead ----------

def _should_lookahead(board, actions):
    if _has_contact(board):
        return True
    for _, b in actions:
        if _has_contact(b):
            return True
    return False


def _candidate_items(scored, board):
    if len(scored) <= 12:
        return scored[:]

    candidates = []
    seen = set()

    def add(item):
        if item[1] not in seen:
            seen.add(item[1])
            candidates.append(item)

    for item in scored[:10]:
        add(item)

    init_opp_bar = board[3]
    init_my_off = board[4]

    # Ensure tactically important hitting/bearing-off plays are considered.
    special = sorted(
        scored,
        key=lambda x: (
            x[2][3] - init_opp_bar,
            x[2][4] - init_my_off,
            -x[2][2],
            x[0],
        ),
        reverse=True,
    )
    for item in special[:6]:
        add(item)
        if len(candidates) >= 12:
            break

    return candidates[:12]


def _expected_after_opponent(board, deadline):
    if board[4] >= 15 or board[5] >= 15:
        return _static_eval(board, fast=False)

    opp_board = _mirror_board(board)
    total = 0.0

    for a, b, weight, code in _ROLLS:
        if time.perf_counter() > deadline:
            return None

        replies = _generate_legal_actions_for_board(opp_board, [a, b])
        if not replies:
            total += weight * _static_eval(board, fast=False)
            continue

        # Opponent chooses the reply that is best from their perspective.
        best_opp_score = -1.0e100
        best_reply = replies[0][1]

        for _, rb in replies:
            val = _static_eval(rb, fast=True)
            if val > best_opp_score:
                best_opp_score = val
                best_reply = rb

        # Convert selected reply back to our perspective and evaluate it.
        our_after = _mirror_board(best_reply)
        total += weight * _static_eval(our_after, fast=False)

    return total / 36.0
