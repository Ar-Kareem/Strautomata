
import heapq
import time

N = 11
DIRS = [(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0)]
INF = 9999

def _dist(player_set, blocker_set, color):
    # shortest number of empties needed for player(color) to connect
    # player_set: stones of player, blocker_set: stones of opponent (blocked)
    # 0 = already connected
    dist = [[INF]*N for _ in range(N)]
    heap = []
    if color == 'b':  # top-bottom
        for c in range(N):
            key = (0, c)
            if key in blocker_set:
                continue
            d = 0 if key in player_set else 1
            if d < dist[0][c]:
                dist[0][c] = d
                heapq.heappush(heap, (d, 0, c))
        def is_target(r, c):
            return r == N-1
    else:  # white left-right
        for r in range(N):
            key = (r, 0)
            if key in blocker_set:
                continue
            d = 0 if key in player_set else 1
            if d < dist[r][0]:
                dist[r][0] = d
                heapq.heappush(heap, (d, r, 0))
        def is_target(r, c):
            return c == N-1
    while heap:
        d, r, c = heapq.heappop(heap)
        if d != dist[r][c]:
            continue
        if is_target(r, c):
            return d
        nd_base = d
        for dr, dc in DIRS:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < N and 0 <= nc < N:
                key = (nr, nc)
                if key in blocker_set:
                    continue
                nd = nd_base + (0 if key in player_set else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(heap, (nd, nr, nc))
    return INF

def _tie(r, c, me_set):
    # small fractional bonus: centrality + friendly adjacency
    cent = (10 - (abs(r-5) + abs(c-5))) * 0.005
    adj = 0
    for dr, dc in DIRS:
        nr = r + dr
        nc = c + dc
        if 0 <= nr < N and 0 <= nc < N and (nr, nc) in me_set:
            adj += 1
    return cent + adj * 0.02

def policy(me, opp, color):
    start = time.time()
    try:
        me_set = set(me)
        opp_set = set(opp)
        opp_color = 'w' if color == 'b' else 'b'

        empty = [(r, c) for r in range(N) for c in range(N) if (r, c) not in me_set and (r, c) not in opp_set]
        if not empty:
            return (0, 0)
        if len(empty) == N*N:
            return (5, 5)
        # quick opening: take center if free
        if len(empty) > N*N - 4:
            if (5, 5) in me_set or (5, 5) in opp_set:
                for cand in [(5,5),(4,5),(6,5),(5,4),(5,6),(4,4),(6,6)]:
                    if cand in empty:
                        # let search decide unless very early; still prefer center adjacency
                        pass
            else:
                return (5, 5)

        # 1-ply ranking
        scored = []  # (score, e, my_d, opp_d)
        # time budget check
        for e in empty:
            me2 = me_set | {e}
            my_d = _dist(me2, opp_set, color)
            if my_d == 0:
                return e  # immediate win
            opp_d = _dist(opp_set, me2, opp_color)
            if opp_d >= INF:
                opp_d = 100
            if my_d >= INF:
                my_d = 100
            s = opp_d - my_d + _tie(e[0], e[1], me_set)
            scored.append((s, e, my_d, opp_d))
            if time.time() - start > 0.45:
                break

        if not scored:
            return empty[0]
        # if we broke early due to time, just return best so far
        scored.sort(key=lambda x: x[0], reverse=True)
        if time.time() - start > 0.5:
            return scored[0][1]

        K = min(len(scored), 12)
        # fewer candidates early to save time, more late for tactics
        if len(empty) > 60:
            K = min(K, 10)
        top = scored[:K]
        top_moves = [e for _, e, _, _ in top]

        best_move = top_moves[0]
        best_val = -1e18

        # 2-ply minimax: my move, opp best reply
        # reply pool = same top moves (likely blocks/attacks)
        R = min(len(top_moves), 10)
        reply_pool = top_moves[:R]

        for _, m, my_d1, opp_d1 in top:
            if time.time() - start > 0.88:
                break
            me2 = me_set | {m}
            # value of m = min over opp replies of (opp_d2 - my_d2)
            worst = 1e18
            # order replies: try most damaging first? replies that were good for opp in 1-ply
            # our top is sorted best-for-me, so worst-for-me is at end; iterate reversed for faster prune
            for o in reversed(reply_pool):
                if o == m:
                    continue
                if time.time() - start > 0.92:
                    break
                opp2 = opp_set | {o}
                my_d2 = _dist(me2, opp2, color)
                if my_d2 >= INF:
                    my_d2 = 100
                opp_d2 = _dist(opp2, me2, opp_color)
                if opp_d2 >= INF:
                    opp_d2 = 100
                # if opp wins immediately after reply, heavily penalize
                if opp_d2 == 0:
                    score2 = -1000
                else:
                    score2 = opp_d2 - my_d2
                if score2 < worst:
                    worst = score2
                # alpha-beta: this m can only get worse
                if worst <= best_val:
                    break
            else:
                pass
            # if no reply considered (1 empty left), use 1-ply score
            if worst == 1e18:
                worst = opp_d1 - my_d1
            # add small tie-break for m to prefer center/connection
            worst_tie = worst + _tie(m[0], m[1], me_set) * 0.2
            if worst_tie > best_val:
                best_val = worst_tie
                best_move = m

        if best_move in empty:
            return best_move
        return scored[0][1]
    except Exception:
        # absolute fallback: first legal
        try:
            occ = set(me) | set(opp)
            for r in range(N):
                for c in range(N):
                    if (r, c) not in occ:
                        return (r, c)
        except Exception:
            pass
        return (5, 5)
