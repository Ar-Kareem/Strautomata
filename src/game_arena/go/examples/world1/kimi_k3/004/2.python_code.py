
import time

N = 19
NN = N * N
EMPTY = 0
ME = 1
OPP = 2

# Precomputed orthogonal neighbors, using zero-based internal indices.
NEI = []
for i in range(NN):
    r, c = divmod(i, N)
    ns = []
    if r > 0:
        ns.append(i - N)
    if r < N - 1:
        ns.append(i + N)
    if c > 0:
        ns.append(i - 1)
    if c < N - 1:
        ns.append(i + 1)
    NEI.append(tuple(ns))

FUSEKI = {}
def _set_points(points, value):
    for p in points:
        FUSEKI[p] = value

_set_points(((4, 4), (4, 16), (16, 4), (16, 16)), 120.0)
_set_points(((4, 3), (3, 4), (4, 17), (3, 16),
             (16, 3), (17, 4), (16, 17), (17, 16)), 112.0)
_set_points(((3, 3), (3, 17), (17, 3), (17, 17)), 100.0)
_set_points(((5, 4), (4, 5), (5, 16), (4, 15),
             (15, 4), (16, 5), (15, 16), (16, 15),
             (5, 15), (15, 5), (5, 6), (6, 5),
             (5, 14), (6, 15), (14, 5), (15, 6),
             (14, 15), (15, 14)), 78.0)
_set_points(((4, 10), (10, 4), (10, 16), (16, 10)), 65.0)
_set_points(((3, 10), (10, 3), (10, 17), (17, 10),
             (5, 10), (10, 5), (10, 15), (15, 10)), 48.0)
SIDE_HOSHI = {(4, 10), (10, 4), (10, 16), (16, 10)}
SIDE_3 = {(3, 10), (10, 3), (10, 17), (17, 10)}


def collect_group(b, start):
    color = b[start]
    stack = [start]
    seen = {start}
    stones = []
    libs = set()
    while stack:
        x = stack.pop()
        stones.append(x)
        for y in NEI[x]:
            v = b[y]
            if v == EMPTY:
                libs.add(y)
            elif v == color and y not in seen:
                seen.add(y)
                stack.append(y)
    return color, stones, libs


def compute_groups(b):
    gid = [-1] * NN
    groups = []
    for i, v in enumerate(b):
        if v != EMPTY and gid[i] < 0:
            gn = len(groups)
            stack = [i]
            gid[i] = gn
            stones = []
            libs = set()
            while stack:
                x = stack.pop()
                stones.append(x)
                for y in NEI[x]:
                    vy = b[y]
                    if vy == EMPTY:
                        libs.add(y)
                    elif vy == v and gid[y] < 0:
                        gid[y] = gn
                        stack.append(y)
            groups.append({"color": v, "stones": stones, "size": len(stones), "libs": libs})
    return gid, groups


def play(b, i, color):
    if b[i] != EMPTY:
        return None
    opp = 3 - color
    b2 = b.copy()
    b2[i] = color

    captured = []
    processed = set()
    for y in NEI[i]:
        if b2[y] == opp and y not in processed:
            _, stones, libs = collect_group(b2, y)
            processed.update(stones)
            if not libs:
                captured.extend(stones)
                for x in stones:
                    b2[x] = EMPTY

    _, my_stones, my_libs = collect_group(b2, i)
    if not my_libs:
        return None

    opp_after = []
    done = set()
    for y in NEI[i]:
        if b2[y] == opp and y not in done:
            _, stones, libs = collect_group(b2, y)
            done.update(stones)
            opp_after.append((len(stones), len(libs)))

    return b2, len(captured), captured, len(my_stones), my_libs, opp_after


def eye_like(b, i, color):
    ns = NEI[i]
    if len(ns) < 2:
        return False
    for y in ns:
        if b[y] != color:
            return False
    return True


