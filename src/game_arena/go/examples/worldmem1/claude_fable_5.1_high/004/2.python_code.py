
import random
import time

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_rng = random.Random(20240601)
ZOB = [[[0, _rng.getrandbits(64), _rng.getrandbits(64)] for _ in range(N + 2)] for _ in range(N + 2)]
LINE_SCORE = {1: -2.5, 2: 0.0, 3: 3.0, 4: 3.0, 5: 1.5, 6: 1.0}
KERNEL = []
for _dr in range(-3, 4):
    for _dc in range(-3, 4):
        _d = abs(_dr) + abs(_dc)
        if 1 <= _d <= 3:
            KERNEL.append((_dr, _dc, {1: 4, 2: 2, 3: 1}[_d]))
CORNER_BASE = [(4, 4, 8.0), (3, 4, 7.0), (4, 3, 7.0), (3, 3, 5.0),
               (3, 5, 4.0), (5, 3, 4.0), (4, 5, 3.5), (5, 4, 3.5)]
SIDE_PTS = [(4, 10, 4.0), (10, 4, 4.0), (16, 10, 4.0), (10, 16, 4.0),
            (3, 10, 3.0), (10, 3, 3.0), (17, 10, 3.0), (10, 17, 3.0), (10, 10, 2.0)]
PASS_T = -4.0


def make_board(me, opp):
    B = [[3] * (N + 2) for _ in range(N + 2)]
    for r in range(1, N + 1):
        row = B[r]
        for c in range(1, N + 1):
            row[c] = 0
    for (r, c) in me:
        if 1 <= r <= N and 1 <= c <= N:
            B[r][c] = 1
    for (r, c) in opp:
        if 1 <= r <= N and 1 <= c <= N:
            B[r][c] = 2
    return B


def board_hash(B):
    h = 0
    for r in range(1, N + 1):
        row = B[r]
        for c in range(1, N + 1):
            v = row[c]
            if v == 1 or v == 2:
                h ^= ZOB[r][c][v]
    return h


def flood(B, r, c):
    color = B[r][c]
    stones = {(r, c)}
    stack = [(r, c)]
    libs = set()
    while stack:
        r0, c0 = stack.pop()
        for dr, dc in DIRS:
            r1, c1 = r0 + dr, c0 + dc
            v = B[r1][c1]
            if v == 0:
                libs.add((r1, c1))
            elif v == color:
                if (r1, c1) not in stones:
                    stones.add((r1, c1))
                    stack.append((r1, c1))
    return stones, libs


def play(B, r, c, color):
    NB = [row[:] for row in B]
    NB[r][c] = color
    opp = 3 - color
    captured = []
    for dr, dc in DIRS:
        r1, c1 = r + dr, c + dc
        if NB[r1][c1] == opp:
            st, libs = flood(NB, r1, c1)
            if not libs:
                for (a, b) in st:
                    NB[a][b] = 0
                captured.extend(st)
    return NB, captured


def find_groups(B):
    gid = [[-1] * (N + 2) for _ in range(N + 2)]
    groups = []
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if B[r][c] in (1, 2) and gid[r][c] == -1:
                st, libs = flood(B, r, c)
                idx = len(groups)
                for (a, b) in st:
                    gid[a][b] = idx
                groups.append((B[r][c], list(st), libs))
    return gid, groups


def defender_escapes(B, target, att, depth, budget):
    """Defender (3-att) group at target is in atari, defender to move. Can it get out?"""
    dfd = 3 - att
    tr, tc = target
    if B[tr][tc] != dfd:
        return False
    st, libs = flood(B, tr, tc)
    if len(libs) == 0:
        return False
    if len(libs) >= 2:
        return True
    r = next(iter(libs))
    responses = [r]
    seen = set()
    for s in st:
        for dr, dc in DIRS:
            nb = (s[0] + dr, s[1] + dc)
            if B[nb[0]][nb[1]] == att and nb not in seen:
                ms, ml = flood(B, nb[0], nb[1])
                seen |= ms
                if len(ml) == 1:
                    q = next(iter(ml))
                    if q not in responses:
                        responses.append(q)
    for resp in responses:
        budget[0] -= 1
        if budget[0] <= 0:
            return True
        B3, _ = play(B, resp[0], resp[1], dfd)
        if B3[tr][tc] != dfd:
            continue
        st3, libs3 = flood(B3, tr, tc)
        if len(libs3) == 0:
            continue
        if len(libs3) >= 3:
            return True
        if len(libs3) == 1:
            continue
        if depth <= 0:
            return True
        if not attacker_captures(B3, target, att, depth - 1, budget):
            return True
    return False


