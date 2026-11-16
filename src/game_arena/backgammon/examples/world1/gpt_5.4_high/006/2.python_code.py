
POINT_TOKENS = [f"A{i}" for i in range(24)]
ROLLS = [(a, b, 1 if a == b else 2) for a in range(1, 7) for b in range(a, 7)]
WIN_SCORE = 10**9


def _base_position(state):
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
    }


def _clone_position(pos):
    return {
        "my_pts": pos["my_pts"][:],
        "opp_pts": pos["opp_pts"][:],
        "my_bar": pos["my_bar"],
        "opp_bar": pos["opp_bar"],
        "my_off": pos["my_off"],
        "opp_off": pos["opp_off"],
    }


def _flip_position(pos):
    return {
        "my_pts": pos["opp_pts"][::-1],
        "opp_pts": pos["my_pts"][::-1],
        "my_bar": pos["opp_bar"],
        "opp_bar": pos["my_bar"],
        "my_off": pos["opp_off"],
        "opp_off": pos["my_off"],
    }


def _count_moves(fr1, fr2):
    return (fr1 != "P") + (fr2 != "P")


def _all_in_home(pos):
    return pos["my_bar"] == 0 and sum(pos["my_pts"][6:]) == 0


def _legal_single_moves(pos, die):
    moves = []
    my_pts = pos["my_pts"]
    opp_pts = pos["opp_pts"]

    # Must enter from bar first.
    if pos["my_bar"] > 0:
        dest = 24 - die  # die 1->23, die 6->18
        if opp_pts[dest] < 2:
            ns = _clone_position(pos)
            ns["my_bar"] -= 1
            if ns["opp_pts"][dest] == 1:
                ns["opp_pts"][dest] = 0
                ns["opp_bar"] += 1
            ns["my_pts"][dest] += 1
            moves.append(("B", ns))
        return moves

    can_bear = _all_in_home(pos)

    for i in range(23, -1, -1):
        if my_pts[i] <= 0:
            continue

        dest = i - die

        if dest >= 0:
            if opp_pts[dest] < 2:
                ns = _clone_position(pos)
                ns["my_pts"][i] -= 1
                if ns["opp_pts"][dest] == 1:
                    ns["opp_pts"][dest] = 0
                    ns["opp_bar"] += 1
                ns["my_pts"][dest] += 1
                moves.append((POINT_TOKENS[i], ns))
        else:
            if not can_bear:
                continue
            # Exact bear-off or overshoot from highest occupied point.
            if die == i + 1 or (die > i + 1 and sum(my_pts[i + 1:6]) == 0):
                ns = _clone_position(pos)
                ns["my_pts"][i] -= 1
                ns["my_off"] += 1
                moves.append((POINT_TOKENS[i], ns))

    return moves


def _gen_order_sequences(pos, dice_order, order_char):
    n = len(dice_order)
    if n == 0:
        return [(order_char, "P", "P", pos)]

    if n == 1:
        first_moves = _legal_single_moves(pos, dice_order[0])
        return [(order_char, fr1, "P", ns1) for fr1, ns1 in first_moves]

    # n == 2
    first_moves = _legal_single_moves(pos, dice_order[0])
    if not first_moves:
        return []

    out = []
    for fr1, ns1 in first_moves:
        second_moves = _legal_single_moves(ns1, dice_order[1])
        if second_moves:
            for fr2, ns2 in second_moves:
                out.append((order_char, fr1, fr2, ns2))
        else:
            out.append((order_char, fr1, "P", ns1))
    return out


def _dedup_actions(seqs):
    seen = {}
    for order_char, fr1, fr2, pos in seqs:
        act = f"{order_char}:{fr1},{fr2}"
        if act not in seen:
            seen[act] = pos
    return [(act, seen[act]) for act in sorted(seen.keys())]


def _legal_action_results(state):
    pos = _base_position(state)
    dice = list(state.get("dice", []))

    if len(dice) == 0:
        return [("H:P,P", pos)]

    if len(dice) == 1:
        d = dice[0]
        seqs = _gen_order_sequences(pos, [d], "H")
        if not seqs:
            return [("H:P,P", pos)]
        return _dedup_actions(seqs)

    d1, d2 = dice[0], dice[1]

    if d1 == d2:
        seqs = _gen_order_sequences(pos, [d1, d2], "H")
        if not seqs:
            return [("H:P,P", pos)]
        max_moves = max(_count_moves(fr1, fr2) for _, fr1, fr2, _ in seqs)
        seqs = [s for s in seqs if _count_moves(s[1], s[2]) == max_moves]
        return _dedup_actions(seqs)

    hi = d1 if d1 > d2 else d2
    lo = d2 if d1 > d2 else d1

    seqs = []
    seqs.extend(_gen_order_sequences(pos, [hi, lo], "H"))
    seqs.extend(_gen_order_sequences(pos, [lo, hi], "L"))

    if not seqs:
        return [("H:P,P", pos)]

    max_moves = max(_count_moves(fr1, fr2) for _, fr1, fr2, _ in seqs)
    seqs = [s for s in seqs if _count_moves(s[1], s[2]) == max_moves]

    # If only one die can be played, must use the higher die when possible.
    if max_moves == 1:
        high_die_seqs = [s for s in seqs if s[0] == "H"]
        if high_die_seqs:
            seqs = high_die_seqs

    return _dedup_actions(seqs)


def _has_contact(pos):
    if pos["my_bar"] > 0 or pos["opp_bar"] > 0:
        return True

    my_max = -1
    for i in range(23, -1, -1):
        if pos["my_pts"][i] > 0:
            my_max = i
            break

    opp_min = 24
    for i in range(24):
        if pos["opp_pts"][i] > 0:
            opp_min = i
            break

    return my_max > opp_min


