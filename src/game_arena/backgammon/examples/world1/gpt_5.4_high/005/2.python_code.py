
# Backgammon policy
# The API requires:
#     def policy(state: dict) -> str
#
# Notes:
# - We always generate legal actions explicitly, then choose among them.
# - If equal dice ever appear, this code treats them as two identical dice
#   because the arena API only encodes up to two checker starts.

POINT_VALUE = [
    0.2, 0.5, 1.2, 1.8, 2.5, 1.7, 2.1, 1.6, 1.2, 1.0, 0.9, 0.8,
    0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.7, 1.8, 1.5, 1.1, 0.8
]

# Standard starting position, from our perspective.
START_MY = [0] * 24
START_MY[23] = 2
START_MY[12] = 5
START_MY[7] = 3
START_MY[5] = 5

START_OPP = [0] * 24
START_OPP[0] = 2
START_OPP[11] = 5
START_OPP[16] = 3
START_OPP[18] = 5

# Small standard opening book for non-double opening rolls.
# Keys are sorted descending dice tuples.
OPENING_BOOK = {
    (6, 5): "H:A23,A17",  # 24/13
    (6, 4): "H:A23,A17",  # 24/14
    (6, 3): "H:A23,A17",  # 24/15
    (6, 2): "H:A23,A17",  # 24/16
    (6, 1): "H:A12,A7",   # 13/7 8/7

    (5, 4): "H:A12,A23",  # 13/8 24/20
    (5, 3): "H:A7,A5",    # 8/3 6/3
    (5, 2): "H:A12,A12",  # 13/8 13/11
    (5, 1): "H:A12,A23",  # 13/8 24/23

    (4, 3): "H:A12,A12",  # 13/9 13/10
    (4, 2): "H:A7,A5",    # 8/4 6/4
    (4, 1): "H:A12,A23",  # 13/9 24/23

    (3, 2): "H:A23,A12",  # 24/21 13/11
    (3, 1): "H:A7,A5",    # 8/5 6/5

    (2, 1): "H:A12,A5",   # 13/11 6/5
}


def _norm_int(x, default=0):
    try:
        v = int(x)
    except Exception:
        return default
    return v


def _norm_pts(raw):
    try:
        pts = list(raw)
    except Exception:
        pts = []
    pts = pts[:24]
    if len(pts) < 24:
        pts = pts + [0] * (24 - len(pts))
    out = []
    for v in pts:
        try:
            n = int(v)
        except Exception:
            n = 0
        if n < 0:
            n = 0
        out.append(n)
    return out


def _norm_dice(raw):
    try:
        vals = list(raw)
    except Exception:
        vals = []
    out = []
    for v in vals[:2]:
        try:
            d = int(v)
        except Exception:
            continue
        if 1 <= d <= 6:
            out.append(d)
    return out


def _state_to_board(state):
    my_pts = _norm_pts(state.get("my_pts", [0] * 24))
    opp_pts = _norm_pts(state.get("opp_pts", [0] * 24))
    my_bar = max(0, _norm_int(state.get("my_bar", 0), 0))
    opp_bar = max(0, _norm_int(state.get("opp_bar", 0), 0))
    my_off = max(0, _norm_int(state.get("my_off", 0), 0))
    opp_off = max(0, _norm_int(state.get("opp_off", 0), 0))
    return [my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off]


def _token(src):
    if src == "B" or src == "P":
        return src
    return f"A{src}"


def _build_action(order, s1, s2):
    return f"{order}:{_token(s1)},{_token(s2)}"


def _opponent_view(board):
    my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off = board
    return [
        list(reversed(opp_pts)),
        list(reversed(my_pts)),
        opp_bar,
        my_bar,
        opp_off,
        my_off,
    ]


def _pip_count_player(pts, bar):
    total = bar * 25
    for i, c in enumerate(pts):
        total += (i + 1) * c
    return total


def _all_in_home_pts(pts, bar):
    if bar:
        return False
    for i in range(6, 24):
        if pts[i] > 0:
            return False
    return True


def _has_contact(board):
    my_pts, opp_pts, my_bar, opp_bar, _, _ = board
    if my_bar > 0 or opp_bar > 0:
        return True

    max_my = -1
    for i in range(23, -1, -1):
        if my_pts[i] > 0:
            max_my = i
            break

    min_opp = 24
    for i in range(24):
        if opp_pts[i] > 0:
            min_opp = i
            break

    return max_my >= min_opp


def _longest_prime(pts):
    best = 0
    cur = 0
    for n in pts:
        if n >= 2:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def _anchor_count(pts):
    cnt = 0
    for i in range(18, 24):
        if pts[i] >= 2:
            cnt += 1
    return cnt


