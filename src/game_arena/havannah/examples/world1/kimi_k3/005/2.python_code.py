
import time, random, math

def policy(me, opp, valid_mask):
    N = len(valid_mask)
    valid = [[bool(valid_mask[r][c]) for c in range(N)] for r in range(N)]
    V = [r * N + c for r in range(N) for c in range(N) if valid[r][c]]
    vid = lambda r, c: r * N + c
    rc = lambda v: (v // N, v % N)

    # ---------- hex adjacency (matches the worked example exactly) ----------
    nb = [[] for _ in range(N * N)]
    deg = [0] * (N * N)
    for r in range(N):
        er = (r % 2 == 0)
        for c in range(N):
            if not valid[r][c]:
                continue
            v = vid(r, c)
            cand = ((r-1,c),(r+1,c),(r,c-1),(r,c+1),
                    (r-1,c-1),(r-1,c+1)) if er else \
                   ((r-1,c),(r+1,c),(r,c-1),(r,c+1),
                    (r+1,c-1),(r+1,c+1))
            for nr, nc in cand:
                if 0 <= nr < N and 0 <= nc < N and valid[nr][nc]:
                    nb[v].append(vid(nr, nc))
            deg[v] = len(nb[v])

    # ---------- edges (fork) and corners (bridge) ----------
    PC = [bin(i).count('1') for i in range(64)]
    EB = [0] * (N * N)          # edge bits (non-corner boundary cells only)
    CB = [0] * (N * N)          # corner bits
    boundary = [v for v in V if deg[v] < 6]
    corners = [v for v in V if deg[v] == 3]
    bset = set(boundary)
    cset = set(corners)
    ok = (len(corners) == 6)
    if ok:
        cid = {v: i for i, v in enumerate(corners)}
        for v in corners:
            CB[v] = 1 << cid[v]
        elab = {}
        neid = 0
        bnb = {v: [u for u in nb[v] if deg[u] < 6] for v in boundary}
        for c0 in corners:
            for s0 in bnb[c0]:
                if s0 in cset:
                    continue
                prev, cur, path = c0, s0, []
                while cur not in cset:
                    path.append(cur)
                    nx = [u for u in bnb[cur] if u != prev]
                    if len(nx) != 1:
                        ok = False
                        break
                    prev, cur = cur, nx[0]
                if not ok:
                    break
                if path and path[0] not in elab:
                    for cell in path:
                        elab[cell] = neid
                    neid += 1
            if not ok:
                break
        if ok and neid <= 6 and all((deg[v] != 4) or (v in elab) for v in V):
            for v, e in elab.items():
                EB[v] = 1 << e
        else:
            ok = False
    if not ok:  # fallback (non-ideal mask): approximate with corner extremes
        corners = sorted(V, key=lambda v: (deg[v], v))[:6]
        for i, v in enumerate(corners):
            CB[v] = 1 << i
            cset.add(v)
        cr = sum(v // N for v in V) / len(V)
        cc = sum(v % N for v in V) / len(V)
        cang = sorted((math.atan2((v // N) - cr, (v % N) - cc), i) for i, v in enumerate(corners))
        for v in boundary:
            if v in cset:
                continue
            a = math.atan2((v // N) - cr, (v % N) - cc)
            # sector between consecutive corner angles -> edge id
            ids = [i for _, i in cang] + [cang[0][1]]
            EB[v] = 1 << (ids[0] % 6) if ids else 0
            for k in range(6):
                a0 = cang[k][0]
                a1 = cang[(k + 1) % 6][0] + (2 * math.pi if k == 5 else 0)
                aa = a if a >= a0 else a + 2 * math.pi
                if a0 <= aa <= a1:
                    EB[v] = 1 << (cang[k][1] % 6)
                    break

    # ---------- position ----------
    ME, OP = 1, 2
    owner = [0] * (N * N)
    for (r, c) in me:
        if 0 <= r < N and 0 <= c < N and valid[r][c]:
            owner[vid(r, c)] = ME
    for (r, c) in opp:
        if 0 <= r < N and 0 <= c < N and valid[r][c]:
            owner[vid(r, c)] = OP
    empties = [v for v in V if owner[v] == 0]
    if not empties:
        return rc(V[0])

    # opening
    cen = vid(N // 2, N // 2)
    if not me and not opp and owner[cen] == 0 and valid[N // 2][N // 2]:
        return (N // 2, N // 2)

    # ---------- exact tactical helpers ----------
    def comp_bits(start, color):
        e = c = s = 0
        st = [start]
        seen = {start}
        while st:
            v = st.pop()
            e |= EB[v]; c |= CB[v]; s += 1
            for u in nb[v]:
                if owner[u] == color and u not in seen:
                    seen.add(u)
                    st.append(u)
        return e, c, s

    def ring_win(color):
        seen = bytearray(N * N)
        st = [v for v in boundary if owner[v] != color]
        for v in st:
            seen[v] = 1
        while st:
            v = st.pop()
            for u in nb[v]:
                if owner[u] != color and not seen[u]:
                    seen[u] = 1
                    st.append(u)
        for v in V:
            if owner[v] != color and not seen[v]:
                return True
        return False

    def move_wins(v, color):
        owner[v] = color
        try:
            e, c, s = comp_bits(v, color)
            if PC[e] >= 3 or PC[c] >= 2:
                return True
            adj = sum(1 for u in nb[v] if owner[u] == color)
            if adj >= 2 and s >= 6 and ring_win(color):
                return True
            return False
        finally:
            owner[v] = 0

    my_wins = [v for v in empties if move_wins(v, ME)]
    if my_wins:
        return rc(my_wins[0])
    op_wins = [v for v in empties if move_wins(v, OP)]
    if op_wins:
        # block the opponent's most central / most connected winning cell
        def bscore(v):
            r, c = rc(v)
            return (sum(1 for u in nb[v] if owner[u] == ME) * 2
                    - abs(r - N // 2) - abs(c - N // 2))
        return rc(max(op_wins, key=bscore))

    # ---------- union-find with rollback (for Monte-Carlo) ----------
    parent = list(range(N * N))
    rnk = [0] * (N * N)
    siz = [1] * (N * N)
    em = [0] * (N * N)
    cm = [0] * (N * N)

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    def union(a, b, log):
        ra, rb = find(a), find(b)
        if ra == rb:
            return ra
        if rnk[ra] < rnk[rb]:
            ra, rb = rb, ra
        log.append(('u', rb, ra, rnk[ra], siz[ra], em[ra], cm[ra]))
        parent[rb] = ra
        siz[ra] += siz[rb]
        em[ra] |= em[rb]
        cm[ra] |= cm[rb]
        if rnk[ra] == rnk[rb]:
            rnk[ra] += 1
        return ra

    def place(v, color, log):
        owner[v] = color
        parent[v] = v; rnk[v] = 0; siz[v] = 1
        em[v] = EB[v]; cm[v] = CB[v]
        log.append(('p', v))
        for u in nb[v]:
            if owner[u] == color:
                union(v, u, log)
        r = find(v)
        return PC[em[r]] >= 3 or PC[cm[r]] >= 2

    def undo(log):
        while log:
            rec = log.pop()
            if rec[0] == 'p':
                owner[rec[1]] = 0
            else:
                _, ch, pa, prk, psz, pem, pcm = rec
                parent[ch] = ch
                rnk[pa] = prk; siz[pa] = psz; em[pa] = pem; cm[pa] = pcm

    def rand_empty(last):
        if last >= 0:
            cands = [u for u in nb[last] if owner[u] == 0]
            if cands and random.random() < 0.7:
                return random.choice(cands)
        for _ in range(14):
            v = random.choice(V)
            if owner[v] == 0:
                return v
        for v in V:
            if owner[v] == 0:
                return v
        return -1

    def cap_value():
        best1 = best2 = 0.0
        for v in V:
            col = owner[v]
            if col and parent[v] == v:
                sc = min(PC[em[v]], 3) * 2.0 + min(PC[cm[v]], 2) * 3.0 + 0.02 * siz[v]
                if col == ME:
                    if sc > best1: best1 = sc
                else:
                    if sc > best2: best2 = sc
        x = (best1 - best2) / 12.0
        return 1.0 if x > 1 else (-1.0 if x < -1 else x)

    def playout(first_color):
        side = first_color
        last = -1
        for _ in range(70):
            v = rand_empty(last)
            if v < 0:
                break
            if place(v, side, LOG):
                return 1.0 if side == ME else -1.0
            last = v
            side = OP if side == ME else ME
        return cap_value()

    def opp_has_immediate():
        for e in V:
            if owner[e] == 0:
                owner[e] = OP
                ee, cc, _ = comp_bits(e, OP)
                owner[e] = 0
                if PC[ee] >= 3 or PC[cc] >= 2:
                    return True
        return False

    # ---------- candidate shortlist ----------
    def hscore(v):
        r, c = rc(v)
        am = sum(1 for u in nb[v] if owner[u] == ME)
        ao = sum(1 for u in nb[v] if owner[u] == OP)
        return (am * 2.0 + ao * 1.0 + (1.2 if EB[v] else 0.0) + (1.0 if CB[v] else 0.0)
                - 0.06 * (abs(r - N // 2) + abs(c - N // 2)))

    arms = empties
    if len(arms) > 28:
        arms = sorted(empties, key=hscore, reverse=True)[:28]
    k = len(arms)
    wins = [0.0] * k
    vis = [0] * k
    LOG = []
    t0 = time.time()
    deadline = t0 + 0.86
    total = 0
    it = 0
    while time.time() < deadline and it < 200000:
        it += 1
        # UCB1 over root arms
        if total < k:
            ai = total
        else:
            lt = math.log(total)
            bi, bv = 0, -1e18
            for i in range(k):
                if vis[i] == 0:
                    ai = i; break
                sc = wins[i] / vis[i] + 1.3 * math.sqrt(lt / vis[i])
                if sc > bv:
                    bv = sc; bi = i
            else:
                ai = bi
        m = arms[ai]
        place(m, ME, LOG)          # (already verified not an immediate win)
        res = playout(OP)          # opponent to move
        undo(LOG)
        vis[ai] += 1
        wins[ai] += (res + 1.0) * 0.5
        total += 1

    order = sorted(range(k), key=lambda i: (vis[i], wins[i]), reverse=True)
    chosen = arms[order[0]]
    for i in order[:10]:
        m = arms[i]
        owner[m] = ME
        hang = opp_has_immediate()
        owner[m] = 0
        if not hang:
            chosen = m
            break

    # ---------- legality fallback ----------
    if not (0 <= chosen < N * N) or owner[chosen] != 0 or not valid[chosen // N][chosen % N]:
        rest = [v for v in V if owner[v] == 0]
        chosen = max(rest, key=hscore) if rest else V[0]
    return rc(chosen)
