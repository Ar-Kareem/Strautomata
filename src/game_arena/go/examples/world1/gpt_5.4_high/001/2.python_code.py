
N = 19
SIZE = N * N

GCOLOR = 0
GSTONES = 1
GLIBS = 2
GSIZE = 3
GNLIB = 4


def _idx(r: int, c: int) -> int:
    return (r - 1) * N + (c - 1)


ROWS = [i // N + 1 for i in range(SIZE)]
COLS = [i % N + 1 for i in range(SIZE)]
LINE = [min(ROWS[i], COLS[i], N + 1 - ROWS[i], N + 1 - COLS[i]) for i in range(SIZE)]
CENTER_DIST = [abs(ROWS[i] - 10) + abs(COLS[i] - 10) for i in range(SIZE)]

NEI = [[] for _ in range(SIZE)]
DIAG = [[] for _ in range(SIZE)]
LOCAL2 = [[] for _ in range(SIZE)]

for i in range(SIZE):
    r0 = ROWS[i] - 1
    c0 = COLS[i] - 1

    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        rr = r0 + dr
        cc = c0 + dc
        if 0 <= rr < N and 0 <= cc < N:
            NEI[i].append(rr * N + cc)

    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        rr = r0 + dr
        cc = c0 + dc
        if 0 <= rr < N and 0 <= cc < N:
            DIAG[i].append(rr * N + cc)

    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if dr == 0 and dc == 0:
                continue
            if abs(dr) + abs(dc) <= 2:
                rr = r0 + dr
                cc = c0 + dc
                if 0 <= rr < N and 0 <= cc < N:
                    LOCAL2[i].append(rr * N + cc)

CORNER_STARS = {
    _idx(4, 4), _idx(4, 16), _idx(16, 4), _idx(16, 16)
}
SIDE_STARS = {
    _idx(4, 10), _idx(10, 4), _idx(10, 16), _idx(16, 10)
}
CENTER_STAR = _idx(10, 10)


def _build_groups(board: list[int]):
    gid_of = [-1] * SIZE
    groups = []
    gid = 0

    for p in range(SIZE):
        color = board[p]
        if color == 0 or gid_of[p] != -1:
            continue

        stack = [p]
        gid_of[p] = gid
        stones = []
        libs = set()

        while stack:
            q = stack.pop()
            stones.append(q)
            for n in NEI[q]:
                v = board[n]
                if v == 0:
                    libs.add(n)
                elif v == color and gid_of[n] == -1:
                    gid_of[n] = gid
                    stack.append(n)

        groups.append((color, stones, libs, len(stones), len(libs)))
        gid += 1

    return gid_of, groups


def _eyeish(board: list[int], p: int, color: int) -> bool:
    # Simple "don't fill your own eye" detector.
    for n in NEI[p]:
        if board[n] != color:
            return False

    # Edge/corner: if all orthogonal neighbors are ours, it's usually eye-like enough.
    if len(NEI[p]) < 4:
        return True

    # Interior: allow at most one "bad" diagonal.
    bad = 0
    for d in DIAG[p]:
        if board[d] != color:
            bad += 1
    return bad <= 1


def _simulate_group_after_move(board: list[int], p: int, gid_of, groups):
    # Apply our move at p, capture adjacent opponent groups in atari,
    # then measure the resulting connected group's size and liberties.
    newb = board[:]
    newb[p] = 1

    seen_opp = set()
    for n in NEI[p]:
        if board[n] == -1:
            g = gid_of[n]
            if g not in seen_opp:
                seen_opp.add(g)
                grp = groups[g]
                if grp[GNLIB] == 1:
                    for s in grp[GSTONES]:
                        newb[s] = 0

    stack = [p]
    seen = {p}
    libs = set()
    size = 0

    while stack:
        q = stack.pop()
        size += 1
        for n in NEI[q]:
            v = newb[n]
            if v == 0:
                libs.add(n)
            elif v == 1 and n not in seen:
                seen.add(n)
                stack.append(n)

    return size, len(libs)


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [0] * SIZE
    occupied = []
    seen = set()

    # Load our stones.
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            p = _idx(r, c)
            if p not in seen:
                seen.add(p)
                board[p] = 1
                occupied.append(p)

    # Load opponent stones, ignoring invalid overlaps if any.
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            p = _idx(r, c)
            if p not in seen:
                seen.add(p)
                board[p] = -1
                occupied.append(p)

    total = len(occupied)
    gid_of, groups = _build_groups(board)
    small_occ = occupied if total < 10 else None

    best_key = None
    best_p = None

    for p in range(SIZE):
        if board[p] != 0:
            continue

        own_ids = set()
        opp_ids = set()
        adj_empty = 0

        for n in NEI[p]:
            v = board[n]
            if v == 0:
                adj_empty += 1
            elif v == 1:
                own_ids.add(gid_of[n])
            else:
                opp_ids.add(gid_of[n])

        captured = 0
        attack2 = 0
        attack3 = 0

        for g in opp_ids:
            grp = groups[g]
            sz = grp[GSIZE]
            nl = grp[GNLIB]
            if nl == 1:
                captured += sz
            elif nl == 2:
                attack2 += sz
            elif nl == 3:
                attack3 += sz

        # Legal if it has an adjacent empty, captures something,
        # or connects to a friendly group that has another liberty.
        if not (captured or adj_empty):
            merged_libs = set()
            for g in own_ids:
                merged_libs.update(groups[g][GLIBS])
            merged_libs.discard(p)
            if not merged_libs:
                continue

        saved = 0
        defend2 = 0
        defend3 = 0
        connect_size = 0

        for g in own_ids:
            grp = groups[g]
            sz = grp[GSIZE]
            nl = grp[GNLIB]
            connect_size += sz
            if nl == 1:
                saved += sz
            elif nl == 2:
                defend2 += sz
            elif nl == 3:
                defend3 += sz

        new_size, new_libs = _simulate_group_after_move(board, p, gid_of, groups)

        score = 0.0

        # Urgent tactics.
        score += 12000 * captured
        score += 14500 * saved
        score += 2600 * attack2
        score += 250 * attack3
        score += 1100 * defend2
        score += 120 * defend3

        # Shape: connect friends, cut enemies.
        if len(own_ids) >= 2:
            score += 500 * (len(own_ids) - 1)
            score += 45 * connect_size
        else:
            score += 20 * connect_size

        if len(opp_ids) >= 2:
            score += 300 * (len(opp_ids) - 1)

        # Prefer healthy resulting groups.
        score += 42 * new_libs
        score += 8 * new_size
        if new_libs >= 4:
            score += 80

        line = LINE[p]

        # Opening preferences.
        if total < 10:
            if p in CORNER_STARS:
                score += 260
            elif p in SIDE_STARS:
                score += 180
            elif p == CENTER_STAR:
                score += 140

            if line == 4:
                score += 120
            elif line == 3:
                score += 100
            elif line == 5:
                score += 70
            elif line == 2:
                score -= 80
            elif line == 1 and captured == 0 and saved == 0:
                score -= 250

            if small_occ:
                r0 = ROWS[p]
                c0 = COLS[p]
                nearest = 999
                for q in small_occ:
                    d = abs(r0 - ROWS[q]) + abs(c0 - COLS[q])
                    if d < nearest:
                        nearest = d

                if nearest <= 1:
                    score -= 180
                elif nearest == 2:
                    score -= 60
                else:
                    score += min(140, 8 * nearest)

        # Mid/late game: prefer locally relevant moves.
        else:
            local2 = 0
            for q in LOCAL2[p]:
                if board[q] != 0:
                    local2 += 1

            if local2 == 0 and captured == 0 and saved == 0:
                score -= 220
            else:
                score += 12 * local2

            if line == 1 and captured == 0 and saved == 0:
                score -= 90
            elif line == 2 and captured == 0 and saved == 0:
                score -= 15

        # Avoid filling our own eye unless tactically justified.
        if _eyeish(board, p, 1) and captured == 0 and saved == 0 and attack2 == 0:
            score -= 2400

        # Avoid self-atari / very cramped moves.
        if new_libs == 1:
            penalty = 4800 + 150 * new_size
            if captured or saved or attack2:
                penalty -= 2200
            score -= penalty
        elif new_libs == 2:
            score -= 180

        # Mild tiebreak toward the center.
        score -= 0.5 * CENTER_DIST[p]

        key = (
            score,
            captured,
            saved,
            attack2,
            new_libs,
            -CENTER_DIST[p],
            -p,
        )

        if best_key is None or key > best_key:
            best_key = key
            best_p = p

    if best_p is None:
        return (0, 0)

    # Very conservative late pass if everything remaining looks bad.
    if total > 300 and best_key[0] < -200:
        return (0, 0)

    return (ROWS[best_p], COLS[best_p])
