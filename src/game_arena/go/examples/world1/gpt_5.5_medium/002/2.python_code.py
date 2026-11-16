
# Go policy for a 19x19 board.
# Required API:
#     policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]

from collections import deque

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

STAR_POINTS = [
    (4, 4), (16, 16), (4, 16), (16, 4),
    (10, 10),
    (4, 10), (16, 10), (10, 4), (10, 16),
    (3, 4), (4, 3), (16, 17), (17, 16),
    (3, 16), (4, 17), (16, 3), (17, 4),
]


def _on_board(p):
    r, c = p
    return 1 <= r <= N and 1 <= c <= N


def _neighbors(p):
    r, c = p
    for dr, dc in DIRS:
        q = (r + dr, c + dc)
        if 1 <= q[0] <= N and 1 <= q[1] <= N:
            yield q


def _diag_neighbors(p):
    r, c = p
    for dr, dc in DIAGS:
        q = (r + dr, c + dc)
        if 1 <= q[0] <= N and 1 <= q[1] <= N:
            yield q


def _build_groups(stones, occupied):
    visited = set()
    groups = []
    group_id = {}

    for s in stones:
        if s in visited:
            continue

        gid = len(groups)
        stack = [s]
        visited.add(s)
        group_stones = set()
        liberties = set()

        while stack:
            x = stack.pop()
            group_stones.add(x)
            group_id[x] = gid

            for y in _neighbors(x):
                if y in stones:
                    if y not in visited:
                        visited.add(y)
                        stack.append(y)
                elif y not in occupied:
                    liberties.add(y)

        groups.append({
            "stones": group_stones,
            "libs": liberties,
            "size": len(group_stones),
        })

    return groups, group_id


def _move_info(p, me_set, opp_set, occupied, my_groups, my_gid, opp_groups, opp_gid):
    if p in occupied or not _on_board(p):
        return {"legal": False}

    adj_my = set()
    adj_opp = set()
    captured_gids = set()

    for q in _neighbors(p):
        if q in me_set:
            adj_my.add(my_gid[q])
        elif q in opp_set:
            gid = opp_gid[q]
            adj_opp.add(gid)
            if p in opp_groups[gid]["libs"] and len(opp_groups[gid]["libs"]) == 1:
                captured_gids.add(gid)

    capture_count = sum(opp_groups[g]["size"] for g in captured_gids)

    # Approximate liberties of the newly formed group after playing p.
    # This is exact enough for legality and robust for scoring.
    libs_after = set()

    for q in _neighbors(p):
        if q not in occupied:
            libs_after.add(q)

    for gid in adj_my:
        libs_after.update(my_groups[gid]["libs"])
    libs_after.discard(p)

    for gid in captured_gids:
        libs_after.update(opp_groups[gid]["stones"])

    legal = bool(libs_after)

    new_group_size = 1 + sum(my_groups[g]["size"] for g in adj_my)

    # Conservative ko-risk detector: single-stone capture by a lone stone
    # leaving exactly one liberty is the common immediate-ko shape.
    ko_risk = (
        capture_count == 1
        and new_group_size == 1
        and len(libs_after) == 1
    )

    return {
        "legal": legal,
        "adj_my": adj_my,
        "adj_opp": adj_opp,
        "captured_gids": captured_gids,
        "capture_count": capture_count,
        "libs_after": len(libs_after),
        "new_group_size": new_group_size,
        "ko_risk": ko_risk,
    }


def _eye_penalty(p, me_set, opp_set, capture_count):
    if capture_count:
        return 0

    # If every orthogonal on-board neighbor is friendly, this is probably
    # our own eye or half-eye; filling it is usually terrible.
    for q in _neighbors(p):
        if q not in me_set:
            return 0

    diag_opp = 0
    diag_empty = 0
    for q in _diag_neighbors(p):
        if q in opp_set:
            diag_opp += 1
        elif q not in me_set:
            diag_empty += 1

    # True-looking eye: very bad to fill.
    if diag_opp == 0:
        return -4200

    # False-eye-ish point: still often bad, but sometimes tactically relevant.
    return -1200


def _positional_score(p, turn):
    r, c = p
    edge = min(r, c, N + 1 - r, N + 1 - c)
    dr = min(r, N + 1 - r)
    dc = min(c, N + 1 - c)

    score = 0.0

    # Prefer classical 3rd/4th line development; avoid first line.
    if edge == 4:
        score += 42
    elif edge == 3:
        score += 36
    elif edge == 5:
        score += 22
    elif edge == 6:
        score += 10
    elif edge == 2:
        score -= 8
    elif edge == 1:
        score -= 45

    # Corners are largest in the opening.
    if dr <= 6 and dc <= 6:
        score += 28
        if dr in (3, 4) and dc in (3, 4):
            score += 30
        if turn < 80:
            score += 22
    elif dr <= 5 or dc <= 5:
        # Side development.
        score += 8
        if edge in (3, 4):
            score += 10

    # Center becomes more interesting later.
    if turn > 120:
        center_dist = abs(r - 10) + abs(c - 10)
        score += max(0, 18 - center_dist) * 0.8

    # Opening star-point preference.
    if turn < 70:
        for i, sp in enumerate(STAR_POINTS):
            d = abs(r - sp[0]) + abs(c - sp[1])
            if d == 0:
                score += 210 - 4 * i
                break
            elif d == 1:
                score += 22
            elif d == 2:
                score += 7

    return score


