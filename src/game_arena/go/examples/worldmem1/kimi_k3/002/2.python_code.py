
import random

N = 19
ME = 1
OPP = 2
OFF = -1
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _build_pos():
    t = {}
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            d = min(r - 1, c - 1, N - r, N - c)
            if d == 0:
                v = -3.0
            elif d == 1:
                v = 0.5
            elif d == 2:
                v = 7.0
            elif d == 3:
                v = 9.0
            elif d == 4:
                v = 7.0
            else:
                v = 5.0
            if r in (4, 10, 16) and c in (4, 10, 16):
                v += 1.5
            if r in (3, 17) and c in (3, 17):
                v += 1.0
            t[(r, c)] = v
    return t


POS = _build_pos()

STAR = [(4, 4), (4, 16), (16, 4), (16, 16),
        (3, 4), (4, 3), (3, 16), (4, 17),
        (16, 3), (17, 4), (16, 17), (17, 16),
        (3, 3), (3, 17), (17, 3), (17, 17),
        (10, 4), (4, 10), (10, 16), (16, 10),
        (3, 10), (10, 3), (10, 17), (17, 10), (10, 10)]


def _compute_groups(b):
    gid = [[0] * (N + 2) for _ in range(N + 2)]
    groups = [None]
    g = 0
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            col = b[r][c]
            if (col == ME or col == OPP) and gid[r][c] == 0:
                g += 1
                stones = []
                libs = set()
                stack = [(r, c)]
                gid[r][c] = g
                while stack:
                    x, y = stack.pop()
                    stones.append((x, y))
                    for dx, dy in DIRS:
                        nx, ny = x + dx, y + dy
                        v = b[nx][ny]
                        if v == 0:
                            libs.add((nx, ny))
                        elif v == col and gid[nx][ny] == 0:
                            gid[nx][ny] = g
                            stack.append((nx, ny))
                groups.append((col, stones, libs))
    return gid, groups


def _try(b, gid, groups, r, c):
    """Simulate playing (r,c). Return None if suicide, else move features."""
    own_g = set()
    opp_g = set()
    for dx, dy in DIRS:
        v = b[r + dx][c + dy]
        if v == ME:
            own_g.add(gid[r + dx][c + dy])
        elif v == OPP:
            opp_g.add(gid[r + dx][c + dy])
    captured = set()
    cap_cells = []
    for g in opp_g:
        if len(groups[g][2]) == 1:  # (r,c) is the last liberty
            captured.add(g)
            cap_cells.extend(groups[g][1])
    b[r][c] = ME
    for (x, y) in cap_cells:
        b[x][y] = 0
    seen = {(r, c)}
    stack = [(r, c)]
    libs = set()
    while stack:
        x, y = stack.pop()
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            v = b[nx][ny]
            if v == 0:
                libs.add((nx, ny))
            elif v == ME and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))
    b[r][c] = 0
    for (x, y) in cap_cells:
        b[x][y] = OPP
    if not libs:
        return None
    return libs, len(seen), len(cap_cells), cap_cells, own_g, opp_g, captured


def _score(b, groups, r, c, libs, size, ncap, own_g, opp_g, captured):
    nlib = len(libs)
    s = POS[(r, c)]
    if ncap:
        s += 18.0 * ncap + 4.0 * ncap * ncap
        if nlib == 1:
            s -= 3.0 * size  # snapback / recapture risk
    saved = 0
    weak = 0
    for g in own_g:
        gl = groups[g][2]
        gs = len(groups[g][1])
        lg = len(gl)
        if lg == 1:
            saved += gs
        elif lg == 2:
            weak += gs
    if saved and nlib >= 2:
        s += 16.0 + 5.0 * saved
    if weak and nlib >= 3:
        s += 2.0 + 0.3 * weak
    for g in opp_g:
        if g in captured:
            continue
        gl = groups[g][2]
        gs = len(groups[g][1])
        after = len(gl) - 1
        if after == 1:
            s += 7.0 + 1.5 * gs   # atari
        elif after == 2:
            s += 1.0              # pressure
    if ncap == 0:
        if nlib == 1:
            s -= 30.0             # self-atari
        elif nlib == 2:
            s -= 2.0
    k = len(own_g)
    if k >= 2:
        s += 4.0 * (k - 1)        # connecting own groups
    if len(opp_g) >= 2:
        s += 2.0 * (len(opp_g) - 1)  # cutting / splitting
    if opp_g:
        s += 1.5                  # contact fight
    if ncap == 0 and not saved and not weak:
        emp = 0
        opp = 0
        for dx, dy in DIRS:
            v = b[r + dx][c + dy]
            if v == 0:
                emp += 1
            elif v == OPP:
                opp += 1
        if emp == 0 and opp == 0:
            # surrounded by own stones: likely filling own eye
            od = 0
            td = 0
            for dx, dy in DIAGS:
                v = b[r + dx][c + dy]
                if v == OFF:
                    continue
                td += 1
                if v == OPP:
                    od += 1
            if od == 0 or (td >= 4 and od <= 1):
                s -= 45.0
            else:
                s -= 12.0
    return s


