
import collections
import time

N = 11
NN = N * N
INF = 1000

# precompute hex neighbours: all 8 except (i-1,j-1),(i+1,j+1)
NB = [[] for _ in range(NN)]
for r in range(N):
    for c in range(N):
        idx = r * N + c
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if dr == -1 and dc == -1:
                    continue
                if dr == 1 and dc == 1:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    NB[idx].append(nr * N + nc)

CENTER_DIST = [0] * NN
for r in range(N):
    for c in range(N):
        CENTER_DIST[r * N + c] = abs(r - 5) + abs(c - 5)

_deque = collections.deque

def _bfs(board, starts, ends_list, own, blocked, need_path=True):
    dist = [INF] * NN
    parent = [-1] * NN if need_path else None
    dq = _deque()
    for s in starts:
        v = board[s]
        if v == blocked:
            continue
        c = 0 if v == own else 1
        if c < dist[s]:
            dist[s] = c
            if need_path:
                parent[s] = -2
            if c == 0:
                dq.appendleft(s)
            else:
                dq.append(s)
    nb_local = NB
    while dq:
        u = dq.popleft()
        du = dist[u]
        for w in nb_local[u]:
            bw = board[w]
            if bw == blocked:
                continue
            cw = 0 if bw == own else 1
            nd = du + cw
            if nd < dist[w]:
                dist[w] = nd
                if need_path:
                    parent[w] = u
                if cw == 0:
                    dq.appendleft(w)
                else:
                    dq.append(w)
    best = INF
    best_e = -1
    for e in ends_list:
        d = dist[e]
        if d < best:
            best = d
            best_e = e
            if best == 0:
                break
    if best >= INF:
        return (INF, [])
    if not need_path:
        return (best, [])
    path = []
    cur = best_e
    while cur != -2 and cur != -1:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return (best, path)


