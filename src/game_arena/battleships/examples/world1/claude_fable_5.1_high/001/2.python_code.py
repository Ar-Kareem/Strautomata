
import random

FLEET = [5, 4, 3, 3, 2]
N = 10


def _find_runs(board):
    runs = []
    # horizontal
    for r in range(N):
        c = 0
        while c < N:
            if board[r][c] == 1:
                s = c
                while c < N and board[r][c] == 1:
                    c += 1
                L = c - s
                lb = (s == 0) or board[r][s - 1] == -1
                rb = (c == N) or board[r][c] == -1
                runs.append((L, [(r, x) for x in range(s, c)], lb and rb))
            else:
                c += 1
    # vertical
    for c in range(N):
        r = 0
        while r < N:
            if board[r][c] == 1:
                s = r
                while r < N and board[r][c] == 1:
                    r += 1
                L = r - s
                tb = (s == 0) or board[s - 1][c] == -1
                bb = (r == N) or board[r][c] == -1
                runs.append((L, [(y, c) for y in range(s, r)], tb and bb))
            else:
                r += 1
    return [x for x in runs if x[0] >= 2]


def _subset_sum(fleet, target):
    # prefer single ship, then fewest ships
    if target in fleet:
        return [target]
    best = None
    m = len(fleet)
    for mask in range(1, 1 << m):
        chosen = [fleet[i] for i in range(m) if mask >> i & 1]
        if sum(chosen) == target:
            if best is None or len(chosen) < len(best):
                best = chosen
    return best


def policy(board):
    unknown = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not unknown:
        return (0, 0)

    fleet = list(FLEET)
    sunk = set()
    runs = _find_runs(board)
    runs.sort(key=lambda x: -x[0])
    for L, cells, blocked in runs:
        if not fleet:
            break
        if any(cl in sunk for cl in cells):
            continue
        if blocked or L >= max(fleet):
            combo = _subset_sum(fleet, L)
            if combo is not None:
                for s in combo:
                    fleet.remove(s)
                sunk.update(cells)

    if not fleet:
        # everything should be sunk; still must return a legal move
        fleet = [2]

    blocked = [[board[r][c] == -1 or (r, c) in sunk for c in range(N)] for r in range(N)]
    active = [[board[r][c] == 1 and (r, c) not in sunk for c in range(N)] for r in range(N)]
    any_active = any(active[r][c] for r in range(N) for c in range(N))

    W = [[0.0] * N for _ in range(N)]
    for s in set(fleet):
        cnt = fleet.count(s)
        for r in range(N):
            for c in range(N):
                for dr, dc in ((0, 1), (1, 0)):
                    er, ec = r + dr * (s - 1), c + dc * (s - 1)
                    if er >= N or ec >= N:
                        continue
                    cells = [(r + dr * i, c + dc * i) for i in range(s)]
                    ok = True
                    h = 0
                    unk = []
                    for (y, x) in cells:
                        if blocked[y][x]:
                            ok = False
                            break
                        if active[y][x]:
                            h += 1
                        elif board[y][x] == 0:
                            unk.append((y, x))
                    if not ok or not unk:
                        continue
                    w = cnt * (100.0 ** h)
                    for (y, x) in unk:
                        W[y][x] += w

    best = max(W[r][c] for r, c in unknown)
    if best <= 0:
        return random.choice(unknown)

    cands = [(r, c) for r, c in unknown if W[r][c] >= best - 1e-9]

    if not any_active:
        # parity lattice preference for hunting
        ms = min(fleet)
        lattice = [(r, c) for r, c in unknown if (r + c) % ms == 0 and W[r][c] > 0]
        if lattice:
            lb = max(W[r][c] for r, c in lattice)
            if lb >= 0.8 * best:
                cands = [(r, c) for r, c in lattice if W[r][c] >= lb - 1e-9]

    # slight center preference among ties
    def center_score(p):
        return -abs(p[0] - 4.5) - abs(p[1] - 4.5)

    random.shuffle(cands)
    cands.sort(key=center_score, reverse=True)
    top = cands[0]
    if board[top[0]][top[1]] != 0:
        return random.choice(unknown)
    return (int(top[0]), int(top[1]))
