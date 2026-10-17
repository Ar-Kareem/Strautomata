
import heapq
import time
import random

N = 11
N2 = 121
INF = 10**9

def _idx(r,c):
    return r*11+c

NEIGH = []
for r in range(11):
    for c in range(11):
        lst = []
        for dr,dc in ((-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < 11 and 0 <= nc < 11:
                lst.append(nr*11+nc)
        NEIGH.append(lst)

TOP = [_idx(0,c) for c in range(11)]
BOTTOM = [_idx(10,c) for c in range(11)]
LEFT = [_idx(r,0) for r in range(11)]
RIGHT = [_idx(r,10) for r in range(11)]
TOP_SET = set(TOP)
BOTTOM_SET = set(BOTTOM)
LEFT_SET = set(LEFT)
RIGHT_SET = set(RIGHT)

def dijkstra_min(cost, starts, goal_set):
    dist = [INF]*N2
    h = []
    for s in starts:
        c = cost[s]
        if c >= INF:
            continue
        if c < dist[s]:
            dist[s] = c
            h.append((c,s))
    heapq.heapify(h)
    while h:
        d,u = heapq.heappop(h)
        if d != dist[u]:
            continue
        if u in goal_set:
            return d
        for v in NEIGH[u]:
            cv = cost[v]
            if cv >= INF:
                continue
            nd = d + cv
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(h,(nd,v))
    return INF

def dijkstra_full(cost, starts):
    dist = [INF]*N2
    h = []
    for s in starts:
        c = cost[s]
        if c >= INF:
            continue
        if c < dist[s]:
            dist[s] = c
            h.append((c,s))
    heapq.heapify(h)
    while h:
        d,u = heapq.heappop(h)
        if d != dist[u]:
            continue
        for v in NEIGH[u]:
            cv = cost[v]
            if cv >= INF:
                continue
            nd = d + cv
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(h,(nd,v))
    return dist

def policy(me, opp, color):
    t0 = time.time()
    try:
        me_set = set(me)
        opp_set = set(opp)
        empties = []
        empty_idx = []
        occ = me_set | opp_set
        for r in range(11):
            for c in range(11):
                if (r,c) not in occ:
                    empties.append((r,c))
                    empty_idx.append(r*11+c)
        if not empties:
            return (0,0)
        if len(empties) == 121:
            return (5,5)
        # quick center opening
        total = len(me_set)+len(opp_set)
        center_empty = (5,5) not in me_set and (5,5) not in opp_set
        if total < 4 and center_empty:
            return (5,5)
        if total < 4 and not center_empty:
            # play adjacent to center
            for rc in [(5,4),(4,5),(6,5),(5,6),(4,4),(6,6),(4,6),(6,4)]:
                if rc not in me_set and rc not in opp_set:
                    return rc

        is_black = (color == 'b')
        if is_black:
            s_me, g_me_set = TOP, BOTTOM_SET
            s_opp, g_opp_set = LEFT, RIGHT_SET
        else:
            s_me, g_me_set = LEFT, RIGHT_SET
            s_opp, g_opp_set = TOP, BOTTOM_SET

        cost_me = [1]*N2
        cost_opp = [1]*N2
        for (r,c) in me_set:
            i = r*11+c
            cost_me[i] = 0
            cost_opp[i] = INF
        for (r,c) in opp_set:
            i = r*11+c
            cost_opp[i] = 0
            cost_me[i] = INF

        D_me0 = dijkstra_min(cost_me, s_me, g_me_set)
        D_opp0 = dijkstra_min(cost_opp, s_opp, g_opp_set)
        if D_me0 >= INF and D_opp0 >= INF:
            # partitioned, just play center-nearest
            empties.sort(key=lambda x: abs(x[0]-5)+abs(x[1]-5))
            return empties[0]

        # full maps for tie break
        if is_black:
            ds_me = dijkstra_full(cost_me, TOP)
            de_me = dijkstra_full(cost_me, BOTTOM)
            ds_opp = dijkstra_full(cost_opp, LEFT)
            de_opp = dijkstra_full(cost_opp, RIGHT)
        else:
            ds_me = dijkstra_full(cost_me, LEFT)
            de_me = dijkstra_full(cost_me, RIGHT)
            ds_opp = dijkstra_full(cost_opp, TOP)
            de_opp = dijkstra_full(cost_opp, BOTTOM)

        through_me = [0]*N2
        through_opp = [0]*N2
        for i in range(N2):
            a = ds_me[i]; b = de_me[i]
            if a >= INF or b >= INF:
                through_me[i] = INF
            else:
                cm = cost_me[i]
                if cm >= INF:
                    through_me[i] = INF
                else:
                    through_me[i] = a + b - cm
            a2 = ds_opp[i]; b2 = de_opp[i]
            if a2 >= INF or b2 >= INF:
                through_opp[i] = INF
            else:
                co = cost_opp[i]
                if co >= INF:
                    through_opp[i] = INF
                else:
                    through_opp[i] = a2 + b2 - co

        # 1-ply simulation
        nE = len(empty_idx)
        D_me_play = [0]*N2
        D_opp_block = [0]*N2
        # mutate in place to avoid alloc
        for e in empty_idx:
            if time.time()-t0 > 0.55:
                break
            cost_me[e] = 0
            d1 = dijkstra_min(cost_me, s_me, g_me_set)
            cost_me[e] = 1
            cost_opp[e] = INF
            d2 = dijkstra_min(cost_opp, s_opp, g_opp_set)
            cost_opp[e] = 1
            D_me_play[e] = d1
            D_opp_block[e] = d2

        # check immediate win
        win_moves = [e for e in empty_idx if D_me_play[e] == 0]
        if win_moves:
            # pick win that blocks most
            win_moves.sort(key=lambda e: D_opp_block[e], reverse=True)
            e = win_moves[0]
            return (e//11, e%11)

        # check immediate loss: opp needs 1
        if D_opp0 == 1:
            # moves that prevent immediate win
            blocks = [e for e in empty_idx if D_opp_block[e] > 1]
            if blocks:
                # prefer block that also advances us
                blocks.sort(key=lambda e: (D_opp_block[e], -D_me_play[e]), reverse=True)
                e = blocks[0]
                return (e//11, e%11)
            # double threat, try best defense
            # fall through to search

        # score 1-ply
        scored = []
        for e in empty_idx:
            # if not computed due to timeout, approximate with through
            d1 = D_me_play[e]
            d2 = D_opp_block[e]
            # if timeout left zero, recompute approx: use through
            # detect uncomputed: both zero and not win case -> use through
            # D can be 0 legitimately only for win which handled, so 0 means uncomputed
            if d1 == 0 and d2 == 0:
                tm = through_me[e] if through_me[e] < INF else 50
                to = through_opp[e] if through_opp[e] < INF else 50
                primary = -(tm+to)*0.05
                scored.append((primary, e))
                continue
            d2c = 100 if d2 >= INF else d2
            d1c = 100 if d1 >= INF else d1
            primary = d2c - d1c
            r = e//11; c = e%11
            tm = through_me[e] if through_me[e] < INF else 50
            to = through_opp[e] if through_opp[e] < INF else 50
            # adjacency bonus
            own_nb = 0; opp_nb = 0
            for nb in NEIGH[e]:
                nr = nb//11; nc = nb%11
                if (nr,nc) in me_set:
                    own_nb += 1
                elif (nr,nc) in opp_set:
                    opp_nb += 1
            secondary = -(tm+to)*0.02 - (abs(r-5)+abs(c-5))*0.02 + (own_nb+opp_nb)*0.05 + random.random()*0.01
            # cap secondary to (-1,1)
            total_s = primary + max(-0.99, min(0.99, secondary))
            scored.append((total_s, e))
        scored.sort(reverse=True, key=lambda x: x[0])
        if not scored:
            return empties[0]
        topK = min(8, len(scored))
        candidates = [scored[i][1] for i in range(topK)]

        # 2-ply minimax on candidates
        # build reply pool: smallest through sum
        # pre-rank all empties by urgency
        urgency = []
        for e in empty_idx:
            tm = through_me[e] if through_me[e] < INF else 50
            to = through_opp[e] if through_opp[e] < INF else 50
            urgency.append((tm+to, e))
        urgency.sort(key=lambda x: x[0])
        pool_size = min(18, len(urgency))
        base_pool = [urgency[i][1] for i in range(pool_size)]

        best_m = candidates[0]
        best_val = -10**9
        # 1-ply best as fallback
        for m in candidates:
            if time.time()-t0 > 0.92:
                break
            # apply m
            cost_me[m] = 0
            cost_opp[m] = INF
            # build reply list: base_pool + neighbors of m
            reply_set = set(base_pool)
            for nb in NEIGH[m]:
                if cost_me[nb] == 1 and cost_opp[nb] == 1:
                    # empty (nb not m, m is blocked now but nb still empty)
                    reply_set.add(nb)
            if m in reply_set:
                reply_set.remove(m)
            reply_list = list(reply_set)
            # limit
            if len(reply_list) > 20:
                # keep most urgent
                reply_list.sort(key=lambda e: (through_me[e] if through_me[e]<INF else 50)+(through_opp[e] if through_opp[e]<INF else 50))
                reply_list = reply_list[:20]
            worst = 10**9
            for n in reply_list:
                # opp plays n
                cost_opp[n] = 0
                cost_me[n] = INF
                d_opp = dijkstra_min(cost_opp, s_opp, g_opp_set)
                d_me = dijkstra_min(cost_me, s_me, g_me_set)
                cost_opp[n] = 1
                cost_me[n] = 1
                d_oppc = 100 if d_opp >= INF else d_opp
                d_mec = 100 if d_me >= INF else d_me
                # value from our perspective: high is good
                # weight defense slightly higher? use 1.0 vs 1.0, but penalize opp win heavily
                if d_opp == 0:
                    v = -200 + d_mec * (-1)
                elif d_me == 0:
                    v = 200 - d_oppc
                else:
                    v = d_oppc - d_mec
                if v < worst:
                    worst = v
                    # alpha prune: if worst already worse than best, break
                    if worst < best_val:
                        # no need to check more replies, this m is bad
                        # but need to finish? can break early
                        pass
                if time.time()-t0 > 0.92:
                    cost_opp[n] = 1
                    cost_me[n] = 1
                    break
            # restore m
            cost_me[m] = 1
            cost_opp[m] = 1
            # tie break with 1-ply score
            # find 1-ply score
            s1 = next((s for s,e in scored if e==m), 0)
            # small bonus for 1-ply to break ties
            worst_total = worst + s1*0.001
            if worst_total > best_val:
                best_val = worst_total
                best_m = m
        return (best_m//11, best_m%11)
    except Exception:
        try:
            occ2 = set(me) | set(opp)
            for r in range(11):
                for c in range(11):
                    if (r,c) not in occ2:
                        return (r,c)
        except Exception:
            return (5,5)
        return (5,5)
