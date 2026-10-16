
from collections import deque
import time

N = 11
NN = 121
INF = 10 ** 9
CAP = 100

NEIGH = []
for r in range(N):
    for c in range(N):
        lst = []
        for dr, dc in ((0, 1), (0, -1), (-1, 0), (1, 0), (-1, 1), (1, -1)):
            nr = r + dr
            nc = c + dc
            if 0 <= nr < N and 0 <= nc < N:
                lst.append(nr * N + nc)
        NEIGH.append(lst)

def shortest(board, player, is_black):
    dist = [INF] * NN
    dq = deque()
    if is_black:
        for c in range(N):
            i = c
            b = board[i]
            if b != 0 and b != player:
                continue
            cost = 0 if b == player else 1
            if cost < dist[i]:
                dist[i] = cost
                if cost == 0:
                    dq.appendleft(i)
                else:
                    dq.append(i)
    else:
        for r in range(N):
            i = r * N
            b = board[i]
            if b != 0 and b != player:
                continue
            cost = 0 if b == player else 1
            if cost < dist[i]:
                dist[i] = cost
                if cost == 0:
                    dq.appendleft(i)
                else:
                    dq.append(i)
    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in NEIGH[u]:
            if dist[v] <= du:
                continue
            b = board[v]
            if b != 0 and b != player:
                continue
            w = 0 if b == player else 1
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)
    if is_black:
        best = INF
        base = 10 * N
        for c in range(N):
            d = dist[base + c]
            if d < best:
                best = d
        return best
    else:
        best = INF
        for r in range(N):
            d = dist[r * N + 10]
            if d < best:
                best = d
        return best

def is_win(board, player, is_black):
    visited = [False] * NN
    stack = []
    if is_black:
        for c in range(N):
            i = c
            if board[i] == player and not visited[i]:
                visited[i] = True
                stack.append(i)
    else:
        for r in range(N):
            i = r * N
            if board[i] == player and not visited[i]:
                visited[i] = True
                stack.append(i)
    while stack:
        u = stack.pop()
        if is_black:
            if u // N == 10:
                return True
        else:
            if u % N == 10:
                return True
        for v in NEIGH[u]:
            if not visited[v] and board[v] == player:
                visited[v] = True
                stack.append(v)
    return False

def capd(d):
    return CAP if d >= INF else d

def policy(me, opp, color):
    try:
        start = time.time()
        is_me_black = (color == 'b')
        is_opp_black = not is_me_black
        board = [0] * NN
        for r, c in me:
            if 0 <= r < N and 0 <= c < N:
                board[r * N + c] = 1
        for r, c in opp:
            if 0 <= r < N and 0 <= c < N:
                board[r * N + c] = 2
        empties = [i for i in range(NN) if board[i] == 0]
        if not empties:
            return (0, 0)
        if len(empties) == NN:
            return (5, 5)
        # quick centre opening if board almost empty
        if len(empties) >= NN - 2:
            if board[5 * N + 5] == 0:
                return (5, 5)

        d_me0 = shortest(board, 1, is_me_black)
        d_op0 = shortest(board, 2, is_opp_black)
        if d_me0 == 0 or d_op0 == 0:
            e = empties[0]
            return (e // N, e % N)

        # immediate winning moves
        my_wins = []
        if d_me0 == 1:
            for e in empties:
                board[e] = 1
                if is_win(board, 1, is_me_black):
                    my_wins.append(e)
                board[e] = 0
                if time.time() - start > 0.85:
                    break
            if my_wins:
                # prefer win that also blocks opponent
                for e in my_wins:
                    board[e] = 1
                    ow = is_win(board, 2, is_opp_black) if False else False
                    board[e] = 0
                # if opponent also threatens, pick intersection
                # compute opp wins quickly for intersection
                # just return first win (any wins immediately)
                # prefer central win on tie
                my_wins.sort(key=lambda x: abs(x // N - 5) + abs(x % N - 5))
                # check intersection with opp wins if cheap
                if d_op0 == 1:
                    opp_tmp = set()
                    for e in empties:
                        board[e] = 2
                        if is_win(board, 2, is_opp_black):
                            opp_tmp.add(e)
                        board[e] = 0
                    inter = [e for e in my_wins if e in opp_tmp]
                    if inter:
                        e = inter[0]
                        return (e // N, e % N)
                e = my_wins[0]
                return (e // N, e % N)

        opp_wins = []
        if d_op0 == 1:
            for e in empties:
                board[e] = 2
                if is_win(board, 2, is_opp_black):
                    opp_wins.append(e)
                board[e] = 0
                if time.time() - start > 0.9:
                    break
            if len(opp_wins) == 1:
                e = opp_wins[0]
                return (e // N, e % N)

        # candidate pool
        if len(opp_wins) > 1:
            pool = list(opp_wins)
        else:
            pool = empties

        # 1-ply evaluation
        scores = {}
        dme_map = {}
        dop_map = {}
        best1 = pool[0]
        best1_score = -1e18
        for e in pool:
            board[e] = 1
            dm = capd(shortest(board, 1, is_me_black))
            do = capd(shortest(board, 2, is_opp_black))
            board[e] = 0
            r = e // N
            c = e % N
            friendly = 0
            for nb in NEIGH[e]:
                if board[nb] == 1:
                    friendly += 1
            centre = abs(r - 5) + abs(c - 5)
            eps = 0.05 * friendly - 0.02 * centre
            s = float(do - dm) + eps * 0.1
            # store integer part for minimax plus eps for ordering
            scores[e] = s
            dme_map[e] = dm
            dop_map[e] = do
            if s > best1_score:
                best1_score = s
                best1 = e
            if time.time() - start > 0.55 and len(scores) > 10:
                # not enough time for full 1-ply, break and use best so far
                # but try to finish 1-ply if pool small
                if len(pool) > 30:
                    break
        if len(scores) == 0:
            e = empties[0]
            return (e // N, e % N)
        # order pool by score
        ordered = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        # top K for deep search
        ne = len(empties)
        if ne < 15:
            K = len(ordered)
        elif ne < 40:
            K = min(len(ordered), 12)
        else:
            K = min(len(ordered), 10)
        topK = ordered[:K]

        # if only one candidate or no time, return best1
        if K <= 1 or time.time() - start > 0.8:
            return (best1 // N, best1 % N)

        # order opponent replies: best for us first (opponent wants to block them)
        # full remaining empties ordered by our 1-ply score (fallback centre)
        opp_order = sorted(empties, key=lambda x: scores.get(x, -abs(x // N - 5) - abs(x % N - 5)), reverse=True)

        best_m = best1
        # integer value of best
        best_val = capd(dop_map.get(best1, 0)) - capd(dme_map.get(best1, 0))

        for m in topK:
            if time.time() - start > 0.92:
                break
            board[m] = 1
            cur_min = 1000
            for o in opp_order:
                if o == m or board[o] != 0:
                    continue
                board[o] = 2
                dm2 = capd(shortest(board, 1, is_me_black))
                do2 = capd(shortest(board, 2, is_opp_black))
                board[o] = 0
                v = do2 - dm2
                if v < cur_min:
                    cur_min = v
                    if cur_min < best_val:
                        break
                # periodic time check
            board[m] = 0
            if cur_min > best_val or (cur_min == best_val and scores.get(m, 0) > scores.get(best_m, 0)):
                best_val = cur_min
                best_m = m
                # early exit if we found a move that keeps opponent far
                # keep searching for better
        return (best_m // N, best_m % N)
    except Exception:
        try:
            occ = set(me) | set(opp)
            for r in range(11):
                for c in range(11):
                    if (r, c) not in occ:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
