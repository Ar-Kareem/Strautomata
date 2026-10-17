
import time

N = 19

NEI = {}
for r in range(1, N + 1):
    for c in range(1, N + 1):
        ns = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 1 <= nr <= N and 1 <= nc <= N:
                ns.append((nr, nc))
        NEI[(r, c)] = ns

OFF2 = [(dr, dc) for dr in range(-2, 3) for dc in range(-2, 3) if dr or dc]
OFF3 = [(dr, dc) for dr in range(-3, 4) for dc in range(-3, 4) if dr or dc]

OPENING_POINTS = set()
_patterns = [(4, 4), (3, 4), (4, 3), (5, 3), (3, 5), (4, 5), (5, 4),
             (3, 6), (6, 3), (4, 6), (6, 4), (3, 3), (5, 5)]
for x, y in _patterns:
    for p in ((x, y), (x, 20 - y), (20 - x, y), (20 - x, 20 - y)):
        if 1 <= p[0] <= N and 1 <= p[1] <= N:
            OPENING_POINTS.add(p)
OPENING_POINTS.update([(4, 10), (10, 4), (10, 16), (16, 10), (10, 10)])


def collect_group(b, start):
    color = b[start[0]][start[1]]
    stack = [start]
    seen = {start}
    stones = []
    libs = set()
    while stack:
        p = stack.pop()
        stones.append(p)
        for q in NEI[p]:
            v = b[q[0]][q[1]]
            if v == 0:
                libs.add(q)
            elif v == color and q not in seen:
                seen.add(q)
                stack.append(q)
    return stones, libs


def scan_groups(b):
    seen = set()
    groups = []
    gid = {}
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            color = b[r][c]
            if color and (r, c) not in seen:
                stones, libs = collect_group(b, (r, c))
                idx = len(groups)
                groups.append({
                    "color": color,
                    "stones": stones,
                    "libs": libs,
                    "size": len(stones),
                    "nlibs": len(libs),
                })
                for s in stones:
                    seen.add(s)
                    gid[s] = idx
    return groups, gid


def try_move(b, move, ko_point=None):
    """Temporarily play as color 1. Return capture/liberty info, or None if illegal."""
    r, c = move
    if move == ko_point or b[r][c] != 0:
        return None

    b[r][c] = 1
    captured = []
    processed = set()

    for q in NEI[move]:
        if b[q[0]][q[1]] == 2 and q not in processed:
            stones, libs = collect_group(b, q)
            processed.update(stones)
            if not libs:
                captured.extend(stones)

    if captured:
        for s in captured:
            b[s[0]][s[1]] = 0

    my_stones, my_libs = collect_group(b, move)
    ok = len(my_libs) > 0

    b[r][c] = 0
    for s in captured:
        b[s[0]][s[1]] = 2

    if not ok:
        return None
    return {
        "captured": captured,
        "n_cap": len(captured),
        "own_libs": len(my_libs),
        "own_size": len(my_stones),
    }


def corner_counts(me_set, opp_set):
    out = [[0, 0] for _ in range(4)]  # TL, TR, BL, BR: [mine, opponent]
    for col, ss in ((0, me_set), (1, opp_set)):
        for r, c in ss:
            if r <= 7 and c <= 7:
                i = 0
            elif r <= 7 and c >= 13:
                i = 1
            elif r >= 13 and c <= 7:
                i = 2
            elif r >= 13 and c >= 13:
                i = 3
            else:
                continue
            out[i][col] += 1
    return out


def pos_score(r, c, total, ccount):
    edge = min(r - 1, N - r, c - 1, N - c)
    if total < 55:
        table = (-90, -28, 7, 17, 9, 4)
    elif total < 155:
        table = (-38, -12, 3, 8, 4, 1)
    else:
        table = (-14, -5, 1, 3, 1, 0)
    s = table[edge] if edge < len(table) else table[-1]

    x = r if r <= 10 else 20 - r
    y = c if c <= 10 else 20 - c
    if x <= 8 and y <= 8:
        if x <= 7 and y <= 7:
            key = (0 if r <= 10 else 2) + (0 if c <= 10 else 1)
            myc, opc = ccount[key]

            if (x, y) == (4, 4):
                s += 34
            elif (x, y) in ((3, 4), (4, 3)):
                s += 28
            elif (x, y) in ((5, 3), (3, 5), (4, 5), (5, 4)):
                s += 20
            elif (x, y) == (3, 3):
                s += 13
            elif (x, y) == (5, 5):
                s += 8
            elif (x, y) in ((3, 6), (6, 3)):
                s += 14
            elif (x, y) in ((4, 6), (6, 4)):
                s += 10

            if x <= 2 or y <= 2:
                s -= 20
            if myc == 0 and opc == 0:
                s += 16
            elif myc == 0 and opc == 1:
                s += 12
            elif myc == 1 and opc == 0:
                s += 4
            elif myc == 0 and opc >= 2:
                s += 7

    if total < 90 and (r, c) in ((4, 10), (10, 4), (10, 16), (16, 10)):
        s += 13
    if total < 35 and (r, c) == (10, 10):
        s += 10
    return s


