
import random

N = 19
NN = N * N
EMPTY = 0
ME = 1
OPP = 2

# Neighbors, coordinates, line numbers.
NEI = []
LINE = [0] * NN
for r in range(N):
    for c in range(N):
        i = r * N + c
        ns = []
        if r > 0:
            ns.append((r - 1) * N + c)
        if r < N - 1:
            ns.append((r + 1) * N + c)
        if c > 0:
            ns.append(r * N + c - 1)
        if c < N - 1:
            ns.append(r * N + c + 1)
        NEI.append(tuple(ns))
        LINE[i] = min(r, N - 1 - r, c, N - 1 - c) + 1

_rng = random.Random(0xC0FFEE)
ZME = [(_rng.getrandbits(64) or 1) for _ in range(NN)]
ZOPP = [(_rng.getrandbits(64) or 1) for _ in range(NN)]
JITTER = [(_rng.random() - 0.5) * 0.10 for _ in range(NN)]

# Positional opening table: reward 3rd/4th-line corner points and side stars,
# discourage 1st/2nd-line moves early.
_key_bonus = {}

def _add_key(r, c, val):
    s = {
        (r, c), (r, N + 1 - c), (N + 1 - r, c), (N + 1 - r, N + 1 - c),
        (c, r), (c, N + 1 - r), (N + 1 - c, r), (N + 1 - c, N + 1 - r),
    }
    for a, b in s:
        if 1 <= a <= N and 1 <= b <= N:
            i = (a - 1) * N + (b - 1)
            if val > _key_bonus.get(i, -1.0e100):
                _key_bonus[i] = val

for args in [
    (4, 4, 10.0), (3, 4, 9.0), (3, 3, 6.0),
    (5, 4, 5.0), (3, 5, 4.0), (4, 6, 3.0), (3, 6, 2.0),
    (4, 10, 3.0), (10, 10, 2.0), (5, 5, 1.0),
]:
    _add_key(*args)

BASE_LINE = (-8.0, -2.5, 5.0, 6.2, 4.0, 2.5, 1.4, 0.7, 0.2, 0.0)
POS = [0.0] * NN
for i in range(NN):
    POS[i] = BASE_LINE[LINE[i] - 1] + _key_bonus.get(i, 0.0)

# Influence kernel, Manhattan distance 1..4.
INFL_OFF = []
for dr in range(-4, 5):
    for dc in range(-4, 5):
        d = abs(dr) + abs(dc)
        if 1 <= d <= 4:
            w = (4.0, 2.0, 1.0, 0.45)[d - 1]
            INFL_OFF.append((dr, dc, w))