def policy(me, opp, color):
    try:
        t0 = time.perf_counter()
        def out_of_time(limit=0.92):
            return (time.perf_counter() - t0) > limit

        board = [0] * NN
        for (r, c) in me:
            if 0 <= r < N and 0 <= c < N:
                board[r * N + c] = 1
        for (r, c) in opp:
            if 0 <= r < N and 0 <= c < N:
                board[r * N + c] = 2
        empties = [i for i, v in enumerate(board) if v == 0]
        if not empties:
            return (0, 0)
        if len(empties) == NN:
            return (5, 5)
        # single stone opening: take centre if free
        if len(empties) >= NN - 1 and board[5 * N + 5] == 0:
            return (5, 5)

        is_black = True
        try:
            if isinstance(color, str) and len(color) > 0 and color[0] == 'w':
                is_black = False
        except Exception:
            is_black = True

        if is_black:
            starts_my = [c for c in range(N)]  # row 0
            ends_my = [(N - 1) * N + c for c in range(N)]  # row 10
            starts_opp = [r * N for r in range(N)]  # col 0
            ends_opp = [r * N + (N - 1) for r in range(N)]  # col 10
        else:
            starts_my = [r * N for r in range(N)]
            ends_my = [r * N + (N - 1) for r in range(N)]
            starts_opp = [c for c in range(N)]
            ends_opp = [(N - 1) * N + c for c in range(N)]

        # initial distances + paths
        md0, path_md0 = _bfs(board, starts_my, ends_my, 1, 2, True)
        od0, path_od0 = _bfs(board, starts_opp, ends_opp, 2, 1, True)

        if md0 >= INF and od0 >= INF:
            # fully blocked strange, play centre-most empty
            empties.sort(key=lambda x: CENTER_DIST[x])
            e = empties[0]
            return (e // N, e % N)
        if md0 == 0 or od0 == 0:
            # game already decided, play centre-most
            empties.sort(key=lambda x: CENTER_DIST[x])
            e = empties[0]
            return (e // N, e % N)

        # immediate win ?
        if md0 == 1:
            # try path cells first
            cands = [x for x in path_md0 if board[x] == 0]
            for x in empties:
                if x not in cands:
                    # keep order: path first then rest; build ordered list
                    pass
            ordered = cands + [x for x in empties if x not in set(cands)]
            for e in ordered:
                board[e] = 1
                d, _ = _bfs(board, starts_my, ends_my, 1, 2, False)
                board[e] = 0
                if d == 0:
                    return (e // N, e % N)
                if out_of_time(0.5):
                    break

        # immediate loss block ?
        opp_wins = []
        if od0 == 1:
            cands_o = [x for x in path_od0 if board[x] == 0]
            # need full scan to find all wins
            # scan path cells first for speed, then rest
            ordered_o = cands_o + [x for x in empties if x not in set(cands_o)]
            for e in ordered_o:
                board[e] = 2
                d, _ = _bfs(board, starts_opp, ends_opp, 2, 1, False)
                board[e] = 0
                if d == 0:
                    opp_wins.append(e)
                if out_of_time(0.5):
                    break
            if len(opp_wins) == 1:
                e = opp_wins[0]
                return (e // N, e % N)
            if len(opp_wins) > 1:
                # must block among them: evaluate best among them below
                # restrict pool
                pool = opp_wins
                # fall through to search restricted to pool
                # quick 1-ply to pick best block
                best_e = pool[0]
                best_score = -10**9
                for e in pool:
                    board[e] = 1
                    md, _ = _bfs(board, starts_my, ends_my, 1, 2, False)
                    od, _ = _bfs(board, starts_opp, ends_opp, 2, 1, False)
                    board[e] = 0
                    s = od - md
                    # tie break centre
                    s2 = s * 100 - CENTER_DIST[e] * 0.1 - md * 0.5
                    if s2 > best_score:
                        best_score = s2
                        best_e = e
                return (best_e // N, best_e % N)

        # 1-ply evaluation over all empties
        # store md, od, D
        mds = {}
        ods = {}
        Ds = {}
        # order empties by centre for early win detection already done
        for e in empties:
            board[e] = 1
            md, _ = _bfs(board, starts_my, ends_my, 1, 2, False)
            od, _ = _bfs(board, starts_opp, ends_opp, 2, 1, False)
            board[e] = 0
            if md == 0:
                return (e // N, e % N)
            mds[e] = md
            ods[e] = od
            Ds[e] = od - md
            if out_of_time(0.55):
                # incomplete: fill remaining with heuristic and break
                # assign remaining a default bad score
                for ee in empties:
                    if ee not in Ds:
                        Ds[ee] = -1000
                        mds[ee] = 100
                        ods[ee] = 0
                break

        # sort by D desc, md asc, centre asc
        ranked = sorted(empties, key=lambda x: (-Ds.get(x, -1000), mds.get(x, 100), CENTER_DIST[x]))

        # if little time left, return best 1-ply
        if out_of_time(0.6):
            e = ranked[0]
            return (e // N, e % N)

        K = 10
        if len(empties) < 25:
            K = 12
        if len(empties) > 80:
            K = 8
        topk = ranked[:K] if len(ranked) > K else ranked

        best_move = topk[0]
        best_D2 = -10**9
        best_D = -10**9
        best_md = 10**9

        for e in topk:
            if out_of_time():
                break
            board[e] = 1
            md_e, p_my = _bfs(board, starts_my, ends_my, 1, 2, True)
            od_e, p_opp = _bfs(board, starts_opp, ends_opp, 2, 1, True)
            D_e = od_e - md_e
            # reply candidates: empty cells on either shortest path
            reply_set = set()
            for x in p_my:
                if board[x] == 0:
                    reply_set.add(x)
            for x in p_opp:
                if board[x] == 0:
                    reply_set.add(x)
            if not reply_set:
                D2 = D_e
            else:
                # limit reply set size if huge (keep most central? keep all, path len small)
                if len(reply_set) > 30:
                    reply_list = sorted(list(reply_set), key=lambda x: CENTER_DIST[x])[:30]
                    reply_set = set(reply_list)
                worst = 10**9
                for f in reply_set:
                    board[f] = 2
                    md_ef, _ = _bfs(board, starts_my, ends_my, 1, 2, False)
                    od_ef, _ = _bfs(board, starts_opp, ends_opp, 2, 1, False)
                    board[f] = 0
                    d_ef = od_ef - md_ef
                    if d_ef < worst:
                        worst = d_ef
                        # pruning: if worst already worse than best found, can stop?
                        # we keep searching for exact min for this e, but early exit if
                        # worst < best_D2 and we only care about max? Actually need min,
                        # if min already below best_D2, this e cannot beat best -> prune
                        if worst < best_D2:
                            # still need? no, e is worse, prune remaining replies
                            # break out to save time (pessimistic prune is exact for maximin)
                            # we can break because worst can only decrease
                            break
                    if out_of_time():
                        break
                D2 = worst
            board[e] = 0
            # compare: primary D2, secondary D_e, tertiary -md_e, centre
            better = False
            if D2 > best_D2:
                better = True
            elif D2 == best_D2:
                if D_e > best_D:
                    better = True
                elif D_e == best_D:
                    if md_e < best_md:
                        better = True
                    elif md_e == best_md:
                        if CENTER_DIST[e] < CENTER_DIST[best_move]:
                            better = True
            if better:
                best_D2 = D2
                best_D = D_e
                best_md = md_e
                best_move = e

        return (best_move // N, best_move % N)
    except Exception:
        try:
            occ = set(me) | set(opp)
            for r in range(N):
                for c in range(N):
                    if (r, c) not in occ:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
