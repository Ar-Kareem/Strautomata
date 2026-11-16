
import heapq
import time

N = 11
NN = N * N
INF = 999

# Neighbour lists: all 8 neighbours except (i-1,j-1) and (i+1,j+1)
NBRS = []
for i in range(N):
    for j in range(N):
        lst = []
        for di, dj in ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)):
            a, b = i + di, j + dj
            if 0 <= a < N and 0 <= b < N:
                lst.append(a * N + b)
        NBRS.append(lst)

# Edge membership
S_B = [x < N for x in range(NN)]                 # black start: top row
E_B = [x >= NN - N for x in range(NN)]           # black end: bottom row
S_W = [x % N == 0 for x in range(NN)]            # white start: left col
E_W = [x % N == N - 1 for x in range(NN)]        # white end: right col
SIDES = {1: (S_B, E_B), 2: (S_W, E_W)}

CENTER_DIST = []
for x in range(NN):
    r, c = divmod(x, N)
    CENTER_DIST.append(abs(r - 5) + abs(c - 5) + abs((r + c) - 10))


def two_dist(board, c):
    S, E = SIDES[c]
    lab = [0] * NN
    for x in range(NN):
        v = board[x]
        if v == 0:
            lab[x] = x
        elif v != c:
            lab[x] = -1
        else:
            lab[x] = -2
    groups = []
    gstart = []
    gend = []
    for x in range(NN):
        if lab[x] == -2:
            g = NN + len(groups)
            members = [x]
            lab[x] = g
            stack = [x]
            ts = te = False
            while stack:
                y = stack.pop()
                if S[y]:
                    ts = True
                if E[y]:
                    te = True
                for n in NBRS[y]:
                    if lab[n] == -2:
                        lab[n] = g
                        members.append(n)
                        stack.append(n)
            if ts and te:
                return 0
            groups.append(members)
            gstart.append(ts)
            gend.append(te)
    total = NN + len(groups)
    final = [False] * total
    cnt = [0] * total
    seen = [-1] * total
    heap = []
    for x in range(NN):
        if S[x] and board[x] == 0:
            heap.append((1, x))
    for gi in range(len(groups)):
        if gstart[gi]:
            heap.append((0, NN + gi))
    heapq.heapify(heap)
    hpop = heapq.heappop
    hpush = heapq.heappush
    while heap:
        d, u = hpop(heap)
        if final[u]:
            continue
        final[u] = True
        if u < NN:
            if E[u]:
                return d
            members = (u,)
        else:
            gi = u - NN
            if gend[gi]:
                return d
            members = groups[gi]
        for y in members:
            for n in NBRS[y]:
                v = lab[n]
                if v < 0 or final[v] or seen[v] == u:
                    continue
                seen[v] = u
                cnt[v] += 1
                if cnt[v] == 2:
                    hpush(heap, (d + 1 if v < NN else d, v))
    return INF


def evaluate(board, mc):
    dm = two_dist(board, mc)
    if dm == 0:
        return 1000
    do = two_dist(board, 3 - mc)
    if do == 0:
        return -1000
    return do - dm


def _coords(x):
    return (x // N, x % N)


def policy(me, opp, color):
    t0 = time.time()
    deadline = t0 + 0.75
    mc = 1 if color == 'b' else 2
    oc = 3 - mc
    board = [0] * NN
    for (r, c) in me:
        if 0 <= r < N and 0 <= c < N:
            board[r * N + c] = mc
    for (r, c) in opp:
        if 0 <= r < N and 0 <= c < N:
            board[r * N + c] = oc
    empties = [x for x in range(NN) if board[x] == 0]
    if not empties:
        return (0, 0)
    if not me and not opp:
        return (5, 5)
    if len(empties) == 1:
        return _coords(empties[0])

    # Pass 1: my moves
    e_me = {}
    for x in empties:
        board[x] = mc
        e = evaluate(board, mc)
        board[x] = 0
        if e >= 1000:
            return _coords(x)
        e_me[x] = e
        if time.time() > deadline:
            break
    for x in empties:
        if x not in e_me:
            e_me[x] = -500 - CENTER_DIST[x]

    ordered_me = sorted(empties, key=lambda x: (-e_me[x], CENTER_DIST[x]))
    best_move = ordered_me[0]
    if time.time() > deadline:
        return _coords(best_move)

    # Pass 2: opponent moves
    e_opp = {}
    threats = []
    for x in empties:
        board[x] = oc
        e = evaluate(board, mc)
        board[x] = 0
        e_opp[x] = e
        if e <= -1000:
            threats.append(x)
        if time.time() > deadline:
            break
    for x in empties:
        if x not in e_opp:
            e_opp[x] = 0
    if len(threats) == 1:
        return _coords(threats[0])
    if time.time() > deadline:
        return _coords(best_move)

    ordered_opp = sorted(empties, key=lambda x: (e_opp[x], CENTER_DIST[x]))
    K1 = 12
    candidates = ordered_me[:K1]
    reply_base = set(ordered_opp[:16]) | set(ordered_me[:8]) | set(threats)

    best_key = None
    timed_out = False
    for m in candidates:
        R = set(reply_base)
        for n in NBRS[m]:
            R.add(n)
        R.discard(m)
        R = [r for r in R if board[r] == 0]
        R.sort(key=lambda x: (e_opp[x], CENTER_DIST[x]))
        board[m] = mc
        worst = 10**9
        complete = True
        for r in R:
            board[r] = oc
            e = evaluate(board, mc)
            board[r] = 0
            if e < worst:
                worst = e
            if best_key is not None and worst < best_key[0]:
                complete = False  # pruned; can't beat best
                break
            if time.time() > deadline:
                timed_out = True
                complete = False
                break
        board[m] = 0
        if timed_out:
            if best_key is None and worst > -10**9:
                # partially evaluated first candidate; keep it as fallback
                pass
            break
        if complete:
            key = (worst, e_me[m], -CENTER_DIST[m])
            if best_key is None or key > best_key:
                best_key = key
                best_move = m
        if time.time() > deadline:
            break

    if board[best_move] != 0:
        for x in empties:
            if board[x] == 0:
                best_move = x
                break
    return _coords(best_move)
