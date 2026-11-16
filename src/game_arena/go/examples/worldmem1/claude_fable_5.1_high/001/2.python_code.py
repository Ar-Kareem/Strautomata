
import random
import time

N = 19
NBR = ((-1, 0), (1, 0), (0, -1), (0, 1))
_rng = random.Random(20240601)
ZOB = [[[0, _rng.getrandbits(63), _rng.getrandbits(63)] for _ in range(N + 2)] for _ in range(N + 2)]
LINE = (-6.0, -2.5, 2.0, 2.5, 1.0)
W3 = {1: 4.0, 2: 2.0, 3: 1.0}
OFFS3 = [(dr, dc) for dr in range(-3, 4) for dc in range(-3, 4) if 0 < abs(dr) + abs(dc) <= 3]
OFFS2 = [(dr, dc) for dr in range(-2, 3) for dc in range(-2, 3) if abs(dr) + abs(dc) <= 2]
T_NEUTRAL = 3.0
READ_BUDGET = 150


def get_group(board, r, c):
    color = board[r][c]
    stones = {(r, c)}
    stack = [(r, c)]
    libs = set()
    while stack:
        r0, c0 = stack.pop()
        for dr, dc in NBR:
            nr, nc = r0 + dr, c0 + dc
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color:
                p = (nr, nc)
                if p not in stones:
                    stones.add(p)
                    stack.append(p)
    return stones, libs


def copy_board(board):
    return [row[:] for row in board]


def sim_play(board, r, c, color):
    if board[r][c] != 0:
        return None
    board[r][c] = color
    opp = 3 - color
    captured = []
    for dr, dc in NBR:
        nr, nc = r + dr, c + dc
        if board[nr][nc] == opp:
            st, lb = get_group(board, nr, nc)
            if not lb:
                for s in st:
                    board[s[0]][s[1]] = 0
                captured.extend(st)
    st, lb = get_group(board, r, c)
    if not lb:
        board[r][c] = 0
        return None
    return captured


def defender_escapes(board, gr, gc, defender, depth, budget, deadline):
    if depth > 50 or budget[0] <= 0 or time.time() > deadline:
        return True
    budget[0] -= 1
    if board[gr][gc] != defender:
        return False
    stones, libs = get_group(board, gr, gc)
    if len(libs) >= 2:
        return True
    if len(libs) == 0:
        return False
    attacker = 3 - defender
    options = set(libs)
    seen = set()
    for (sr, sc) in stones:
        for dr, dc in NBR:
            nr, nc = sr + dr, sc + dc
            if board[nr][nc] == attacker and (nr, nc) not in seen:
                ast, alb = get_group(board, nr, nc)
                seen |= ast
                if len(alb) == 1:
                    options.add(next(iter(alb)))
    for (r, c) in options:
        b2 = copy_board(board)
        caps = sim_play(b2, r, c, defender)
        if caps is None:
            continue
        st2, lb2 = get_group(b2, gr, gc)
        if len(lb2) >= 3:
            return True
        if len(lb2) == 2:
            if not attacker_captures(b2, gr, gc, attacker, depth + 1, budget, deadline):
                return True
    return False


def attacker_captures(board, gr, gc, attacker, depth, budget, deadline):
    if depth > 50 or budget[0] <= 0 or time.time() > deadline:
        return False
    budget[0] -= 1
    defender = 3 - attacker
    if board[gr][gc] != defender:
        return True
    stones, libs = get_group(board, gr, gc)
    if len(libs) >= 3:
        return False
    if len(libs) <= 1:
        return True
    for (r, c) in libs:
        b2 = copy_board(board)
        caps = sim_play(b2, r, c, attacker)
        if caps is None:
            continue
        st, lb = get_group(b2, r, c)
        if len(lb) <= 1 and not caps:
            continue
        if not defender_escapes(b2, gr, gc, defender, depth + 1, budget, deadline):
            return True
    return False