def _analyze(b):
    comp = [-1] * NN
    g_color = []
    g_size = []
    g_members = []
    g_libcnt = []
    for i in range(NN):
        col = b[i]
        if col != EMPTY and comp[i] < 0:
            gid = len(g_color)
            comp[i] = gid
            stack = [i]
            members = []
            libs = set()
            while stack:
                x = stack.pop()
                members.append(x)
                for n in NEI[x]:
                    bn = b[n]
                    if bn == col:
                        if comp[n] < 0:
                            comp[n] = gid
                            stack.append(n)
                    elif bn == EMPTY:
                        libs.add(n)
            g_color.append(col)
            g_members.append(members)
            g_size.append(len(members))
            g_libcnt.append(len(libs))
    return comp, g_color, g_size, g_members, g_libcnt


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    out_memory = dict(memory) if isinstance(memory, dict) else {}
    hist = set(out_memory.get("hist", ()))

    b = [EMPTY] * NN
    h = 0
    my_idx = []
    opp_idx = []

    for r, c in me:
        i = (r - 1) * N + (c - 1)
        if 0 <= i < NN:
            b[i] = ME
            h ^= ZME[i]
            my_idx.append(i)
    for r, c in opponent:
        i = (r - 1) * N + (c - 1)
        if 0 <= i < NN:
            b[i] = OPP
            h ^= ZOPP[i]
            opp_idx.append(i)

    # Store current position too; this is a strict repetition guard and is safe.
    hist.add(h)

    stones = len(my_idx) + len(opp_idx)
    comp, g_color, g_size, g_members, g_libcnt = _analyze(b)

    # Influence map: positive is good for us.
    infl = [0.0] * NN
    for i in my_idx:
        r, c = divmod(i, N)
        for dr, dc, w in INFL_OFF:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < N and 0 <= cc < N:
                infl[rr * N + cc] += w
    for i in opp_idx:
        r, c = divmod(i, N)
        for dr, dc, w in INFL_OFF:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < N and 0 <= cc < N:
                infl[rr * N + cc] -= w

    opening = max(0.0, 1.0 - stones / 50.0)
    pos_weight = 0.55 + 2.0 * opening
    infl_weight = 0.34 if stones < 140 else 0.24
    late = max(0.0, min(1.0, (stones - 170.0) / 60.0))

    mark = [0] * NN
    stamp = 0

    best_idx = -1
    best_score = -1.0e100
    best_hash = 0

    for idx in range(NN):
        if b[idx] != EMPTY:
            continue

        friend = []
        opp = []
        fseen = set()
        oseen = set()
        empty_adj = 0
        captured = []
        cap_groups = 0

        for n in NEI[idx]:
            bn = b[n]
            if bn == EMPTY:
                empty_adj += 1
            elif bn == ME:
                gid = comp[n]
                if gid not in fseen:
                    fseen.add(gid)
                    friend.append(gid)
            else:
                gid = comp[n]
                if gid not in oseen:
                    oseen.add(gid)
                    opp.append(gid)
                    # Since idx is empty and adjacent to this opponent group, idx is
                    # one of its liberties. One placed stone can only remove that
                    # liberty, so only one-liberty adjacent groups are captured.
                    if g_libcnt[gid] == 1:
                        cap_groups += 1
                        captured.extend(g_members[gid])

        h2 = h ^ ZME[idx]
        if captured:
            for s in captured:
                h2 ^= ZOPP[s]
        if h2 in hist:
            continue

        nb = b.copy()
        nb[idx] = ME
        if captured:
            for s in captured:
                nb[s] = EMPTY

        # Measure the resulting own group exactly enough: full size, liberties
        # counted exactly up to 8 (9 means "many").
        stamp += 1
        stack = [idx]
        mark[idx] = stamp
        own_size = 0
        libs = set()
        over = False
        while stack:
            x = stack.pop()
            own_size += 1
            for n in NEI[x]:
                bn = nb[n]
                if bn == ME:
                    if mark[n] != stamp:
                        mark[n] = stamp
                        stack.append(n)
                elif bn == EMPTY:
                    if not over:
                        libs.add(n)
                        if len(libs) > 8:
                            over = True
        new_libs = 9 if over else len(libs)
        if new_libs == 0:
            continue

        cap_count = len(captured)

        pv = POS[idx]
        if late > 0.0:
            ln = LINE[idx]
            if ln == 1:
                pv += 5.0 * late
            elif ln == 2:
                pv += 2.5 * late

        score = pv * pos_weight + infl_weight * infl[idx] + 2.0 * (new_libs if new_libs < 4 else 4) + JITTER[idx]

        if friend:
            if len(friend) > 1:
                score += 12.0 * (len(friend) - 1) + 0.5 * min(20, sum(g_size[g] for g in friend))

            max_lib = max(g_libcnt[g] for g in friend)
            sum_sz = sum(g_size[g] for g in friend)
            if cap_count == 0:
                if new_libs < max_lib:
                    score -= (max_lib - new_libs) * 8.0 + 1.2 * own_size
                elif new_libs > max_lib:
                    score += min(4, new_libs - max_lib) * 3.0 + 0.15 * sum_sz

            for g in friend:
                gl = g_libcnt[g]
                gs = g_size[g]
                if gl == 1:
                    if cap_count > 0 or new_libs > 1:
                        score += 52.0 + 7.0 * gs + 4.0 * (new_libs if new_libs < 4 else 4)
                    else:
                        score -= 100.0 + 10.0 * gs
                elif gl == 2:
                    if new_libs >= 3:
                        score += 10.0 + 1.5 * gs
                    elif cap_count == 0 and new_libs < gl:
                        score -= 15.0 + 2.0 * gs
                elif gl == 3 and new_libs > gl:
                    score += 4.0 + 0.6 * gs
        else:
            if opp and cap_count == 0:
                if new_libs >= 3:
                    score += 6.0 + 1.5 * new_libs
                else:
                    score -= 22.0

        if cap_count:
            score += 40.0 * cap_count + 20.0 * cap_groups
            if cap_count >= 4:
                score += 15.0 + 3.0 * cap_count
            if cap_count >= 10:
                score += 60.0

        ataris = 0
        for g in opp:
            gl = g_libcnt[g]
            if gl == 1:
                continue  # already counted as captured
            after = gl - 1
            gs = g_size[g]
            if after == 1:
                ataris += 1
                score += 26.0 + 4.5 * gs + (12.0 if gs >= 8 else 0.0)
            elif after == 2:
                score += 6.0 + 1.2 * gs
            elif after == 3:
                score += 1.5 + 0.4 * gs
        if ataris > 1:
            score += 18.0 * (ataris - 1)

        # Self-atari / snapback control. A one-stone capture leaving a one-stone
        # group in atari is normally a ko take, so it is not treated like a bad
        # snapback; larger bad trades are heavily penalized.
        if new_libs == 1:
            if cap_count == 1 and own_size == 1:
                score += 12.0
            elif cap_count >= own_size and cap_count > 0:
                score += 8.0 * (cap_count - own_size + 1)
            else:
                score -= 125.0 + 34.0 * own_size - 16.0 * cap_count

        # Do not fill solid eyes/territory for no reason.
        if cap_count == 0 and not opp and friend:
            if empty_adj == 0:
                score -= 120.0
            elif all(g_libcnt[g] >= 4 for g in friend) and new_libs <= 2:
                score -= 45.0

        # After the opening, avoid totally isolated low-influence moves unless the
        # positional table has a strong reason for them.
        if cap_count == 0 and not friend and not opp and stones > 25 and infl[idx] < 1.0:
            score -= 8.0

        if score > best_score:
            best_score = score
            best_idx = idx
            best_hash = h2

    if best_idx < 0:
        out_memory["hist"] = list(hist)
        return (0, 0), out_memory

    hist.add(best_hash)
    out_memory["hist"] = list(hist)
    return (best_idx // N + 1, best_idx % N + 1), out_memory