def _current_direct_shots(pos):
    # Approximate single-die tactical shots for the side to move.
    opp_pts = pos["opp_pts"]

    # If on bar, practical direct shots are entry hits only.
    if pos["my_bar"] > 0:
        total = 0
        for i in range(18, 24):
            if opp_pts[i] == 1:
                total += 1
        return total

    my_pts = pos["my_pts"]
    total = 0
    for i in range(24):
        if opp_pts[i] != 1:
            continue
        shot_dice = 0
        for d in range(1, 7):
            src = i + d
            if src <= 23 and my_pts[src] > 0:
                shot_dice += 1
        total += shot_dice
    return total


def _side_features(pos):
    pts = pos["my_pts"]

    pips = 25 * pos["my_bar"]
    home_made = 0
    anchors = 0
    made_total = 0
    prime = 0
    run = 0
    blots = 0
    stack_pen = 0.0

    for i, n in enumerate(pts):
        if n > 0:
            pips += (i + 1) * n
            if n == 1:
                blots += 1
            if n >= 2:
                made_total += 1
                if i < 6:
                    home_made += 1
                if i >= 18:
                    anchors += 1
                run += 1
                if run > prime:
                    prime = run
            else:
                run = 0

            if n > 2:
                stack_pen += (n - 2) * (1.0 + 0.10 * max(i - 5, 0))
        else:
            run = 0

    # Two rearmost checkers: smaller is better.
    rear = 0
    need = 2
    for i in range(23, -1, -1):
        n = pts[i]
        if n <= 0:
            continue
        take = n if n < need else need
        rear += i * take
        need -= take
        if need == 0:
            break

    shots = _current_direct_shots(pos)
    return (pips, home_made, anchors, made_total, prime, blots, stack_pen, shots, rear)


def _static_eval(pos):
    if pos["my_off"] >= 15:
        return WIN_SCORE
    if pos["opp_off"] >= 15:
        return -WIN_SCORE

    me = _side_features(pos)
    opp = _side_features(_flip_position(pos))

    off_diff = pos["my_off"] - pos["opp_off"]
    bar_diff = pos["opp_bar"] - pos["my_bar"]
    pip_diff = opp[0] - me[0]
    home_diff = me[1] - opp[1]
    anchor_diff = me[2] - opp[2]
    made_diff = me[3] - opp[3]
    prime_diff = max(0, me[4] - 1) ** 2 - max(0, opp[4] - 1) ** 2
    blot_diff = opp[5] - me[5]
    stack_diff = opp[6] - me[6]
    shots_diff = me[7] - opp[7]
    rear_diff = opp[8] - me[8]

    if _has_contact(pos):
        return (
            28.0 * off_diff
            + 24.0 * bar_diff
            + 1.10 * pip_diff
            + 6.0 * home_diff
            + 4.0 * anchor_diff
            + 3.0 * made_diff
            + 2.5 * prime_diff
            + 1.6 * shots_diff
            + 2.6 * blot_diff
            + 0.7 * stack_diff
            + 0.25 * rear_diff
            + 7.0 * me[1] * pos["opp_bar"]
            - 7.0 * opp[1] * pos["my_bar"]
        )

    # Pure race / no contact.
    return (
        40.0 * off_diff
        + 25.0 * bar_diff
        + 2.20 * pip_diff
        + 1.2 * home_diff
        + 0.4 * made_diff
        + 0.7 * blot_diff
        + 1.1 * stack_diff
        + 0.6 * rear_diff
    )


def _expected_after_opponent(pos):
    if pos["my_off"] >= 15:
        return WIN_SCORE
    if pos["opp_off"] >= 15:
        return -WIN_SCORE

    opp_view = _flip_position(pos)

    total = 0.0
    total_w = 0

    for d1, d2, w in ROLLS:
        opp_view["dice"] = [d1, d2]
        opp_actions = _legal_action_results(opp_view)

        best_opp = -WIN_SCORE
        for _, opp_res in opp_actions:
            v = _static_eval(opp_res)  # from opponent's perspective
            if v > best_opp:
                best_opp = v

        total += w * (-best_opp)  # convert back to my perspective
        total_w += w

    return total / total_w


def _choose_best_action(state, actions):
    pos = _base_position(state)

    scored = [(_static_eval(res), act, res) for act, res in actions]
    scored.sort(key=lambda x: (-x[0], x[1]))

    # In pure races, static eval is enough and faster.
    if not _has_contact(pos):
        return scored[0][1]

    top_n = 8 if len(scored) > 8 else len(scored)
    top = scored[:top_n]

    best_act = top[0][1]
    best_total = -10**18
    best_quick = -10**18

    for quick, act, res in top:
        future = _expected_after_opponent(res)
        total = 0.65 * future + 0.35 * quick
        if (
            total > best_total + 1e-12
            or (
                abs(total - best_total) <= 1e-12
                and (
                    quick > best_quick + 1e-12
                    or (abs(quick - best_quick) <= 1e-12 and act < best_act)
                )
            )
        ):
            best_total = total
            best_quick = quick
            best_act = act

    return best_act


def policy(state: dict) -> str:
    actions = _legal_action_results(state)
    if not actions:
        return "H:P,P"
    if len(actions) == 1:
        return actions[0][0]

    try:
        return _choose_best_action(state, actions)
    except Exception:
        # Safety fallback: always return a legal move.
        return actions[0][0]