def positional(i, total):
    r = i // N + 1
    c = i % N + 1

    if total < 18:
        v = FUSEKI.get((r, c))
        if v is not None:
            return v

    dr = min(r - 1, N - r)
    dc = min(c - 1, N - c)
    a = dr if dr < dc else dc
    b = dc if dr < dc else dr

    if a == 0:
        val = -25.0 if total < 150 else -3.0
    elif a == 1:
        val = -4.0 if total < 120 else 2.0
    elif a == 2:
        val = 9.0
    elif a == 3:
        val = 10.0
    elif a == 4:
        val = 6.0
    else:
        val = 3.0

    if total < 80:
        cd = min((r - 1) + (c - 1),
                 (r - 1) + (N - c),
                 (N - r) + (c - 1),
                 (N - r) + (N - c))
        val += max(0, 18 - 2 * cd)
        if (r, c) in SIDE_HOSHI:
            val += 8.0
        elif (r, c) in SIDE_3:
            val += 5.0
        if a >= 4:
            val -= 3.0
    else:
        val += max(0, 5 - (abs(r - 10) + abs(c - 10)) // 3)

    return val


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    start = time.time()

    b = [EMPTY] * NN
    for r, c in me:
        b[(r - 1) * N + (c - 1)] = ME
    for r, c in opponent:
        b[(r - 1) * N + (c - 1)] = OPP

    total = len(me) + len(opponent)
    if total == 0:
        return (4, 4)

    gid, groups = compute_groups(b)
    empties = [i for i, v in enumerate(b) if v == EMPTY]
    if not empties:
        return (0, 0)

    our_atari_sizes = [g["size"] for g in groups if g["color"] == ME and len(g["libs"]) == 1]
    max_our_atari = max(our_atari_sizes) if our_atari_sizes else 0

    best_i = -1
    best_score = -10 ** 18

    for k, i in enumerate(empties):
        if (k & 31) == 0 and best_i >= 0 and time.time() - start > 0.90:
            break

        adj_f = set()
        adj_o = set()
        for y in NEI[i]:
            v = b[y]
            if v == ME:
                adj_f.add(gid[y])
            elif v == OPP:
                adj_o.add(gid[y])

        res = play(b, i, ME)
        if res is None:
            continue
        _b2, capn, captured, gsize, glibs, opp_after = res
        glen = len(glibs)

        # A one-stone capture leaving a one-stone/one-liberty shape may be an
        # illegal ko recapture when history is unavailable; avoid it.
        if capn == 1 and gsize == 1 and glen == 1 and captured[0] in glibs:
            continue

        score = positional(i, total)
        score += ((i * 1315423911 + total * 2654435761) & 1023) * 1e-7

        saved_any = False
        saved_max = 0
        adj_f_size = 0

        for gi in adj_f:
            g = groups[gi]
            sz = g["size"]
            l = len(g["libs"])
            adj_f_size += sz
            if l == 1:
                if capn > 0 or glen > 1:
                    saved_any = True
                    if sz > saved_max:
                        saved_max = sz
                    score += 185.0 + 28.0 * sz + 10.0 * glen
                else:
                    score -= 140.0
            elif l == 2:
                if capn > 0 or glen > 2:
                    score += 38.0 + 6.0 * sz + 2.0 * glen
                else:
                    score -= 18.0
            elif l == 3:
                score += 7.0 + 0.8 * sz

        if len(adj_f) >= 2:
            score += 15.0 * (len(adj_f) - 1) + min(18, adj_f_size)
        else:
            score += min(5, adj_f_size)

        relieved = set()
        if capn:
            for x in captured:
                for y in NEI[x]:
                    if b[y] == ME:
                        gi = gid[y]
                        if gi not in relieved:
                            relieved.add(gi)
                            g = groups[gi]
                            l = len(g["libs"])
                            if l == 1:
                                saved_any = True
                                if g["size"] > saved_max:
                                    saved_max = g["size"]
                                score += 95.0 + 20.0 * g["size"]
                            elif l == 2:
                                score += 22.0 + 4.0 * g["size"]

        if max_our_atari and saved_max < max_our_atari and capn < max_our_atari:
            score -= 95.0 + 18.0 * max_our_atari

        if capn:
            score += 70.0 + 30.0 * capn + 6.0 * capn * capn

        if glen == 1:
            if capn == 0:
                score -= 75.0 + 18.0 * gsize
            else:
                score -= 12.0 * gsize
        elif glen == 2 and capn == 0 and total < 150:
            score -= 8.0
        elif glen >= 4:
            score += min(8, glen - 2)

        if opp_after:
            contact_bonus = 0.0
            for osz, olibs in opp_after:
                if olibs == 1:
                    contact_bonus += 36.0 + 13.0 * osz
                elif olibs == 2:
                    contact_bonus += 5.0 + 2.0 * osz
                elif olibs == 3:
                    contact_bonus += 0.7 * osz
            score += contact_bonus
            if glen >= 3:
                score += 3.0 * len(opp_after)

        if len(adj_o) >= 2 and glen >= 2:
            score += 8.0 * (len(adj_o) - 1)

        if capn == 0 and not saved_any and eye_like(b, i, ME):
            score -= 95.0

        if score > best_score:
            best_score = score
            best_i = i

    if best_i < 0:
        return (0, 0)
    if total > 120 and best_score < -45.0:
        return (0, 0)
    return (best_i // N + 1, best_i % N + 1)
