
import random
from collections import deque

DIRS = [(-1,0),(1,0),(0,-1),(0,1)]
DIAGS = [(-1,-1),(-1,1),(1,-1),(1,1)]

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    try:
        N = 19
        board = [[0]*N for _ in range(N)]
        for r, c in me:
            try:
                if 1 <= r <= 19 and 1 <= c <= 19:
                    board[r-1][c-1] = 1
            except:
                continue
        for r, c in opponent:
            try:
                if 1 <= r <= 19 and 1 <= c <= 19:
                    # don't overwrite own (should not happen)
                    if board[r-1][c-1] == 0:
                        board[r-1][c-1] = 2
            except:
                continue

        total = len(me) + len(opponent)

        # build groups once
        gid_map = [[-1]*N for _ in range(N)]
        g_stones = []  # list of list
        g_libs = []    # list of set
        gid = 0
        for r in range(N):
            for c in range(N):
                if board[r][c] != 0 and gid_map[r][c] == -1:
                    color = board[r][c]
                    q = [(r, c)]
                    gid_map[r][c] = gid
                    idx = 0
                    stones = []
                    libs = set()
                    while idx < len(q):
                        cr, cc = q[idx]
                        idx += 1
                        stones.append((cr, cc))
                        # neighbors
                        if cr > 0:
                            nr, nc = cr-1, cc
                            v = board[nr][nc]
                            if v == 0:
                                libs.add((nr, nc))
                            elif v == color and gid_map[nr][nc] == -1:
                                gid_map[nr][nc] = gid
                                q.append((nr, nc))
                        if cr < N-1:
                            nr, nc = cr+1, cc
                            v = board[nr][nc]
                            if v == 0:
                                libs.add((nr, nc))
                            elif v == color and gid_map[nr][nc] == -1:
                                gid_map[nr][nc] = gid
                                q.append((nr, nc))
                        if cc > 0:
                            nr, nc = cr, cc-1
                            v = board[nr][nc]
                            if v == 0:
                                libs.add((nr, nc))
                            elif v == color and gid_map[nr][nc] == -1:
                                gid_map[nr][nc] = gid
                                q.append((nr, nc))
                        if cc < N-1:
                            nr, nc = cr, cc+1
                            v = board[nr][nc]
                            if v == 0:
                                libs.add((nr, nc))
                            elif v == color and gid_map[nr][nc] == -1:
                                gid_map[nr][nc] = gid
                                q.append((nr, nc))
                    g_stones.append(stones)
                    g_libs.append(libs)
                    gid += 1

        empties = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
        if not empties:
            return ((0, 0), memory)

        # opening: prefer 3rd/4th line star points
        # precompute star set for bonus
        stars = {(3,3),(3,9),(3,15),(9,3),(9,9),(9,15),(15,3),(15,9),(15,15),
                 (2,2),(2,6),(2,12),(2,16),(6,2),(6,6),(6,12),(6,16),
                 (12,2),(12,6),(12,12),(12,16),(16,2),(16,6),(16,12),(16,16)}

        best_score = -10**18
        best_move = None

        is_opening = total < 50

        for r, c in empties:
            # adjacency
            adj_own = set()
            adj_opp = set()
            empty_nb = 0
            own_orth = 0
            opp_orth = 0
            # unrolled neighbor checks
            # up
            if r > 0:
                v = board[r-1][c]
                if v == 0:
                    empty_nb += 1
                elif v == 1:
                    adj_own.add(gid_map[r-1][c])
                    own_orth += 1
                else:
                    adj_opp.add(gid_map[r-1][c])
                    opp_orth += 1
            else:
                own_orth += 0  # edge handled for eye separately
            if r < N-1:
                v = board[r+1][c]
                if v == 0:
                    empty_nb += 1
                elif v == 1:
                    adj_own.add(gid_map[r+1][c])
                    own_orth += 1
                else:
                    adj_opp.add(gid_map[r+1][c])
                    opp_orth += 1
            if c > 0:
                v = board[r][c-1]
                if v == 0:
                    empty_nb += 1
                elif v == 1:
                    adj_own.add(gid_map[r][c-1])
                    own_orth += 1
                else:
                    adj_opp.add(gid_map[r][c-1])
                    opp_orth += 1
            if c < N-1:
                v = board[r][c+1]
                if v == 0:
                    empty_nb += 1
                elif v == 1:
                    adj_own.add(gid_map[r][c+1])
                    own_orth += 1
                else:
                    adj_opp.add(gid_map[r][c+1])
                    opp_orth += 1

            # captures and saves
            captures = 0
            captured_n = 0
            for g in adj_opp:
                libs = g_libs[g]
                # group in atari whose only liberty is (r,c)
                if len(libs) == 1 and (r, c) in libs:
                    captures += len(g_stones[g])
                    captured_n += 1

            save = 0
            for g in adj_own:
                libs = g_libs[g]
                if len(libs) == 1 and (r, c) in libs:
                    save += len(g_stones[g])

            # merged liberties for own new group
            # union of own liberties minus (r,c) plus empty neighbors
            # fast estimate of size without building huge set when possible
            # build set (small)
            merged = set()
            for g in adj_own:
                # union; libs are small on average
                merged.update(g_libs[g])
            if merged:
                merged.discard((r, c))
            # add empty neighbors
            if r > 0 and board[r-1][c] == 0:
                merged.add((r-1, c))
            if r < N-1 and board[r+1][c] == 0:
                merged.add((r+1, c))
            if c > 0 and board[r][c-1] == 0:
                merged.add((r, c-1))
            if c < N-1 and board[r][c+1] == 0:
                merged.add((r, c+1))
            # captured adjacent points become liberties (at least one)
            # if captures>0, suicide impossible; add bonus liberty
            n_merged = len(merged)
            if captures > 0 and n_merged == 0:
                n_merged = 1  # capture gives liberty

            # suicide -> illegal, skip
            if captures == 0 and n_merged == 0:
                continue

            score = 0.0

            # tactical weights - dominant
            if captures > 0:
                score += captures * 200 + captured_n * 10
                # snapback / big capture extra
                if captures >= 3:
                    score += 50
            if save > 0:
                # saving is almost as important, but avoid double count if also capture
                # if capture also saves, capture already gives value
                if captures == 0:
                    score += save * 150 + 20
                else:
                    score += save * 40

            # atari attack / defense shaping
            for g in adj_opp:
                if len(g_libs[g]) == 1:
                    continue  # already captured
                # after move, liberties -1 (since (r,c) was a liberty)
                # check if (r,c) in libs (it must be if adjacent)
                lafter = len(g_libs[g]) - (1 if (r, c) in g_libs[g] else 0)
                if lafter == 1:
                    sz = len(g_stones[g])
                    score += 35 + sz * 8
                    if sz >= 3:
                        score += 20
                elif lafter == 2:
                    score += 4 + len(g_stones[g]) * 1.0

            # self liberties penalty / bonus
            if captures == 0:
                if n_merged == 1:
                    # self-atari: very bad unless saving large / atari large
                    # allow if it also attacks (atari) to enable snapback, reduce penalty
                    score -= 180
                    # if this self-atari puts opponent in atari too, it's a snapback fight, less bad
                    # check if any opp atari created
                    has_atari = False
                    for g in adj_opp:
                        if len(g_libs[g]) == 2 and (r, c) in g_libs[g]:
                            has_atari = True
                            break
                    if has_atari:
                        score += 100  # net -80, still risky but playable
                elif n_merged == 2:
                    score -= 12
                elif n_merged >= 5:
                    score += 6
                elif n_merged >= 4:
                    score += 3

            # connection / cut
            if len(adj_own) >= 2:
                score += 12 + (len(adj_own)-1) * 8
            elif len(adj_own) == 1:
                score += 3
            if len(adj_opp) >= 2:
                # splitting / surrounding
                score += 10 + (len(adj_opp)-1) * 6

            # eye fill avoidance: own eye
            # orth all own/wall and empty_nb==0
            if empty_nb == 0 and len(adj_opp) == 0 and len(adj_own) > 0:
                # count diagonal own/wall
                diag_own = 0
                for dr, dc in DIAGS:
                    nr, nc = r+dr, c+dc
                    if nr < 0 or nr >= N or nc < 0 or nc >= N:
                        diag_own += 1
                    elif board[nr][nc] == 1:
                        diag_own += 1
                if diag_own >= 3:
                    # true eye, don't fill
                    score -= 250
                else:
                    score -= 60
            elif empty_nb == 0 and captures == 0:
                score -= 80

            # first line / edge positional
            d = r
            if c < d:
                d = c
            t = N-1-r
            if t < d:
                d = t
            t = N-1-c
            if t < d:
                d = t

            if is_opening:
                if d == 0:
                    score -= 12
                elif d == 1:
                    score -= 2
                elif d == 2:
                    score += 8
                elif d == 3:
                    score += 10
                elif d == 4:
                    score += 3
                else:
                    score -= 3
                if (r, c) in stars:
                    score += 6
                # spread in opening: penalize contact
                adj_stones = own_orth + opp_orth
                score -= adj_stones * 1.5
                # prefer corners in very early game
                if total < 12:
                    # corner distance bonus: closer to corner star better
                    # manhattan to nearest corner star
                    score += 0
            else:
                if d == 0:
                    score -= 10
                elif d == 1:
                    score -= 3
                elif d == 2:
                    score += 2
                elif d == 3:
                    score += 3
                # fighting: prefer near stones
                adj_stones = own_orth + opp_orth
                score += adj_stones * 2.5
                # diagonal contact
                diag_touch = 0
                if r > 0 and c > 0 and board[r-1][c-1] != 0:
                    diag_touch += 1
                if r > 0 and c < N-1 and board[r-1][c+1] != 0:
                    diag_touch += 1
                if r < N-1 and c > 0 and board[r+1][c-1] != 0:
                    diag_touch += 1
                if r < N-1 and c < N-1 and board[r+1][c+1] != 0:
                    diag_touch += 1
                score += diag_touch * 1.0
                # proximity in 5x5 for influence (cheap)
                # only compute for promising moves to save time? compute always but limited
                # count stones within distance 2
                cnt = 0
                for dr in (-2,-1,0,1,2):
                    nr = r+dr
                    if nr < 0 or nr >= N:
                        continue
                    row = board[nr]
                    for dc in (-2,-1,0,1,2):
                        if dr == 0 and dc == 0:
                            continue
                        nc = c+dc
                        if nc < 0 or nc >= N:
                            continue
                        if row[nc] != 0:
                            cnt += 1
                if cnt <= 8:
                    score += cnt * 1.2
                else:
                    score += 9.6 - (cnt-8)*0.8

            # tiny random tie-break
            score += random.random() * 2.0

            if score > best_score:
                best_score = score
                best_move = (r, c)

        if best_move is None:
            return ((0, 0), memory)
        # late game pass if only terrible eye-fill left
        if best_score < -150 and total > 100:
            return ((0, 0), memory)
        return ((best_move[0]+1, best_move[1]+1), memory)
    except Exception:
        # fallback: first empty else pass to guarantee legal
        try:
            occ = set(me) | set(opponent)
            for r in range(1, 20):
                for c in range(1, 20):
                    if (r, c) not in occ:
                        return ((r, c), memory)
            return ((0, 0), memory)
        except Exception:
            return ((0, 0), memory)