def _back_pair_pips(pts):
    need = 2
    total = 0
    for i in range(23, -1, -1):
        c = pts[i]
        if c <= 0:
            continue
        take = c if c < need else need
        total += (i + 1) * take
        need -= take
        if need == 0:
            break
    return total


def _stack_penalty(pts):
    pen = 0.0
    for i, n in enumerate(pts):
        if n > 4:
            if i < 6:
                w = 0.25
            elif i < 18:
                w = 0.60
            else:
                w = 0.45
            pen += (n - 4) * w
        if n > 6:
            pen += (n - 6) * 0.40
    return pen


def _made_point_value(pts):
    val = 0.0
    for i, n in enumerate(pts):
        if n >= 2:
            val += POINT_VALUE[i]
            val += 0.10 * min(n - 2, 2)
    return val


def _count_blots(pts):
    cnt = 0
    for n in pts:
        if n == 1:
            cnt += 1
    return cnt


def _bearoff_wastage(pts):
    if any(pts[6:]):
        return 0.0
    w = 0.0
    for i, c in enumerate(pts[:6]):
        if c > 2:
            w += (c - 2) * (i + 1) * 0.40
    highest = -1
    for i in range(5, -1, -1):
        if pts[i] > 0:
            highest = i
            break
    if highest > 0:
        gaps = 0
        for i in range(highest):
            if pts[i] == 0:
                gaps += 1
        w += 1.2 * gaps
    return w


def _blot_exposure(my_pts, opp_pts, my_bar, opp_bar):
    # Approximate chance-weighted pip loss from direct one-die shots.
    total = 0.0
    for i in range(24):
        if my_pts[i] != 1:
            continue
        nums = set()
        if opp_bar > 0 and i < 6:
            nums.add(i + 1)
        start = i - 6
        if start < 0:
            start = 0
        for src in range(start, i):
            if opp_pts[src] > 0:
                nums.add(i - src)
        n = len(nums)
        if n:
            p_hit = 1.0 - ((6 - n) / 6.0) ** 2
            total += p_hit * (24 - i)
    return total


def _side_value(board):
    my_pts, opp_pts, my_bar, opp_bar, my_off, _ = board
    pip = _pip_count_player(my_pts, my_bar)
    v = -1.40 * pip + 5.0 * my_off - 9.0 * my_bar

    contact = _has_contact(board)

    if contact:
        mpv = _made_point_value(my_pts)
        prime = _longest_prime(my_pts)
        anchors = _anchor_count(my_pts)
        v += 1.60 * mpv
        if prime >= 2:
            v += 0.50 * prime * prime
        v += 0.25 * anchors
        v -= 0.60 * _stack_penalty(my_pts)
        v -= 0.16 * _back_pair_pips(my_pts)
        v -= 1.20 * _blot_exposure(my_pts, opp_pts, my_bar, opp_bar)
        v -= 0.10 * _count_blots(my_pts)
    else:
        if _all_in_home_pts(my_pts, my_bar):
            v -= 1.60 * _bearoff_wastage(my_pts)
        else:
            v -= 0.20 * _stack_penalty(my_pts)

    if my_bar > 0:
        blocked = 0
        for d in range(1, 7):
            if opp_pts[24 - d] >= 2:
                blocked += 1
        fail_prob = (blocked / 6.0) ** 2
        v -= (6.0 + 16.0 * fail_prob) * my_bar

    return v


def _evaluate(board):
    return _side_value(board) - _side_value(_opponent_view(board))


def _legal_single_moves(board, die):
    my_pts, opp_pts, my_bar, _, _, _ = board
    if die < 1 or die > 6:
        return []

    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest <= 23 and opp_pts[dest] < 2:
            return ["B"]
        return []

    home_ready = not any(my_pts[6:])

    moves = []
    for i in range(24):
        if my_pts[i] <= 0:
            continue

        dest = i - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                moves.append(i)
        else:
            if not home_ready:
                continue
            # Exact bearoff
            if i == die - 1:
                moves.append(i)
            # Oversize die can bear off only from highest occupied point
            elif die > i + 1:
                higher_exists = False
                for j in range(i + 1, 24):
                    if my_pts[j] > 0:
                        higher_exists = True
                        break
                if not higher_exists:
                    moves.append(i)

    return moves


def _apply_move(board, src, die):
    my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off = board
    my_pts = my_pts[:]
    opp_pts = opp_pts[:]

    if src == "B":
        my_bar -= 1
        dest = 24 - die
    else:
        my_pts[src] -= 1
        dest = src - die

    if dest < 0:
        my_off += 1
    else:
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            opp_bar += 1
        my_pts[dest] += 1

    return [my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off]


