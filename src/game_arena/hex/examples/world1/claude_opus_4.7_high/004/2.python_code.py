
import heapq

N = 11
NEIGHBOR_OFFSETS = [(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0)]
INF = 10**9

def dijkstra_from(sources, me_set, opp_set):
    dist = [INF] * (N*N)
    pq = []
    for r, c in sources:
        if (r, c) in opp_set:
            continue
        d = 0 if (r, c) in me_set else 1
        idx = r*N + c
        if d < dist[idx]:
            dist[idx] = d
            heapq.heappush(pq, (d, idx))
    while pq:
        d, idx = heapq.heappop(pq)
        if d > dist[idx]:
            continue
        r, c = divmod(idx, N)
        for dr, dc in NEIGHBOR_OFFSETS:
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N:
                if (nr, nc) in opp_set:
                    continue
                nd = d + (0 if (nr, nc) in me_set else 1)
                nidx = nr*N + nc
                if nd < dist[nidx]:
                    dist[nidx] = nd
                    heapq.heappush(pq, (nd, nidx))
    return dist

def min_connection_cost(me_set, opp_set, color):
    if color == 'b':
        s1 = [(0, c) for c in range(N)]
        d = dijkstra_from(s1, me_set, opp_set)
        return min(d[10*N + c] for c in range(N))
    else:
        s1 = [(r, 0) for r in range(N)]
        d = dijkstra_from(s1, me_set, opp_set)
        return min(d[r*N + 10] for r in range(N))

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)

    if len(me) == 0 and len(opp) == 0:
        return (5, 5)

    opp_color = 'w' if color == 'b' else 'b'

    if color == 'b':
        my_s1 = [(0, c) for c in range(N)]
        my_s2 = [(10, c) for c in range(N)]
    else:
        my_s1 = [(r, 0) for r in range(N)]
        my_s2 = [(r, 10) for r in range(N)]
    if opp_color == 'b':
        opp_s1 = [(0, c) for c in range(N)]
        opp_s2 = [(10, c) for c in range(N)]
    else:
        opp_s1 = [(r, 0) for r in range(N)]
        opp_s2 = [(r, 10) for r in range(N)]

    d_my1 = dijkstra_from(my_s1, me_set, opp_set)
    d_my2 = dijkstra_from(my_s2, me_set, opp_set)
    d_opp1 = dijkstra_from(opp_s1, opp_set, me_set)
    d_opp2 = dijkstra_from(opp_s2, opp_set, me_set)

    empty = [(r, c) for r in range(N) for c in range(N)
             if (r, c) not in me_set and (r, c) not in opp_set]

    if not empty:
        return (0, 0)

    candidates = []
    fallback_score = -INF
    fallback_move = empty[0]
    for r, c in empty:
        idx = r*N + c
        m1, m2 = d_my1[idx], d_my2[idx]
        o1, o2 = d_opp1[idx], d_opp2[idx]
        if m1 >= INF or m2 >= INF:
            my_through = 2*INF
        else:
            my_through = m1 + m2
        if o1 >= INF or o2 >= INF:
            opp_through = 2*INF
        else:
            opp_through = o1 + o2
        heur = -(my_through + opp_through)
        if heur > fallback_score:
            fallback_score = heur
            fallback_move = (r, c)
        candidates.append((heur, r, c))

    candidates.sort(reverse=True)
    top_k = candidates[:25]

    best_score = (-INF, -INF)
    best_move = fallback_move

    for heur, r, c in top_k:
        new_me_set = me_set | {(r, c)}
        md = min_connection_cost(new_me_set, opp_set, color)
        od = min_connection_cost(opp_set, new_me_set, opp_color)
        score = (od - md, heur)
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