def _score_move(p, info, me_set, opp_set, my_groups, opp_groups, turn):
    r, c = p
    score = 0.0

    capture_count = info["capture_count"]
    libs = info["libs_after"]
    adj_my = info["adj_my"]
    adj_opp = info["adj_opp"]
    captured = info["captured_gids"]

    tactical = False

    # Captures are very valuable, especially larger captures.
    if capture_count:
        tactical = True
        score += 1150 * capture_count
        score += 100 * len(captured)
        score += 35 * min(libs, 10)

    # Save own adjacent groups in atari or low-liberty trouble.
    for gid in adj_my:
        g = my_groups[gid]
        glibs = len(g["libs"])
        size = g["size"]
        if glibs == 1 and p in g["libs"]:
            tactical = True
            score += 850 + 95 * size
        elif glibs == 2 and p in g["libs"]:
            score += 95 + 16 * size

    # Attack opponent groups.
    for gid in adj_opp:
        if gid in captured:
            continue
        g = opp_groups[gid]
        glibs = len(g["libs"])
        size = g["size"]
        if p in g["libs"]:
            if glibs == 2:
                tactical = True
                score += 260 + 38 * size
            elif glibs == 3:
                score += 70 + 12 * size
            elif glibs == 4:
                score += 18 + 4 * size

    # Connections and cuts.
    if len(adj_my) >= 2:
        score += 105 + 18 * len(adj_my)
        tactical = True
    elif len(adj_my) == 1:
        score += 20

    if len(adj_opp) >= 2:
        score += 65 + 12 * len(adj_opp)

    # Liberties / shape.
    score += 18 * min(libs, 8)
    if libs <= 1:
        if capture_count:
            score -= 220
        else:
            score -= 950
    elif libs == 2 and not tactical:
        score -= 120
    elif libs >= 5:
        score += 18

    # Avoid filling own eyes.
    score += _eye_penalty(p, me_set, opp_set, capture_count)

    # Positional fundamentals.
    score += _positional_score(p, turn)

    # Local influence. Cheap full scan is fine on 19x19.
    near_own_1 = 0
    near_opp_1 = 0
    nearest_any = 99

    for s in me_set:
        d = abs(r - s[0]) + abs(c - s[1])
        if d < nearest_any:
            nearest_any = d
        if d == 1:
            near_own_1 += 1
            score += 12
        elif d == 2:
            score += 10
        elif d == 3:
            score += 6
        elif d == 4:
            score += 3

    for s in opp_set:
        d = abs(r - s[0]) + abs(c - s[1])
        if d < nearest_any:
            nearest_any = d
        if d == 1:
            near_opp_1 += 1
            score += 7
        elif d == 2:
            score += 9
        elif d == 3:
            score += 5
        elif d == 4:
            score += 2

    # Unsupported contact is often bad unless tactical.
    if near_opp_1 and not near_own_1 and not tactical and libs <= 3:
        score -= 85

    # In the opening, avoid pointless shoulder-to-shoulder clumping.
    if turn < 80 and nearest_any == 1 and not tactical:
        score -= 28

    # Prefer not to make tiny over-concentrated moves early.
    if turn < 60 and near_own_1 >= 2 and not tactical:
        score -= 35

    # Deterministic tiny tie-breaker.
    score += ((r * 73856093) ^ (c * 19349663) ^ (turn * 83492791)) % 997 / 997.0

    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = {p for p in me if _on_board(p)}
    opp_set = {p for p in opponent if _on_board(p)}
    occupied = me_set | opp_set
    turn = len(me_set) + len(opp_set)

    my_groups, my_gid = _build_groups(me_set, occupied)
    opp_groups, opp_gid = _build_groups(opp_set, occupied)

    best_move = None
    best_score = -10**18

    best_nonko_move = None
    best_nonko_score = -10**18

    for r in range(1, N + 1):
        for c in range(1, N + 1):
            p = (r, c)
            if p in occupied:
                continue

            info = _move_info(
                p,
                me_set,
                opp_set,
                occupied,
                my_groups,
                my_gid,
                opp_groups,
                opp_gid,
            )

            if not info["legal"]:
                continue

            score = _score_move(
                p,
                info,
                me_set,
                opp_set,
                my_groups,
                opp_groups,
                turn,
            )

            if score > best_score:
                best_score = score
                best_move = p

            # Avoid likely immediate-ko recaptures if any other legal move exists.
            if not info["ko_risk"] and score > best_nonko_score:
                best_nonko_score = score
                best_nonko_move = p

    # No legal board move: pass.
    if best_move is None:
        return (0, 0)

    # Prefer non-ko-risk moves for safety.
    chosen = best_nonko_move if best_nonko_move is not None else None
    chosen_score = best_nonko_score if best_nonko_move is not None else -10**18

    # If every non-ko move is just filling our own eye, pass instead.
    if chosen is not None and chosen_score < -2500:
        return (0, 0)

    if chosen is not None:
        return chosen

    # If only likely-ko-risk moves exist, passing is always legal and avoids
    # possible illegal-ko disqualification.
    return (0, 0)