def policy(me, opponent, memory):
    t0 = time.time()
    deadline = t0 + 0.55
    board = [[3] * (N + 2) for _ in range(N + 2)]
    for r in range(1, N + 1):
        row = board[r]
        for c in range(1, N + 1):
            row[c] = 0
    me = [tuple(p) for p in me]
    opponent = [tuple(p) for p in opponent]
    for (r, c) in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r][c] = 1
    for (r, c) in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r][c] = 2

    curhash = 0
    for (r, c) in me:
        curhash ^= ZOB[r][c][1]
    for (r, c) in opponent:
        curhash ^= ZOB[r][c][2]
    hist = list(memory.get('hist', [])) if isinstance(memory, dict) else []
    histset = set(hist)
    histset.add(curhash)

    last_opp = None
    prev_opp = memory.get('prev_opp') if isinstance(memory, dict) else None
    if prev_opp is not None:
        ps = set(tuple(p) for p in prev_opp)
        new = [p for p in opponent if p not in ps]
        if len(new) == 1:
            last_opp = new[0]

    # groups
    gid = [[0] * (N + 2) for _ in range(N + 2)]
    groups = [None]
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            v = board[r][c]
            if v in (1, 2) and gid[r][c] == 0:
                st, lb = get_group(board, r, c)
                idx = len(groups)
                for (sr, sc) in st:
                    gid[sr][sc] = idx
                groups.append((v, st, lb))

    # empty regions
    reg_id = [[0] * (N + 2) for _ in range(N + 2)]
    regions = [None]
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == 0 and reg_id[r][c] == 0:
                idx = len(regions)
                stack = [(r, c)]
                reg_id[r][c] = idx
                size = 0
                colors = set()
                while stack:
                    r0, c0 = stack.pop()
                    size += 1
                    for dr, dc in NBR:
                        nr, nc = r0 + dr, c0 + dc
                        v = board[nr][nc]
                        if v == 0:
                            if reg_id[nr][nc] == 0:
                                reg_id[nr][nc] = idx
                                stack.append((nr, nc))
                        elif v in (1, 2):
                            colors.add(v)
                regions.append((size, colors))

    # influence
    INF = [[0.0] * (N + 2) for _ in range(N + 2)]
    for (r, c) in me:
        for dr, dc in OFFS3:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= N and 1 <= nc <= N:
                INF[nr][nc] += W3[abs(dr) + abs(dc)]
    for (r, c) in opponent:
        for dr, dc in OFFS3:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= N and 1 <= nc <= N:
                INF[nr][nc] -= W3[abs(dr) + abs(dc)]
    NEU = [[0.0] * (N + 2) for _ in range(N + 2)]
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == 0:
                a = abs(INF[r][c])
                if a < T_NEUTRAL:
                    NEU[r][c] = (T_NEUTRAL - a) / T_NEUTRAL
    TERR = [[0.0] * (N + 2) for _ in range(N + 2)]
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == 0:
                s = 0.0
                for dr, dc in OFFS2:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= N and 1 <= nc <= N:
                        s += NEU[nr][nc]
                TERR[r][c] = s

    # ---------- tactical reading ----------
    save_moves = {}
    kill_moves = {}
    defend_moves = {}

    def capture_points_adjacent(stones, enemy):
        pts = set()
        for (sr, sc) in stones:
            for dr, dc in NBR:
                nr, nc = sr + dr, sc + dc
                if board[nr][nc] == enemy:
                    og = gid[nr][nc]
                    if len(groups[og][2]) == 1:
                        pts.add(next(iter(groups[og][2])))
        return pts

    # C: my groups in atari
    my_atari = [g for g in range(1, len(groups)) if groups[g][0] == 1 and len(groups[g][2]) == 1]
    my_atari.sort(key=lambda g: -len(groups[g][1]))
    for g in my_atari:
        if time.time() > deadline:
            break
        color, stones, libs = groups[g]
        gr, gc = next(iter(stones))
        options = set(libs) | capture_points_adjacent(stones, 2)
        for (r, c) in options:
            if time.time() > deadline:
                break
            b2 = copy_board(board)
            caps = sim_play(b2, r, c, 1)
            if caps is None:
                continue
            st2, lb2 = get_group(b2, gr, gc)
            ok = False
            if len(lb2) >= 3:
                ok = True
            elif len(lb2) == 2:
                ok = not attacker_captures(b2, gr, gc, 2, 0, [READ_BUDGET], deadline)
            if ok:
                val = 8 * len(stones) + 10
                if val > save_moves.get((r, c), 0):
                    save_moves[(r, c)] = val

    # B: opponent groups with two liberties -> ladder kill?
    opp2 = [g for g in range(1, len(groups)) if groups[g][0] == 2 and len(groups[g][2]) == 2]
    opp2.sort(key=lambda g: -len(groups[g][1]))
    for g in opp2:
        if time.time() > deadline:
            break
        color, stones, libs = groups[g]
        gr, gc = next(iter(stones))
        for (r, c) in libs:
            if time.time() > deadline:
                break
            b2 = copy_board(board)
            caps = sim_play(b2, r, c, 1)
            if caps is None:
                continue
            st, lb = get_group(b2, r, c)
            if len(lb) <= 1 and not caps:
                continue
            if b2[gr][gc] != 2:
                continue
            if not defender_escapes(b2, gr, gc, 2, 0, [READ_BUDGET], deadline):
                val = 10 * len(stones) + 12
                if val > kill_moves.get((r, c), 0):
                    kill_moves[(r, c)] = val

    # D: my groups with two liberties threatened by ladder
    my2 = [g for g in range(1, len(groups)) if groups[g][0] == 1 and len(groups[g][2]) == 2]
    my2.sort(key=lambda g: -len(groups[g][1]))
    for g in my2:
        if time.time() > deadline:
            break
        color, stones, libs = groups[g]
        gr, gc = next(iter(stones))
        if attacker_captures(board, gr, gc, 2, 0, [READ_BUDGET], deadline):
            options = set(libs) | capture_points_adjacent(stones, 2)
            for (r, c) in options:
                if time.time() > deadline:
                    break
                b2 = copy_board(board)
                caps = sim_play(b2, r, c, 1)
                if caps is None:
                    continue
                st2, lb2 = get_group(b2, gr, gc)
                ok = False
                if len(lb2) >= 3:
                    ok = True
                elif len(lb2) == 2:
                    ok = not attacker_captures(b2, gr, gc, 2, 0, [READ_BUDGET], deadline)
                if ok:
                    val = 6 * len(stones) + 5
                    if val > defend_moves.get((r, c), 0):
                        defend_moves[(r, c)] = val

    # ---------- scoring ----------
    best = None
    bestscore = -1e9
    rnd = random.Random(curhash & 0xFFFFFFFF)
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] != 0:
                continue
            adj_own = set()
            adj_opp = set()
            empties = 0
            libs = set()
            for dr, dc in NBR:
                nr, nc = r + dr, c + dc
                v = board[nr][nc]
                if v == 0:
                    empties += 1
                    libs.add((nr, nc))
                elif v == 1:
                    adj_own.add(gid[nr][nc])
                elif v == 2:
                    adj_opp.add(gid[nr][nc])
            size = 1
            for g in adj_own:
                libs |= groups[g][2]
                size += len(groups[g][1])
            libs.discard((r, c))
            captured = [g for g in adj_opp if len(groups[g][2]) == 1]
            ncap = 0
            newhash = curhash ^ ZOB[r][c][1]
            if captured:
                newstones = {(r, c)}
                for g in adj_own:
                    newstones |= groups[g][1]
                for g in captured:
                    for (sr, sc) in groups[g][1]:
                        ncap += 1
                        newhash ^= ZOB[sr][sc][2]
                        for dr, dc in NBR:
                            if (sr + dr, sc + dc) in newstones:
                                libs.add((sr, sc))
                                break
            L = len(libs)
            if L == 0 and ncap == 0:
                continue
            if ncap and newhash in histset:
                continue

            s = 0.0
            pt = (r, c)
            if ncap > 0:
                s += 15 + 10 * ncap
            if L == 1 and ncap == 0:
                s -= 25 + 6 * size
            elif L == 1:
                s -= 4
            elif L == 2:
                s -= 1.5
            else:
                s += 0.6 * min(L, 5)

            s += save_moves.get(pt, 0) + kill_moves.get(pt, 0) + defend_moves.get(pt, 0)

            for g in adj_own:
                gl = len(groups[g][2])
                gs = len(groups[g][1])
                if gl == 1:
                    if pt not in save_moves and (L >= 2 or ncap > 0):
                        s += 1.0
                elif gl == 2 and L >= 3:
                    s += 3 + 0.5 * min(gs, 10)
            if len(adj_own) >= 2:
                s += 2.5

            for g in adj_opp:
                if g in captured:
                    continue
                gl = len(groups[g][2])
                gs = len(groups[g][1])
                after = gl - 1
                if after == 1:
                    if pt not in kill_moves:
                        s += 2 + 0.7 * gs
                elif after == 2:
                    s += 1.5 + 0.3 * gs
                else:
                    s += 0.5

            if empties == 0 and not adj_opp and ncap == 0:
                s -= 30

            rd = min(r - 1, N - r)
            cd = min(c - 1, N - c)
            d = min(rd, cd)
            s += LINE[min(d, 4)]
            terr = TERR[r][c]
            s += 2.0 * terr
            infp = INF[r][c]
            if infp > 8:
                s -= 0.6 * (infp - 8)
            elif infp < -8:
                s -= 0.6 * (-infp - 8)
            if 2 <= rd <= 3 and 2 <= cd <= 3 and terr >= 9:
                s += 3
            if last_opp is not None and abs(last_opp[0] - r) + abs(last_opp[1] - c) <= 2:
                s += 1.5

            reg = regions[reg_id[r][c]]
            if reg is not None:
                rsize, rcolors = reg
                if rcolors == {1} and rsize <= 60:
                    s -= 14
                elif rcolors == {2}:
                    if rsize <= 8:
                        s -= 14
                    elif rsize <= 25:
                        s -= 5

            s += rnd.random() * 0.5
            if s > bestscore:
                bestscore = s
                best = (pt, newhash)

    new_memory = {}
    if best is None or bestscore < -10:
        action = (0, 0)
        hist.append(curhash)
    else:
        action = best[0]
        hist.append(curhash)
        hist.append(best[1])
    if len(hist) > 600:
        hist = hist[-600:]
    new_memory['hist'] = hist
    new_memory['prev_opp'] = [tuple(p) for p in opponent]
    return action, new_memory