def _apply(b, r, c):
    b[r][c] = ME
    for dx, dy in DIRS:
        nx, ny = r + dx, c + dy
        if b[nx][ny] == OPP:
            stack = [(nx, ny)]
            seen = {(nx, ny)}
            has_lib = False
            while stack:
                x, y = stack.pop()
                for ddx, ddy in DIRS:
                    px, py = x + ddx, y + ddy
                    v = b[px][py]
                    if v == 0:
                        has_lib = True
                    elif v == OPP and (px, py) not in seen:
                        seen.add((px, py))
                        stack.append((px, py))
            if not has_lib:
                for (x, y) in seen:
                    b[x][y] = 0


def _encode(b):
    return bytes(b[r][c] for r in range(1, N + 1) for c in range(1, N + 1))


def _opening(b):
    corners = [(4, 4), (4, 16), (16, 4), (16, 16),
               (3, 4), (4, 3), (3, 16), (4, 17),
               (16, 3), (17, 4), (16, 17), (17, 16),
               (3, 3), (3, 17), (17, 3), (17, 17)]
    best = None
    bestv = -1.0
    for (r, c) in corners:
        if b[r][c] != 0:
            continue
        r0, r1 = (1, 9) if r <= 10 else (11, 19)
        c0, c1 = (1, 9) if c <= 10 else (11, 19)
        occ = 0
        for x in range(r0, r1 + 1):
            for y in range(c0, c1 + 1):
                if b[x][y] != 0:
                    occ += 1
        if occ == 0:
            v = 100.0
        elif occ == 1:
            v = 60.0
        else:
            v = 20.0
        if r in (4, 16) and c in (4, 16):
            v += 5.0
        v += random.random() * 3.0
        if v > bestv:
            bestv = v
            best = (r, c)
    return best


def policy(me, opponent, memory):
    if memory is None:
        memory = {}
    b = [[OFF] * (N + 2) for _ in range(N + 2)]
    for r in range(1, N + 1):
        br = b[r]
        for c in range(1, N + 1):
            br[c] = 0
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            b[r][c] = ME
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            b[r][c] = OPP
    total = len(me) + len(opponent)

    gid, groups = _compute_groups(b)

    my_atari = False
    opp_atari = False
    for g in groups[1:]:
        if len(g[2]) == 1:
            if g[0] == ME:
                my_atari = True
            else:
                opp_atari = True

    move = None
    if total < 8 and not my_atari and not opp_atari:
        move = _opening(b)

    if move is None:
        near = [[False] * (N + 2) for _ in range(N + 2)]
        any_stone = False
        for r in range(1, N + 1):
            for c in range(1, N + 1):
                if b[r][c] == ME or b[r][c] == OPP:
                    any_stone = True
                    for dr in (-2, -1, 0, 1, 2):
                        nr = r + dr
                        if nr < 1 or nr > N:
                            continue
                        nrow = near[nr]
                        for dc in (-2, -1, 0, 1, 2):
                            nc = c + dc
                            if 1 <= nc <= N:
                                nrow[nc] = True
        cands = []
        for r in range(1, N + 1):
            br = b[r]
            nrow = near[r]
            for c in range(1, N + 1):
                if br[c] == 0 and nrow[c]:
                    cands.append((r, c))
        if total < 40:
            for (r, c) in STAR:
                if b[r][c] == 0 and not near[r][c]:
                    cands.append((r, c))
        if not cands:
            if not any_stone:
                move = (10, 10)
            else:
                for r in range(1, N + 1):
                    for c in range(1, N + 1):
                        if b[r][c] == 0:
                            cands.append((r, c))
        if move is None:
            if not cands:
                memory['prev'] = _encode(b)
                return (0, 0), memory
            prev = memory.get('prev')
            best = None
            best_s = -1e18
            for (r, c) in cands:
                res = _try(b, gid, groups, r, c)
                if res is None:
                    continue
                libs, size, ncap, cap_cells, own_g, opp_g, captured = res
                if ncap == 1 and size == 1 and len(libs) == 1 and prev is not None:
                    # possible ko: would this recreate the previous position?
                    b[r][c] = ME
                    x, y = cap_cells[0]
                    b[x][y] = 0
                    cur = _encode(b)
                    b[r][c] = 0
                    b[x][y] = OPP
                    if cur == prev:
                        continue
                s = _score(b, groups, r, c, libs, size, ncap, own_g, opp_g, captured)
                s += random.random() * 1.2
                if s > best_s:
                    best_s = s
                    best = (r, c)
            if best is None or best_s < 1.0:
                memory['prev'] = _encode(b)
                return (0, 0), memory
            move = best

    _apply(b, move[0], move[1])
    memory['prev'] = _encode(b)
    return move, memory
