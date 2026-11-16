
# Backgammon arena policy
# Provides: policy(state: dict) -> str

from itertools import product

def _dest_from(src, die):
    """Our checkers always move from high index to low index. Bar enters at 24-die."""
    if src == 'B':
        return 24 - die
    return src - die

def _all_in_home(my_pts, my_bar):
    if my_bar > 0:
        return False
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True

def _can_bear_from(my_pts, src, die):
    """Assumes all in home. Moving from src with die bears off if src-die < 0 and rules allow."""
    dest = src - die
    if dest >= 0:
        return False
    # Exact bear-off allowed
    if src == die - 1:
        return True
    # Oversized die can bear off only from the highest occupied point.
    for j in range(src + 1, 6):
        if my_pts[j] > 0:
            return False
    return True

def _single_legal_sources(pos, die):
    my_pts, opp_pts, my_bar = pos["my_pts"], pos["opp_pts"], pos["my_bar"]

    if my_bar > 0:
        dest = _dest_from('B', die)
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            return ['B']
        return []

    sources = []
    in_home = _all_in_home(my_pts, my_bar)
    for s in range(24):
        if my_pts[s] <= 0:
            continue
        d = s - die
        if d >= 0:
            if opp_pts[d] < 2:
                sources.append(s)
        else:
            if in_home and s < 6 and _can_bear_from(my_pts, s, die):
                sources.append(s)
    return sources

def _apply_single(pos, src, die):
    """Apply one legal checker move and return new position plus tactical info."""
    my_pts = pos["my_pts"][:]
    opp_pts = pos["opp_pts"][:]
    my_bar = pos["my_bar"]
    opp_bar = pos["opp_bar"]
    my_off = pos["my_off"]
    opp_off = pos["opp_off"]

    hit = False
    bear = False

    if src == 'B':
        my_bar -= 1
        dest = 24 - die
    else:
        my_pts[src] -= 1
        dest = src - die

    if dest < 0:
        my_off += 1
        bear = True
    else:
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            opp_bar += 1
            hit = True
        my_pts[dest] += 1

    return {
        "my_pts": my_pts, "opp_pts": opp_pts,
        "my_bar": my_bar, "opp_bar": opp_bar,
        "my_off": my_off, "opp_off": opp_off
    }, {"hit": hit, "bear": bear, "src": src, "die": die, "dest": dest}

def _fmt_src(src):
    return 'B' if src == 'B' else ('P' if src == 'P' else 'A%d' % src)

def _pos_key(pos):
    return (tuple(pos["my_pts"]), tuple(pos["opp_pts"]), pos["my_bar"], pos["opp_bar"], pos["my_off"], pos["opp_off"])

def _pip_count(my_pts, my_bar):
    # Approximate pips to bear off: point i needs i+1 pips; bar is 25 pips.
    return my_bar * 25 + sum(my_pts[i] * (i + 1) for i in range(24))

def _opp_pip_count(opp_pts, opp_bar):
    # Opponent moves opposite direction, approximate pips to bear off: point i needs 24-i pips.
    return opp_bar * 25 + sum(opp_pts[i] * (24 - i) for i in range(24))

def _made_points_score(my_pts):
    score = 0.0
    for i, n in enumerate(my_pts):
        if n >= 2:
            # Home-board points are valuable; anchors in opponent home also useful.
            if i <= 5:
                score += 7.0 + (5 - i) * 0.7
            elif i >= 18:
                score += 4.0 + (i - 18) * 0.3
            else:
                score += 2.0
            if n > 2:
                score -= 0.25 * (n - 2)  # avoid excessive stacks
    return score

def _blot_risk(my_pts, opp_pts):
    risk = 0.0
    for i, n in enumerate(my_pts):
        if n == 1:
            # Direct shots from opponent behind this blot. Opp moves upward, so check lower indices.
            direct = 0
            for d in range(1, 7):
                j = i - d
                if 0 <= j < 24 and opp_pts[j] > 0:
                    direct += 1
            # Blots in/near home are particularly painful.
            mult = 1.0
            if i <= 5:
                mult = 2.0
            elif i <= 11:
                mult = 1.3
            risk += mult * (1.5 + direct * 1.2)
    return risk

def _opp_blot_targets(my_pts, opp_pts):
    val = 0.0
    # Reward having checkers that attack opponent blots within 6 pips.
    for i, on in enumerate(opp_pts):
        if on == 1:
            attackers = 0
            for d in range(1, 7):
                j = i + d  # our checker at higher point can move down to i
                if 0 <= j < 24 and my_pts[j] > 0:
                    attackers += 1
            if attackers:
                val += 0.8 * attackers
    return val