def _gen_sequences_order(board, die1, die2, order_char):
    seqs = []

    srcs1 = _legal_single_moves(board, die1)
    if srcs1:
        for s1 in srcs1:
            b1 = _apply_move(board, s1, die1)
            srcs2 = _legal_single_moves(b1, die2)
            if srcs2:
                for s2 in srcs2:
                    b2 = _apply_move(b1, s2, die2)
                    seqs.append((order_char, s1, s2, b2, 2, die1, die2))
            else:
                seqs.append((order_char, s1, "P", b1, 1, die1, die2))
    else:
        srcs2 = _legal_single_moves(board, die2)
        if srcs2:
            for s2 in srcs2:
                b2 = _apply_move(board, s2, die2)
                seqs.append((order_char, "P", s2, b2, 1, die1, die2))
        else:
            seqs.append((order_char, "P", "P", board, 0, die1, die2))

    return seqs


def _legal_actions(board, dice):
    dice = [d for d in dice if 1 <= d <= 6]

    if not dice:
        return [("H:P,P", board, "P", "P", 0)]

    if len(dice) == 1:
        die = dice[0]
        srcs = _legal_single_moves(board, die)
        if not srcs:
            return [("H:P,P", board, "P", "P", 0)]
        out = []
        for s in srcs:
            b = _apply_move(board, s, die)
            out.append((_build_action("H", s, "P"), b, s, "P", 1))
        return out

    d1, d2 = dice[0], dice[1]

    if d1 == d2:
        seqs = _gen_sequences_order(board, d1, d2, "H")
        max_used = max(seq[4] for seq in seqs)
        seqs = [seq for seq in seqs if seq[4] == max_used]
    else:
        hi = d1 if d1 >= d2 else d2
        lo = d2 if d1 >= d2 else d1
        seqs = _gen_sequences_order(board, hi, lo, "H") + _gen_sequences_order(board, lo, hi, "L")
        max_used = max(seq[4] for seq in seqs)
        seqs = [seq for seq in seqs if seq[4] == max_used]

        if max_used == 1:
            def used_die(seq):
                _, s1, s2, _, used, die1, die2 = seq
                if used == 0:
                    return None
                return die1 if s1 != "P" else die2

            if any(used_die(seq) == hi for seq in seqs):
                seqs = [seq for seq in seqs if used_die(seq) == hi]

    dedup = {}
    for order, s1, s2, final_board, used, _, _ in seqs:
        act = _build_action(order, s1, s2)
        if act not in dedup:
            dedup[act] = (act, final_board, s1, s2, used)

    return list(dedup.values())


def _is_standard_start(board):
    my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off = board
    return (
        my_bar == 0 and opp_bar == 0 and my_off == 0 and opp_off == 0 and
        my_pts == START_MY and opp_pts == START_OPP
    )


def _opening_book_action(board, dice, legal_strings):
    if len(dice) != 2 or dice[0] == dice[1]:
        return None
    if not _is_standard_start(board):
        return None
    key = tuple(sorted(dice, reverse=True))
    act = OPENING_BOOK.get(key)
    if act in legal_strings:
        return act
    return None


def _policy_impl(state):
    board = _state_to_board(state)
    dice = _norm_dice(state.get("dice", []))
    actions = _legal_actions(board, dice)

    if not actions:
        return "H:P,P"

    legal_strings = {a[0] for a in actions}
    book_act = _opening_book_action(board, dice, legal_strings)
    if book_act is not None:
        return book_act

    best_action = None
    best_score = None
    best_pref = None

    for act, final_board, s1, s2, _used in actions:
        score = _evaluate(final_board)
        pref = (1 if s1 != "P" else 0, 1 if s2 != "P" else 0)

        if best_action is None:
            best_action = act
            best_score = score
            best_pref = pref
            continue

        if score > best_score + 1e-9:
            best_action = act
            best_score = score
            best_pref = pref
        elif abs(score - best_score) <= 1e-9:
            if pref > best_pref or (pref == best_pref and act < best_action):
                best_action = act
                best_score = score
                best_pref = pref

    return best_action if best_action is not None else "H:P,P"


def _safe_legal_fallback(state):
    board = _state_to_board(state)
    dice = _norm_dice(state.get("dice", []))
    actions = _legal_actions(board, dice)
    if not actions:
        return "H:P,P"
    actions.sort(key=lambda x: (1 if x[2] == "P" else 0, 1 if x[3] == "P" else 0, x[0]))
    return actions[0][0]


def policy(state: dict) -> str:
    try:
        return _policy_impl(state)
    except Exception:
        try:
            return _safe_legal_fallback(state)
        except Exception:
            return "H:P,P"