def near_counts(b, p, rad=2):
    r, c = p
    my = opp = 0
    for dr in range(-rad, rad + 1):
        nr = r + dr
        if nr < 1 or nr > N:
            continue
        for dc in range(-rad, rad + 1):
            if dr == 0 and dc == 0:
                continue
            nc = c + dc
            if 1 <= nc <= N:
                v = b[nr][nc]
                if v == 1:
                    my += 1
                elif v == 2:
                    opp += 1
    return my, opp


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    memory = memory or {}
    start = time.time()
    deadline = start + 0.92

    me_set = {tuple(p) for p in me if 1 <= p[0] <= N and 1 <= p[1] <= N}
    opp_set = {tuple(p) for p in opponent if 1 <= p[0] <= N and 1 <= p[1] <= N}
    opp_set -= me_set

    b = [[0] * (N + 1) for _ in range(N + 1)]
    for r, c in me_set:
        b[r][c] = 1
    for r, c in opp_set:
        b[r][c] = 2

    total = len(me_set) + len(opp_set)

    # Simple-ko avoidance: if the opponent just captured exactly one stone,
    # forbid immediately recreating the stored post-move position.
    ko_point = None
    try:
        after_me = {tuple(p) for p in memory.get("after_me", [])}
        after_opp = {tuple(p) for p in memory.get("after_opp", [])}
        lost = after_me - me_set
        gained = opp_set - after_opp
        if len(lost) == 1 and len(gained) == 1:
            lp = next(iter(lost))
            gp = next(iter(gained))
            if gp in NEI.get(lp, ()) and b[lp[0]][lp[1]] == 0:
                ko_point = lp
    except Exception:
        ko_point = None

    groups, gid = scan_groups(b)

    my_lib1, my_lib2 = {}, {}
    opp_lib1, opp_lib2, opp_lib3 = {}, {}, {}
    critical_stones = set()
    critical_size = 0

    for i, g in enumerate(groups):
        libs = g["libs"]
        if g["color"] == 1:
            if g["nlibs"] == 1:
                critical_size += g["size"]
                critical_stones.update(g["stones"])
                for p in libs:
                    my_lib1.setdefault(p, []).append(i)
            elif g["nlibs"] == 2:
                for p in libs:
                    my_lib2.setdefault(p, []).append(i)
        else:
            if g["nlibs"] == 1:
                for p in libs:
                    opp_lib1.setdefault(p, []).append(i)
            elif g["nlibs"] == 2:
                for p in libs:
                    opp_lib2.setdefault(p, []).append(i)
            elif g["nlibs"] == 3:
                for p in libs:
                    opp_lib3.setdefault(p, []).append(i)

    critical_zone = set(my_lib1)
    for s in critical_stones:
        for q in NEI[s]:
            if b[q[0]][q[1]] == 0:
                critical_zone.add(q)

    ccount = corner_counts(me_set, opp_set)

    cand = set()
    if total == 0:
        cand.update(p for p in OPENING_POINTS if b[p[0]][p[1]] == 0)
    else:
        offs = OFF3 if total < 14 else OFF2
        for r, c in me_set | opp_set:
            for dr, dc in offs:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= N and 1 <= nc <= N and b[nr][nc] == 0:
                    cand.add((nr, nc))
        if total < 90:
            cand.update(p for p in OPENING_POINTS if b[p[0]][p[1]] == 0)
        for g in groups:
            if g["nlibs"] <= 4:
                cand.update(p for p in g["libs"] if b[p[0]][p[1]] == 0)

    if not cand:
        cand.update((r, c) for r in range(1, N + 1) for c in range(1, N + 1) if b[r][c] == 0)

    def cheap_key(p):
        k = pos_score(p[0], p[1], total, ccount)
        if p in opp_lib1:
            k += 100000 + 1000 * sum(groups[i]["size"] for i in opp_lib1[p])
        if p in my_lib1:
            k += 90000 + 900 * sum(groups[i]["size"] for i in my_lib1[p])
        if critical_size and p in critical_zone:
            k += 50000 + 1000 * critical_size
        if p in opp_lib2:
            k += 30000 + 300 * sum(groups[i]["size"] for i in opp_lib2[p])
        if p in my_lib2:
            k += 8000
        return k

    def eval_score(p, sim, adj_my, adj_opp, my_near, opp_near):
        r, c = p
        ncap = sim["n_cap"]
        libs = sim["own_libs"]
        tactical = (
            ncap > 0
            or p in my_lib1
            or p in opp_lib1
            or p in opp_lib2
            or (critical_size and p in critical_zone)
        )

        sc = 0.0
        if ncap:
            sc += 320.0 * ncap + 95.0 * ncap * ncap
            if ncap == 1 and libs == 1:
                sc -= 540.0
            elif libs == 1:
                sc -= 140.0
            if critical_size and (p in critical_zone or ncap >= 2):
                sc += 120.0 + 55.0 * critical_size
        else:
            if libs == 1:
                sc -= 900.0
                if adj_opp:
                    sc -= 60.0 * len(adj_opp)
            elif libs == 2 and total > 45 and opp_near >= my_near:
                sc -= 45.0
            else:
                sc += min(28.0, 4.0 * libs)

        if critical_size:
            addresses = False
            if p in my_lib1 and (ncap or libs >= 2):
                addresses = True
            if ncap and p in critical_zone:
                addresses = True
            if p in critical_zone and libs >= 3:
                addresses = True
            if not addresses:
                sc -= 160.0 + 60.0 * critical_size

        if p in my_lib1:
            for gi in my_lib1[p]:
                g = groups[gi]
                if ncap or libs >= 2:
                    sc += 260.0 + 70.0 * g["size"]
                else:
                    sc -= 220.0 + 45.0 * g["size"]

        if p in my_lib2 and libs >= 3:
            sc += min(140.0, sum(16.0 * groups[gi]["size"] for gi in my_lib2[p]))

        if p in opp_lib2 and ncap == 0:
            for gi in opp_lib2[p]:
                g = groups[gi]
                bonus = 52.0 + 15.0 * g["size"]
                if libs >= 3:
                    sc += bonus
                elif libs == 2:
                    sc += 0.45 * bonus
                else:
                    sc -= 120.0 + 12.0 * g["size"]

        if p in opp_lib3 and ncap == 0 and libs >= 3:
            sc += min(50.0, sum(4.0 * groups[gi]["size"] for gi in opp_lib3[p]))

        if len(adj_my) >= 2:
            sc += 34.0 * (len(adj_my) - 1)
            sc += min(130.0, 6.0 * sum(groups[i]["size"] for i in adj_my))
            if any(groups[i]["nlibs"] <= 2 for i in adj_my):
                sc += 95.0

        if len(adj_opp) >= 2:
            if len(adj_my) or libs >= 3 or ncap:
                sc += 22.0 * (len(adj_opp) - 1) + min(70.0, 4.0 * sum(groups[i]["size"] for i in adj_opp))
            else:
                sc -= 70.0 * (len(adj_opp) - 1)

        # Do not fill solid own territory/eyes late unless there is a tactical reason.
        if total > 150 and ncap == 0 and opp_near == 0 and my_near >= 6 and p not in my_lib1 and p not in my_lib2:
            sc -= 45.0 + 9.0 * (my_near - 5)

        ps = pos_score(r, c, total, ccount)
        if tactical:
            sc += (0.35 if total < 55 else 0.12) * ps
        else:
            sc += (1.25 if total < 55 else (0.55 if total < 155 else 0.22)) * ps
            if total < 60:
                sc += 1.15 * my_near - 0.70 * opp_near
                if opp_near > my_near + 3:
                    sc -= 5.0 * (opp_near - my_near - 3)
            else:
                sc += 2.1 * my_near - 3.0 * opp_near
                if opp_near > my_near + 2:
                    sc -= 18.0 * (opp_near - my_near - 2)
            if total < 85:
                if r == 1 or r == N or c == 1 or c == N:
                    sc -= 75.0
                elif r == 2 or r == 18 or c == 2 or c == 18:
                    sc -= 28.0
        return sc

    best_move = None
    best_cap = []
    best_score = -10**18

    for p in sorted(cand, key=cheap_key, reverse=True):
        if time.time() > deadline and best_move is not None:
            break
        sim = try_move(b, p, ko_point)
        if sim is None:
            continue

        adj_my = set()
        adj_opp = set()
        for q in NEI[p]:
            v = b[q[0]][q[1]]
            if v == 1:
                adj_my.add(gid[q])
            elif v == 2:
                adj_opp.add(gid[q])
        my_near, opp_near = near_counts(b, p, 2)

        sc = eval_score(p, sim, adj_my, adj_opp, my_near, opp_near)
        if sc > best_score:
            best_score = sc
            best_move = p
            best_cap = sim["captured"]

    if best_move is None:
        pts = sorted(
            ((r, c) for r in range(1, N + 1) for c in range(1, N + 1) if b[r][c] == 0),
            key=lambda p: pos_score(p[0], p[1], total, ccount),
            reverse=True,
        )
        for p in pts:
            sim = try_move(b, p, ko_point)
            if sim is not None:
                best_move = p
                best_cap = sim["captured"]
                best_score = 0.0
                break

    if best_move is None:
        out = {
            "after_me": [list(p) for p in sorted(me_set)],
            "after_opp": [list(p) for p in sorted(opp_set)],
            "last_move": [0, 0],
        }
        return (0, 0), out

    # Very late: pass rather than fill solid own territory for a negative reason.
    if total >= 250 and best_score < -25 and not best_cap:
        out = {
            "after_me": [list(p) for p in sorted(me_set)],
            "after_opp": [list(p) for p in sorted(opp_set)],
            "last_move": [0, 0],
        }
        return (0, 0), out

    new_me = me_set | {best_move}
    new_opp = opp_set - set(best_cap)
    out = {
        "after_me": [list(p) for p in sorted(new_me)],
        "after_opp": [list(p) for p in sorted(new_opp)],
        "last_move": [best_move[0], best_move[1]],
    }
    return best_move, out
