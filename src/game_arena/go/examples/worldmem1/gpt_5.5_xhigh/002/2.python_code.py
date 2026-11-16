
# Heuristic 19x19 Go policy.
# API: policy(me, opponent, memory) -> ((row, col), memory)

N = 19
NN = N * N


def _pt1(r, c):
    """1-based row/col to flat 0-based index."""
    return (r - 1) * N + (c - 1)


def _transform_corner_point(r, c, corner):
    """Transform a top-left 1-based corner coordinate to another corner."""
    # corner order: 0=TL, 1=TR, 2=BL, 3=BR
    rr = r if corner in (0, 1) else (N + 1 - r)
    cc = c if corner in (0, 2) else (N + 1 - c)
    return rr, cc


def _make_geometry():
    neigh, diag, r2, inf = [], [], [], []
    weights = [0, 10, 6, 3, 1]  # Chebyshev-distance influence weights.

    for r in range(N):
        for c in range(N):
            ns = []
            if r > 0:
                ns.append((r - 1) * N + c)
            if r + 1 < N:
                ns.append((r + 1) * N + c)
            if c > 0:
                ns.append(r * N + c - 1)
            if c + 1 < N:
                ns.append(r * N + c + 1)
            neigh.append(tuple(ns))

            ds = []
            for dr in (-1, 1):
                for dc in (-1, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < N and 0 <= cc < N:
                        ds.append(rr * N + cc)
            diag.append(tuple(ds))

            near = []
            infl = []
            for dr in range(-4, 5):
                for dc in range(-4, 5):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < N and 0 <= cc < N:
                        d = max(abs(dr), abs(dc))
                        q = rr * N + cc
                        if d <= 2:
                            near.append(q)
                        if d <= 4:
                            infl.append((q, weights[d]))
            r2.append(tuple(near))
            inf.append(tuple(infl))

    return tuple(neigh), tuple(diag), tuple(r2), tuple(inf)


_NEIGH, _DIAG, _R2, _INF = _make_geometry()


def _make_position():
    # Values by distance from edge: first line bad, third/fourth lines good.
    line_scores = [-20, -7, 9, 13, 10, 7, 5, 3, 2, 2]

    corner_44 = {_pt1(*_transform_corner_point(4, 4, ci)) for ci in range(4)}
    corner_33 = {_pt1(*_transform_corner_point(3, 3, ci)) for ci in range(4)}
    corner_34 = set()
    for base in ((3, 4), (4, 3)):
        for ci in range(4):
            corner_34.add(_pt1(*_transform_corner_point(base[0], base[1], ci)))

    pos = []
    for r in range(N):
        for c in range(N):
            idx = r * N + c
            edge = min(r, c, N - 1 - r, N - 1 - c)
            s = float(line_scores[edge] if edge < len(line_scores) else 2)

            # Hoshi/star points.
            if r in (3, 9, 15) and c in (3, 9, 15):
                s += 8.0

            if idx in corner_44:
                s += 16.0
            elif idx in corner_33:
                s += 12.0
            elif idx in corner_34:
                s += 10.0

            # Side star points.
            if ((r in (3, 15) and c == 9) or
                    (c in (3, 15) and r == 9)):
                s += 5.0

            center_dist = abs(r - 9) + abs(c - 9)
            s += max(0.0, 4.0 - center_dist // 3)
            pos.append(s)
    return tuple(pos)


_POS = _make_position()

_OPENING_POINTS = [
    _pt1(4, 4), _pt1(16, 16), _pt1(4, 16), _pt1(16, 4),
    _pt1(10, 10),
    _pt1(4, 10), _pt1(16, 10), _pt1(10, 4), _pt1(10, 16),
    _pt1(3, 3), _pt1(17, 17), _pt1(3, 17), _pt1(17, 3),
    _pt1(3, 10), _pt1(17, 10), _pt1(10, 3), _pt1(10, 17),
]
_OPEN_RANK = {p: i for i, p in enumerate(_OPENING_POINTS)}


def _make_corner_sets():
    claim = set()
    approaches = [set() for _ in range(4)]
    three_three = [None] * 4

    base_claim = [(3, 3), (3, 4), (4, 3), (4, 4)]
    base_approach = [(3, 6), (4, 6), (5, 5), (6, 3), (6, 4), (5, 3)]

    for ci in range(4):
        for r, c in base_claim:
            claim.add(_pt1(*_transform_corner_point(r, c, ci)))
        for r, c in base_approach:
            approaches[ci].add(_pt1(*_transform_corner_point(r, c, ci)))
        three_three[ci] = _pt1(*_transform_corner_point(3, 3, ci))

    return frozenset(claim), tuple(frozenset(x) for x in approaches), tuple(three_three)


_CORNER_CLAIM, _APPROACH_BY_CORNER, _THREE_THREE_BY_CORNER = _make_corner_sets()


def _make_point_corner():
    point_corner = []
    regions = [[] for _ in range(4)]

    for r in range(N):
        for c in range(N):
            ci = -1
            if r <= 6 and c <= 6:
                ci = 0
            elif r <= 6 and c >= 12:
                ci = 1
            elif r >= 12 and c <= 6:
                ci = 2
            elif r >= 12 and c >= 12:
                ci = 3
            p = r * N + c
            point_corner.append(ci)
            if ci != -1:
                regions[ci].append(p)

    return tuple(point_corner), tuple(tuple(x) for x in regions)


_POINT_CORNER, _CORNER_REGIONS = _make_point_corner()


def _build_board(me, opponent):
    b = [0] * NN
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            b[(r - 1) * N + (c - 1)] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            p = (r - 1) * N + (c - 1)
            if b[p] == 0:
                b[p] = -1
    return b


def _hash_board(b):
    # -1 -> 0, 0 -> 1, 1 -> 2
    return bytes((v + 1 for v in b))


def _collect_groups(b):
    visited = [False] * NN
    gids = [-1] * NN
    groups = []

    for p, val in enumerate(b):
        if val == 0 or visited[p]:
            continue

        gid = len(groups)
        stack = [p]
        visited[p] = True
        gids[p] = gid
        stones = []
        libs = set()

        while stack:
            x = stack.pop()
            stones.append(x)
            for nb in _NEIGH[x]:
                nv = b[nb]
                if nv == 0:
                    libs.add(nb)
                elif nv == val and not visited[nb]:
                    visited[nb] = True
                    gids[nb] = gid
                    stack.append(nb)

        groups.append({
            "color": val,
            "stones": stones,
            "libs": libs,
            "size": len(stones),
            "adj": set(),
        })

    # Opposing group adjacencies.
    for p, val in enumerate(b):
        if val == 0:
            continue
        gp = gids[p]
        for nb in _NEIGH[p]:
            if b[nb] == -val:
                groups[gp]["adj"].add(gids[nb])

    return groups, gids


def _compute_influence(b):
    own = [0] * NN
    opp = [0] * NN

    for p, val in enumerate(b):
        if val == 0:
            continue
        arr = own if val == 1 else opp
        for q, w in _INF[p]:
            arr[q] += w

    return own, opp


def _corner_counts(b):
    out = []
    for region in _CORNER_REGIONS:
        own = opp = 0
        for p in region:
            if b[p] == 1:
                own += 1
            elif b[p] == -1:
                opp += 1
        out.append((own, opp))
    return tuple(out)


def _is_eyeish(p, color, b):
    # Off-board edges count as friendly boundaries.
    for nb in _NEIGH[p]:
        if b[nb] != color:
            return False
    return True


def _eye_badness(p, color, b):
    bad = 0
    for d in _DIAG[p]:
        if b[d] == -color:
            bad += 1
    return bad


def _coerce_seen(raw):
    if isinstance(raw, set):
        return raw
    if raw is None:
        return set()
    try:
        return set(raw)
    except Exception:
        return set()


def _effect_for_move(p, b, groups, gids, seen, last_hash):
    if b[p] != 0:
        return None

    own_adj = set()
    opp_adj = set()
    captured = set()
    empty_adj = 0
    friend_adj = 0
    enemy_adj = 0

    for nb in _NEIGH[p]:
        v = b[nb]
        if v == 0:
            empty_adj += 1
        elif v == 1:
            friend_adj += 1
            own_adj.add(gids[nb])
        else:
            enemy_adj += 1
            og = gids[nb]
            opp_adj.add(og)
            if len(groups[og]["libs"]) == 1:
                captured.add(og)

    # Suicide test. If not capturing, the placed/connected group needs a liberty.
    if not captured and empty_adj == 0:
        ok = False
        for g in own_adj:
            if len(groups[g]["libs"]) > 1:
                ok = True
                break
        if not ok:
            return None

    libs = set()
    for nb in _NEIGH[p]:
        if b[nb] == 0:
            libs.add(nb)

    for g in own_adj:
        libs.update(groups[g]["libs"])
    libs.discard(p)

    captured_count = 0
    if captured:
        for g in captured:
            captured_count += groups[g]["size"]
            # Only captured stones directly adjacent to the new connected group
            # become liberties of that new group.
            for s in groups[g]["stones"]:
                for nb in _NEIGH[s]:
                    if nb == p or (b[nb] == 1 and gids[nb] in own_adj):
                        libs.add(s)
                        break

    result_libs = len(libs)
    if result_libs == 0:
        return None

    result_size = 1 + sum(groups[g]["size"] for g in own_adj)

    h = None
    if last_hash is not None or seen:
        rb = b.copy()
        rb[p] = 1
        for g in captured:
            for s in groups[g]["stones"]:
                rb[s] = 0
        h = _hash_board(rb)
        if h == last_hash or h in seen:
            return None

    return {
        "p": p,
        "own_adj": own_adj,
        "opp_adj": opp_adj,
        "captured": captured,
        "capture_count": captured_count,
        "libs": result_libs,
        "size": result_size,
        "hash": h,
        "friend_adj": friend_adj,
        "enemy_adj": enemy_adj,
        "empty_adj": empty_adj,
    }


def _result_board(b, effect, groups):
    rb = b.copy()
    p = effect["p"]
    rb[p] = 1
    for g in effect["captured"]:
        for s in groups[g]["stones"]:
            rb[s] = 0
    return rb


def _score_move(p, b, groups, gids, e, own_inf, opp_inf,
                stage, corner_info, max_own_atari, last_opp):
    r, c = divmod(p, N)

    near2_own = near2_opp = 0
    for q in _R2[p]:
        v = b[q]
        if v == 1:
            near2_own += 1
        elif v == -1:
            near2_opp += 1

    # Positional/opening value.
    if stage < 70:
        pos_mult = 2.0
    elif stage < 160:
        pos_mult = 1.15
    else:
        pos_mult = 0.8

    score = _POS[p] * pos_mult
    early = max(0.0, (70.0 - stage) / 70.0)
    opening_scale = max(0.0, (55.0 - stage) / 55.0)

    rank = _OPEN_RANK.get(p)
    if rank is not None and opening_scale > 0:
        score += (500.0 - 13.0 * rank) * opening_scale

    # Tactical terms.
    tactical = False
    saved_big = 0
    capture_count = e["capture_count"]

    for g in e["captured"]:
        s = groups[g]["size"]
        score += 850.0 + 190.0 * s
        if s >= 3:
            score += 160.0 * s
        tactical = True

        # Capturing a surrounding opponent group may save adjacent own groups.
        for ag in groups[g]["adj"]:
            if groups[ag]["color"] == 1:
                al = len(groups[ag]["libs"])
                az = groups[ag]["size"]
                if al == 1:
                    score += 900.0 + 180.0 * az
                    saved_big = max(saved_big, az)
                elif al == 2:
                    score += 120.0 + 35.0 * az

    for g in e["own_adj"]:
        gl = len(groups[g]["libs"])
        s = groups[g]["size"]
        if gl == 1:
            score += 1050.0 + 240.0 * s
            if s >= 3:
                score += 160.0 * s
            saved_big = max(saved_big, s)
            tactical = True
        elif gl == 2:
            score += 190.0 + 70.0 * s
        elif gl == 3:
            score += 45.0 + 18.0 * s

    for g in e["opp_adj"]:
        if g in e["captured"]:
            continue
        gl = len(groups[g]["libs"])
        s = groups[g]["size"]
        if gl == 2:
            score += 320.0 + 105.0 * s
            tactical = True
        elif gl == 3:
            score += 75.0 + 28.0 * s
        elif gl == 4 and stage > 60:
            score += 20.0 + 8.0 * s

    # If a sizeable own group is in atari, moves that do not help are suspect.
    if max_own_atari > saved_big:
        m = min(max_own_atari, 30)
        score -= 380.0 + 115.0 * m
        if max_own_atari >= 3:
            score -= 60.0 * m

    # Opening corner logic.
    ci = _POINT_CORNER[p]
    if ci != -1 and stage < 90:
        ownc, oppc = corner_info[ci]
        if ownc == 0 and oppc == 0:
            if p in _CORNER_CLAIM:
                score += 170.0 * early + 45.0
            else:
                score += 20.0 * early
        elif ownc == 0 and oppc > 0:
            if p in _APPROACH_BY_CORNER[ci]:
                score += 130.0 * early + 25.0
            if p == _THREE_THREE_BY_CORNER[ci] and stage > 22:
                score += 80.0 + 30.0 * min(1.0, (stage - 22.0) / 60.0)
        elif ownc > 0 and oppc == 0 and stage < 50 and not tactical:
            if near2_own > 0:
                score -= 35.0

    # Shape/connect/cut.
    own_groups = len(e["own_adj"])
    opp_groups = len(e["opp_adj"])

    if own_groups >= 2:
        score += 170.0 * (own_groups - 1)
    elif own_groups == 1:
        score += 24.0

    if opp_groups >= 2:
        score += 115.0 * (opp_groups - 1)

    if e["friend_adj"] and e["enemy_adj"]:
        score += 35.0

    for d in _DIAG[p]:
        if b[d] == 1:
            score += 9.0
        elif b[d] == -1:
            score += 4.0

    # Liberties and self-atari avoidance.
    libs = e["libs"]
    result_size = e["size"]
    score += 13.0 * min(libs, 8)

    if libs == 1:
        score -= 1750.0 + 70.0 * min(result_size, 25)
        if capture_count <= 1:
            score -= 1050.0
    elif libs == 2:
        score -= 160.0 + 25.0 * min(result_size, 10)
        if e["enemy_adj"] and own_inf[p] < opp_inf[p]:
            score -= 80.0
    elif libs >= 4:
        score += 30.0

    # Influence: prefer relevant boundary/extension points, not useless fills.
    owni = own_inf[p]
    oppi = opp_inf[p]
    if stage < 80:
        score += 0.55 * owni + 0.35 * oppi + 0.22 * min(owni, oppi)
    else:
        score += 0.70 * owni + 0.65 * oppi + 0.45 * min(owni, oppi)

    if not tactical:
        if owni > oppi * 3 + 25:
            score -= 45.0 + 0.25 * (owni - oppi)
        if oppi > owni * 3 + 30 and libs <= 3:
            score -= 70.0 + 0.20 * (oppi - owni)

    # Avoid premature contact/overconcentration in the opening.
    if stage < 65 and not tactical:
        if e["friend_adj"] > 0:
            score -= 25.0 * e["friend_adj"]
        if e["enemy_adj"] > 0 and e["friend_adj"] == 0:
            score -= 95.0 + 20.0 * e["enemy_adj"]
        near_total = near2_own + near2_opp
        if near_total > 5:
            score -= 10.0 * (near_total - 5)

    # Do not fill own eyes unless there is a strong tactical reason.
    if _is_eyeish(p, 1, b):
        penalty = 2600.0
        if _eye_badness(p, 1, b) == 0:
            penalty += 1200.0
        if capture_count or saved_big:
            penalty *= 0.35
        score -= penalty

    # Small local-response bias near the opponent's last detected move.
    if last_opp is not None:
        lr, lc = divmod(last_opp, N)
        d = max(abs(r - lr), abs(c - lc))
        if d == 1:
            score += 35.0
        elif d == 2:
            score += 20.0
        elif d == 3:
            score += 8.0

    # Deterministic tiny tie-breaker.
    score += ((p * 1315423911 + stage * 2654435761) & 255) * 0.0001
    return score


def _fallback_move(me, opponent, memory):
    mem = memory if isinstance(memory, dict) else {}
    b = _build_board(me, opponent)

    used = set()
    for p in list(_OPENING_POINTS) + list(range(NN)):
        if p in used:
            continue
        used.add(p)
        if b[p] != 0:
            continue
        # Having an adjacent empty point guarantees non-suicide and cannot be
        # an immediate ko recapture in normal ko shape.
        for nb in _NEIGH[p]:
            if b[nb] == 0:
                return ((p // N + 1, p % N + 1), mem)

    return ((0, 0), mem)


def _policy_impl(me, opponent, memory):
    if not isinstance(memory, dict):
        memory = {}

    b = _build_board(me, opponent)
    stones_on_board = sum(1 for x in b if x != 0)

    turns = memory.get("_turns", 0)
    if not isinstance(turns, int):
        turns = 0

    # If memory is accidentally reused across games, reset on tiny new board.
    if stones_on_board <= 1 and turns > 4:
        memory = {}
        turns = 0

    stage = max(stones_on_board, 2 * turns)
    current_hash = _hash_board(b)
    last_after = memory.get("_after_hash")

    curr_opp_positions = tuple(i for i, v in enumerate(b) if v == -1)
    last_opp = None
    prev_opp = memory.get("_opp_after")
    if prev_opp is not None:
        try:
            prev_set = set(prev_opp)
            curr_set = set(curr_opp_positions)
            diff = curr_set - prev_set
            if len(diff) == 1:
                last_opp = next(iter(diff))
        except Exception:
            last_opp = None

    opponent_passed = (last_after is not None and last_after == current_hash)

    seen = _coerce_seen(memory.get("_seen"))
    seen.add(current_hash)

    groups, gids = _collect_groups(b)
    own_inf, opp_inf = _compute_influence(b)
    corner_info = _corner_counts(b)

    max_own_atari = 0
    for g in groups:
        if g["color"] == 1 and len(g["libs"]) == 1:
            if g["size"] > max_own_atari:
                max_own_atari = g["size"]

    best_p = None
    best_e = None
    best_score = -10 ** 100

    for p, val in enumerate(b):
        if val != 0:
            continue
        e = _effect_for_move(p, b, groups, gids, seen, last_after)
        if e is None:
            continue

        sc = _score_move(
            p, b, groups, gids, e, own_inf, opp_inf,
            stage, corner_info, max_own_atari, last_opp
        )
        if sc > best_score:
            best_score = sc
            best_p = p
            best_e = e

    do_pass = False
    if best_p is None:
        do_pass = True
    else:
        # Pass only when moves are clearly harmful or when the board is very late.
        if best_score < -3500:
            do_pass = True
        elif stones_on_board > 320 and best_score < -50:
            do_pass = True
        elif opponent_passed and stage > 220 and best_score < 40:
            do_pass = True

    if do_pass:
        action = (0, 0)
        after_hash = current_hash
        opp_after = curr_opp_positions
    else:
        action = (best_p // N + 1, best_p % N + 1)
        rb = _result_board(b, best_e, groups)
        after_hash = best_e["hash"] if best_e["hash"] is not None else _hash_board(rb)
        opp_after = tuple(i for i, v in enumerate(rb) if v == -1)

    seen.add(after_hash)
    if len(seen) > 1800:
        seen = {current_hash, after_hash}

    memory["_seen"] = seen
    memory["_after_hash"] = after_hash
    memory["_opp_after"] = opp_after
    memory["_turns"] = turns + 1
    memory["_last_total"] = stones_on_board

    return action, memory


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Broad safety wrapper: never fail to return a legal pass/fallback move.
    try:
        return _policy_impl(me, opponent, memory)
    except Exception:
        return _fallback_move(me, opponent, memory)