def attacker_captures(B, target, att, depth, budget):
    """Attacker to move; defender group at target. Can attacker capture it (ladder-like)?"""
    dfd = 3 - att
    tr, tc = target
    if B[tr][tc] != dfd:
        return True
    st, libs = flood(B, tr, tc)
    if len(libs) <= 1:
        return True
    if len(libs) >= 3:
        return False
    for q in libs:
        budget[0] -= 1
        if budget[0] <= 0:
            return False
        B2, cap = play(B, q[0], q[1], att)
        if B2[tr][tc] != dfd:
            return True
        mst, mlibs = flood(B2, q[0], q[1])
        if len(mlibs) <= 1:
            continue
        st2, libs2 = flood(B2, tr, tc)
        if len(libs2) >= 2:
            continue
        if not defender_escapes(B2, target, att, depth, budget):
            return True
    return False


def _policy(me, opponent, memory):
    t0 = time.time()
    B = make_board(me, opponent)
    hist = set(memory.get('hist', [])) if isinstance(memory, dict) else set()
    h0 = board_hash(B)
    hist.add(h0)
    gid, groups = find_groups(B)
    total = len(me) + len(opponent)

    I = [[0] * (N + 2) for _ in range(N + 2)]
    O = [[0] * (N + 2) for _ in range(N + 2)]
    for (r, c) in me:
        for dr, dc, w in KERNEL:
            rr, cc = r + dr, c + dc
            if 1 <= rr <= N and 1 <= cc <= N:
                I[rr][cc] += w
    for (r, c) in opponent:
        for dr, dc, w in KERNEL:
            rr, cc = r + dr, c + dc
            if 1 <= rr <= N and 1 <= cc <= N:
                O[rr][cc] += w

    stones_all = list(me) + list(opponent)
    corner_bonus = {}
    dist_any = None
    if total < 80:
        quad_has = [False] * 4
        for (r, c) in stones_all:
            if r <= 9 and c <= 9:
                quad_has[0] = True
            if r <= 9 and c >= 11:
                quad_has[1] = True
            if r >= 11 and c <= 9:
                quad_has[2] = True
            if r >= 11 and c >= 11:
                quad_has[3] = True
        for qi, (rs, cs) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
            if quad_has[qi]:
                continue
            for (r, c, b) in CORNER_BASE:
                rr = r if rs == 0 else N + 1 - r
                cc = c if cs == 0 else N + 1 - c
                corner_bonus[(rr, cc)] = b
        for (r, c, b) in SIDE_PTS:
            if B[r][c] == 0 and all(max(abs(r - sr), abs(c - sc)) > 4 for (sr, sc) in stones_all):
                corner_bonus[(r, c)] = max(corner_bonus.get((r, c), 0.0), b)
        dist_any = [[99] * (N + 2) for _ in range(N + 2)]
        for (sr, sc) in stones_all:
            for rr in range(max(1, sr - 5), min(N, sr + 5) + 1):
                for cc in range(max(1, sc - 5), min(N, sc + 5) + 1):
                    d = max(abs(rr - sr), abs(cc - sc))
                    if d < dist_any[rr][cc]:
                        dist_any[rr][cc] = d

    budget = [1500]
    danger = set()
    for gi, g in enumerate(groups):
        if g[0] == 1 and len(g[2]) == 2:
            if time.time() - t0 > 0.3:
                break
            if attacker_captures(B, g[1][0], 2, 7, budget):
                danger.add(gi)

    rnd = random.Random(h0 & 0xFFFFFFFF)
    best = None
    best_score = -1e9
    best_hash = None

    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if B[r][c] != 0:
                continue
            adj_my = set()
            adj_opp = set()
            empties = []
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                v = B[rr][cc]
                if v == 0:
                    empties.append((rr, cc))
                elif v == 1:
                    adj_my.add(gid[rr][cc])
                elif v == 2:
                    adj_opp.add(gid[rr][cc])
            captured = [g for g in adj_opp if len(groups[g][2]) == 1]
            new_stones = {(r, c)}
            libs = set(empties)
            for g in adj_my:
                new_stones.update(groups[g][1])
                libs |= groups[g][2]
            libs.discard((r, c))
            cap_stones = []
            for g in captured:
                for s in groups[g][1]:
                    cap_stones.append(s)
                    for dr, dc in DIRS:
                        if (s[0] + dr, s[1] + dc) in new_stones:
                            libs.add(s)
                            break
            if not libs:
                continue
            h = h0 ^ ZOB[r][c][1]
            for s in cap_stones:
                h ^= ZOB[s[0]][s[1]][2]
            if h in hist:
                continue

            deep = (time.time() - t0) < 0.7
            if not deep:
                budget[0] = 0
            nl = len(libs)
            size_new = len(new_stones)
            score = 0.0
            ncap = len(cap_stones)
            if ncap:
                score += 12.0 * ncap + 10.0
            if nl == 1:
                if ncap == 0:
                    score -= 35.0 + 3.0 * size_new
                else:
                    score -= 6.0
            elif nl == 2:
                score -= 3.0 if adj_opp else 1.0
                if size_new >= 4:
                    score -= 3.0
            # eye filling
            if not empties and not adj_opp and not any(len(groups[g][2]) == 1 for g in adj_my):
                score -= 30.0
            B2 = None
            # saving / strengthening own groups
            for g in adj_my:
                ol = len(groups[g][2])
                sz = len(groups[g][1])
                if ol == 1:
                    if nl >= 3:
                        score += 8.0 * sz + 8.0
                    elif nl == 2:
                        if B2 is None:
                            B2, _ = play(B, r, c, 1)
                        if not attacker_captures(B2, (r, c), 2, 7, budget):
                            score += 8.0 * sz + 8.0
                        else:
                            score -= 2.0
                elif ol == 2:
                    if g in danger and nl >= 3:
                        score += 5.0 * sz + 5.0
                    elif nl >= 3:
                        score += 1.5 * min(sz, 6) + 1.0
            if len(adj_my) >= 2:
                score += 2.5
                if any(len(groups[g][2]) <= 3 for g in adj_my):
                    score += 2.0
            # attacking
            for g in adj_opp:
                if g in captured:
                    continue
                ol = len(groups[g][2])
                sz = len(groups[g][1])
                rem = ol - 1
                if rem == 1:
                    if nl >= 2:
                        if B2 is None:
                            B2, _ = play(B, r, c, 1)
                        if not defender_escapes(B2, groups[g][1][0], 1, 7, budget):
                            score += 10.0 * sz + 10.0
                        else:
                            score += 0.5 * min(sz, 4) + (1.0 if nl >= 3 else -1.0)
                elif rem == 2:
                    if nl >= 3:
                        score += 2.0 + 0.5 * min(sz, 6)
                    elif nl == 2:
                        score += 0.5
                elif rem == 3 and nl >= 3:
                    score += 0.5 + 0.2 * min(sz, 5)
            if len(adj_opp) >= 2 and nl >= 2:
                score += 2.5
            # positional
            line = min(r, c, N + 1 - r, N + 1 - c)
            score += LINE_SCORE.get(line, 0.5)
            ci = I[r][c]
            oi = O[r][c]
            control = ci - oi
            if oi <= 1 and control >= 6:
                score -= 6.0 + (control - 6) * 0.3
            elif ci <= 1 and control <= -6:
                score -= 6.0 + (-control - 6) * 0.3
            elif ci > 0 and oi > 0:
                score += 1.5 + 0.15 * min(ci, oi)
            if control >= 8 and oi > 1:
                score -= 3.0
            if oi == 0 and adj_my:
                score -= 1.0 * len(adj_my)
            if dist_any is not None:
                if not adj_my and not adj_opp:
                    d = dist_any[r][c]
                    if 2 <= d <= 4:
                        score += 1.5
                    elif d >= 5:
                        score += 0.5
                score += corner_bonus.get((r, c), 0.0)
                if total < 30 and (adj_my or adj_opp) and not cap_stones and nl >= 2:
                    score -= 1.5
            score += rnd.random() * 0.8
            if score > best_score:
                best_score = score
                best = (r, c)
                best_hash = h

    if best is None or best_score < PASS_T:
        move = (0, 0)
    else:
        move = best
        hist.add(best_hash)
    if not isinstance(memory, dict):
        memory = {}
    memory['hist'] = list(hist)
    return move, memory


def _fallback(me, opponent, memory):
    try:
        B = make_board(me, opponent)
        hist = set(memory.get('hist', [])) if isinstance(memory, dict) else set()
        cands = [(r, c) for r in range(1, N + 1) for c in range(1, N + 1) if B[r][c] == 0]
        random.shuffle(cands)
        for (r, c) in cands:
            B2, cap = play(B, r, c, 1)
            st, libs = flood(B2, r, c)
            if not libs:
                continue
            if board_hash(B2) in hist:
                continue
            return (r, c), (memory if isinstance(memory, dict) else {})
    except Exception:
        pass
    return (0, 0), (memory if isinstance(memory, dict) else {})


def policy(me, opponent, memory):
    try:
        if memory is None or not isinstance(memory, dict):
            memory = {}
        return _policy(me, opponent, memory)
    except Exception:
        return _fallback(me, opponent, memory)