def _evaluate(pos, infos):
    my_pts, opp_pts = pos["my_pts"], pos["opp_pts"]
    my_bar, opp_bar = pos["my_bar"], pos["opp_bar"]
    my_off, opp_off = pos["my_off"], pos["opp_off"]

    pip = _pip_count(my_pts, my_bar)
    opp_pip = _opp_pip_count(opp_pts, opp_bar)
    hits = sum(1 for x in infos if x.get("hit"))
    bears = sum(1 for x in infos if x.get("bear"))

    score = 0.0
    score += my_off * 120.0
    score -= opp_off * 80.0
    score += (opp_pip - pip) * 1.15
    score -= my_bar * 45.0
    score += opp_bar * 35.0
    score += hits * 18.0
    score += bears * 25.0

    score += _made_points_score(my_pts)
    score -= _blot_risk(my_pts, opp_pts)
    score += _opp_blot_targets(my_pts, opp_pts)

    # Home board strength matters more when opponent is on bar.
    home_made = sum(1 for i in range(6) if my_pts[i] >= 2)
    score += home_made * (4.0 + 3.0 * opp_bar)

    # Bearoff race: if all in home, strongly prefer taking checkers off and lower pips.
    if _all_in_home(my_pts, my_bar):
        score += my_off * 80.0
        score -= pip * 2.0
        # Avoid gaps mildly during bearoff.
        for i in range(6):
            if my_pts[i] == 0 and any(my_pts[j] > 0 for j in range(i + 1, 6)):
                score -= 0.6

    # Penalize huge stacks.
    for n in my_pts:
        if n >= 5:
            score -= (n - 4) * 1.2

    return score

def _enumerate_for_order(state, order_char, dice_order):
    base = {
        "my_pts": state["my_pts"][:],
        "opp_pts": state["opp_pts"][:],
        "my_bar": state["my_bar"],
        "opp_bar": state["opp_bar"],
        "my_off": state["my_off"],
        "opp_off": state["opp_off"],
    }

    d1, d2 = dice_order
    actions = []

    s1s = _single_legal_sources(base, d1)
    if s1s:
        for s1 in s1s:
            p1, info1 = _apply_single(base, s1, d1)
            s2s = _single_legal_sources(p1, d2)
            if s2s:
                for s2 in s2s:
                    p2, info2 = _apply_single(p1, s2, d2)
                    actions.append((order_char, s1, s2, p2, [info1, info2], 2))
            else:
                actions.append((order_char, s1, 'P', p1, [info1], 1))
    else:
        # First die cannot play; second may still be playable.
        s2s = _single_legal_sources(base, d2)
        if s2s:
            for s2 in s2s:
                p2, info2 = _apply_single(base, s2, d2)
                actions.append((order_char, 'P', s2, p2, [info2], 1))
        else:
            actions.append((order_char, 'P', 'P', base, [], 0))
    return actions

def _legal_actions(state):
    dice = state.get("dice", [])
    if not dice:
        return [('H', 'P', 'P', {
            "my_pts": state["my_pts"][:], "opp_pts": state["opp_pts"][:],
            "my_bar": state["my_bar"], "opp_bar": state["opp_bar"],
            "my_off": state["my_off"], "opp_off": state["opp_off"]
        }, [], 0)]

    if len(dice) == 1:
        d = dice[0]
        # Encode as H; second pass.
        base = {
            "my_pts": state["my_pts"][:], "opp_pts": state["opp_pts"][:],
            "my_bar": state["my_bar"], "opp_bar": state["opp_bar"],
            "my_off": state["my_off"], "opp_off": state["opp_off"],
        }
        acts = []
        srcs = _single_legal_sources(base, d)
        if srcs:
            for s in srcs:
                p, info = _apply_single(base, s, d)
                acts.append(('H', s, 'P', p, [info], 1))
        else:
            acts.append(('H', 'P', 'P', base, [], 0))
        return acts

    low, high = min(dice[0], dice[1]), max(dice[0], dice[1])

    # This implementation treats doubles as two moves, matching the requested compact format.
    # If the engine supplies doubles differently, this still returns legal first-two-move encodings.
    actions = []
    if high == low:
        actions.extend(_enumerate_for_order(state, 'H', (high, low)))
    else:
        actions.extend(_enumerate_for_order(state, 'H', (high, low)))
        actions.extend(_enumerate_for_order(state, 'L', (low, high)))

    # Enforce normal backgammon "use maximum dice" and "if only one, use higher if possible".
    max_used = max(a[5] for a in actions)
    actions = [a for a in actions if a[5] == max_used]
    if max_used == 1 and high != low:
        # If any legal one-move action uses the higher die, lower-only actions are illegal.
        high_possible = bool(_single_legal_sources({
            "my_pts": state["my_pts"][:], "opp_pts": state["opp_pts"][:],
            "my_bar": state["my_bar"], "opp_bar": state["opp_bar"],
            "my_off": state["my_off"], "opp_off": state["opp_off"],
        }, high))
        if high_possible:
            filt = []
            for a in actions:
                order, s1, s2 = a[0], a[1], a[2]
                if (order == 'H' and s1 != 'P') or (order == 'L' and s2 != 'P'):
                    filt.append(a)
            if filt:
                actions = filt

    # De-duplicate identical move strings/positions
    seen = set()
    uniq = []
    for a in actions:
        key = (a[0], a[1], a[2], _pos_key(a[3]))
        if key not in seen:
            seen.add(key)
            uniq.append(a)
    return uniq

def policy(state: dict) -> str:
    try:
        actions = _legal_actions(state)
        if not actions:
            return "H:P,P"

        best = None
        best_score = -10**18
        for a in actions:
            sc = _evaluate(a[3], a[4])
            # tiny deterministic tie-breakers: prefer playing both, H, non-pass first
            sc += a[5] * 0.01
            if a[0] == 'H':
                sc += 0.001
            if a[1] != 'P':
                sc += 0.0001
            if sc > best_score:
                best_score = sc
                best = a

        return "%s:%s,%s" % (best[0], _fmt_src(best[1]), _fmt_src(best[2]))
    except Exception:
        # Last-resort syntactically valid fallback. In normal play enumeration above is used.
        return "H:P,P"
