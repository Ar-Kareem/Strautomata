
import random

N = 19
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
STAR = {(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)}

BOOK = [
    (4,4),(16,16),(16,4),(4,16),
    (10,4),(4,10),(16,10),(10,16),
    (10,10),
    (7,4),(4,7),(16,7),(7,16),(13,16),(16,13),(13,4),(4,13),
    (7,10),(10,7),(10,13),(13,10),
    (6,4),(4,6),(16,14),(14,16),(6,16),(16,6),(14,4),(4,14),
    (6,10),(10,6),(10,14),(14,10),
    (7,7),(7,13),(13,7),(13,13),
]

def _group(board, sr, sc):
    col = board[sr][sc]
    stones = []
    libs = set()
    stack = [(sr, sc)]
    seen = {(sr, sc)}
    while stack:
        r, c = stack.pop()
        stones.append((r, c))
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N:
                v = board[nr][nc]
                if v == 0:
                    libs.add((nr, nc))
                elif v == col and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))
    return stones, libs

def _all_groups(board, color):
    visited = [[False]*N for _ in range(N)]
    groups = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == color and not visited[r][c]:
                # BFS
                stones = []
                libs = set()
                stack = [(r, c)]
                visited[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    stones.append((cr, cc))
                    for dr, dc in DIRS:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < N and 0 <= nc < N:
                            v = board[nr][nc]
                            if v == 0:
                                libs.add((nr, nc))
                            elif v == color and not visited[nr][nc]:
                                visited[nr][nc] = True
                                stack.append((nr, nc))
                groups.append((stones, libs))
    return groups

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    try:
        if memory is None:
            memory = {}
        if "seen" not in memory or not isinstance(memory["seen"], set):
            # try to keep set, else reset
            try:
                s = memory.get("seen", None)
                if isinstance(s, list):
                    memory["seen"] = set(s)
                else:
                    memory["seen"] = set()
            except Exception:
                memory["seen"] = set()
        seen = memory["seen"]

        # build board 0 empty 1 me 2 opp, 0-indexed
        board = [[0]*N for _ in range(N)]
        occ = set()
        for (r, c) in me:
            if 1 <= r <= 19 and 1 <= c <= 19:
                board[r-1][c-1] = 1
                occ.add((r-1, c-1))
        for (r, c) in opponent:
            if 1 <= r <= 19 and 1 <= c <= 19:
                # opponent stone overwrites only if empty (defensive)
                if board[r-1][c-1] == 0:
                    board[r-1][c-1] = 2
                    occ.add((r-1, c-1))
        total = len(occ)

        # record current position for superko
        try:
            cur_key = tuple(tuple(row) for row in board)
            seen.add(cur_key)
        except Exception:
            pass

        empties = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
        if not empties:
            return ((0, 0), memory)

        # helper to test legality quickly with simulation
        def simulate(r, c):
            # returns (legal, captures, own_libs_len, own_size, board2) or (False,...)
            # assume empty
            b2 = [row[:] for row in board]
            b2[r][c] = 1
            caps = 0
            # check opponent neighbours
            checked = set()
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N and b2[nr][nc] == 2:
                    if (nr, nc) in checked:
                        continue
                    stones, libs = _group(b2, nr, nc)
                    for s in stones:
                        checked.add(s)
                    if len(libs) == 0:
                        caps += len(stones)
                        for sr, sc in stones:
                            b2[sr][sc] = 0
            # own liberties
            ostones, olibs = _group(b2, r, c)
            if len(olibs) == 0:
                return (False, 0, 0, 0, None, None, None)
            return (True, caps, len(olibs), len(ostones), b2, ostones, olibs)

        # opening book fast path
        if total < 14:
            for (br, bc) in BOOK:
                r, c = br-1, bc-1
                if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
                    legal, caps, ol, osz, b2, _, _ = simulate(r, c)
                    if legal and ol > 1:
                        # avoid immediate self-atari in opening
                        try:
                            k = tuple(tuple(row) for row in b2)
                            if k in seen:
                                continue
                        except Exception:
                            pass
                        return ((br, bc), memory)

        # precompute groups for save bonus
        own_groups = _all_groups(board, 1)
        save_map = {}  # (r,c) -> max size saved
        for stones, libs in own_groups:
            if len(libs) == 1:
                lib = next(iter(libs))
                sz = len(stones)
                if lib not in save_map or save_map[lib] < sz:
                    save_map[lib] = sz

        # precompute friendly/enemy counts via board for window bonus quickly?
        # For each empty we will count 5x5 window (could be ~24 checks * 300 = 7200, fine)

        best_list = []  # (score, r, c, b2key, b2)
        # iterate
        for (r, c) in empties:
            legal, caps, olibs_n, osize, b2, ostones, olibs = simulate(r, c)
            if not legal:
                continue

            score = 0.0

            # captures
            if caps > 0:
                score += caps * 120 + 40

            # save
            if (r, c) in save_map:
                score += 100 + 10 * save_map[(r, c)]

            # atari / pressure on neighbours after move
            # check opponent neighbour groups on b2
            seen_opp = set()
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N and b2[nr][nc] == 2:
                    if (nr, nc) in seen_opp:
                        continue
                    stones2, libs2 = _group(b2, nr, nc)
                    for s in stones2:
                        seen_opp.add(s)
                    nl = len(libs2)
                    sz2 = len(stones2)
                    if nl == 1:
                        score += 55 + 8 * min(sz2, 10)
                    elif nl == 2:
                        score += 12 + 2 * min(sz2, 8)

            # own liberties
            if olibs_n == 1:
                score -= 600
            elif olibs_n == 2:
                score -= 15
            elif olibs_n == 3:
                score += 3
            else:
                score += 8
                if osize > 4:
                    score += 3

            # friendly neighbours (original board) - shape
            f = 0
            e = 0
            eye_me = True
            eye_opp = True
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N:
                    v = board[nr][nc]
                    if v == 1:
                        f += 1
                    elif v == 2:
                        e += 1
                    if v != 1:
                        eye_me = False
                    if v != 2:
                        eye_opp = False
                else:
                    # edge counts as friendly wall for eye_me? treat as friendly
                    # for opp eye, edge is not opponent
                    eye_opp = False
                    pass
            if eye_me and caps == 0:
                score -= 250  # filling own eye
            elif f == 4 and caps == 0:
                score -= 250
            elif f == 3 and caps == 0:
                score -= 25
            elif f == 1:
                score += 8
            elif f == 2:
                score += 4

            if eye_opp and caps == 0:
                # throwing into opponent eye
                if olibs_n <= 2:
                    score -= 150
                else:
                    score -= 30

            # positional
            d = r
            if c < d:
                d = c
            t = N-1-r
            if t < d:
                d = t
            t2 = N-1-c
            if t2 < d:
                d = t2
            if total < 80:
                if d == 0:
                    score -= 12
                elif d == 1:
                    score -= 4
                elif d == 2 or d == 3:
                    score += 6
                else:
                    score -= 1
                if (r+1, c+1) in STAR:
                    score += 4
            else:
                if d == 0:
                    score -= 2
                elif d == 1:
                    score -= 1

            # window influence 5x5
            Fw = 0
            Ew = 0
            for dr in (-2, -1, 0, 1, 2):
                nr = r+dr
                if nr < 0 or nr >= N:
                    continue
                row = board[nr]
                for dc in (-2, -1, 0, 1, 2):
                    if dr == 0 and dc == 0:
                        continue
                    nc = c+dc
                    if nc < 0 or nc >= N:
                        continue
                    v = row[nc]
                    if v == 1:
                        Fw += 1
                    elif v == 2:
                        Ew += 1
            score += min(Fw, 2) * 3 + min(Ew, 3) * 5
            if Fw > 3:
                score -= (Fw-3) * 4
            if Fw == 0 and Ew == 0:
                if total < 60:
                    score += 3
                else:
                    score -= 8
            # first line late dame vs early
            # ladder-ish: avoid 2nd line attachment with no support?
            # small noise
            score += random.random() * 4

            # ko: penalize repeat heavily (don't forbid yet, filter later)
            try:
                k = tuple(tuple(row) for row in b2)
                repeated = k in seen
            except Exception:
                k = None
                repeated = False
            if repeated:
                score -= 500

            best_list.append((score, r, c, k, b2))

        if not best_list:
            return ((0, 0), memory)

        best_list.sort(key=lambda x: x[0], reverse=True)
        best_score = best_list[0][0]
        # pass if only terrible eye-filling moves remain
        if best_score < -30:
            # check if any reasonable dame exists? best already is best, so pass
            return ((0, 0), memory)

        # pick first non-repeating (already penalized, but ensure)
        chosen = None
        for score, r, c, k, b2 in best_list[:20]:
            if k is not None and k in seen:
                continue
            chosen = (score, r, c, k)
            break
        if chosen is None:
            # all top repeats, pass to avoid ko loop if capture not decisive
            # if best capture is large, allow it anyway
            if best_list[0][0] > 150:
                _, r, c, k = best_list[0][0], best_list[0][1], best_list[0][2], best_list[0][3]
                chosen = (best_list[0][0], r, c, k)
            else:
                return ((0, 0), memory)
        _, r, c, k = chosen
        # add to seen
        try:
            if k is not None:
                seen.add(k)
        except Exception:
            pass
        memory["seen"] = seen
        return ((r+1, c+1), memory)

    except Exception:
        try:
            # emergency fallback: first empty
            occ2 = set(me) | set(opponent)
            occset = set()
            for (rr, cc) in occ2:
                if isinstance(rr, int) and isinstance(cc, int):
                    occset.add((rr, cc))
            for rr in range(1, 20):
                for cc in range(1, 20):
                    if (rr, cc) not in occset:
                        return ((rr, cc), memory if isinstance(memory, dict) else {})
            return ((0, 0), memory if isinstance(memory, dict) else {})
        except Exception:
            return ((0, 0), {})

