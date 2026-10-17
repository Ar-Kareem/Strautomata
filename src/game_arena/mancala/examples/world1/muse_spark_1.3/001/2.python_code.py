
import time

INF = 10000

def policy(you: list[int], opponent: list[int]) -> int:
    try:
        start = time.perf_counter()
        deadline = start + 0.90

        legal = [i for i in range(6) if you[i] > 0]
        if not legal:
            return 0
        if len(legal) == 1:
            return int(legal[0])

        # copy root
        root_cur = [int(x) for x in you]
        root_other = [int(x) for x in opponent]

        class Timeout(Exception):
            pass

        # fast apply, creates new lists
        def do_move(cur, other, i):
            new_cur = cur[:]  # len 7
            new_other = other[:]
            seeds = new_cur[i]
            new_cur[i] = 0
            pos = i
            # sow seeds times
            for _ in range(seeds):
                pos += 1
                if pos == 13:
                    pos = 0
                if pos <= 5:
                    new_cur[pos] += 1
                elif pos == 6:
                    new_cur[6] += 1
                else:
                    new_other[pos - 7] += 1
            extra = (pos == 6)
            if pos <= 5:
                if new_cur[pos] == 1:
                    opp_idx = 5 - pos
                    if new_other[opp_idx] > 0:
                        new_cur[6] += 1 + new_other[opp_idx]
                        new_cur[pos] = 0
                        new_other[opp_idx] = 0
            return new_cur, new_other, extra

        def sums(cur, other):
            sc = cur[0]+cur[1]+cur[2]+cur[3]+cur[4]+cur[5]
            so = other[0]+other[1]+other[2]+other[3]+other[4]+other[5]
            return sc, so

        def terminal_val(cur, other, sc, so):
            # from cur perspective
            if sc == 0 and so == 0:
                return float(cur[6] - other[6])
            elif sc == 0:
                return float(cur[6] - (other[6] + so))
            else:  # so == 0
                return float((cur[6] + sc) - other[6])

        def heuristic(cur, other, sc, so):
            store_diff = cur[6] - other[6]
            pit_diff = sc - so
            total = store_diff + 0  # placeholder
            # total seeds
            tot = cur[6] + other[6] + sc + so
            if tot == 0:
                w = 0.9
            else:
                prog = (cur[6] + other[6]) / tot  # 0..1
                w = 0.15 + 0.75 * prog
            # mobility
            mob_c = (1 if cur[0]>0 else 0)+(1 if cur[1]>0 else 0)+(1 if cur[2]>0 else 0)+(1 if cur[3]>0 else 0)+(1 if cur[4]>0 else 0)+(1 if cur[5]>0 else 0)
            mob_o = (1 if other[0]>0 else 0)+(1 if other[1]>0 else 0)+(1 if other[2]>0 else 0)+(1 if other[3]>0 else 0)+(1 if other[4]>0 else 0)+(1 if other[5]>0 else 0)
            return float(store_diff + w * pit_diff + 0.05 * (mob_c - mob_o))

        nodes = [0]

        def negamax(cur, other, depth, alpha, beta):
            nodes[0] += 1
            if (nodes[0] & 1023) == 0:
                if time.perf_counter() >= deadline:
                    raise Timeout()
            sc = cur[0]+cur[1]+cur[2]+cur[3]+cur[4]+cur[5]
            so = other[0]+other[1]+other[2]+other[3]+other[4]+other[5]
            if sc == 0 or so == 0:
                if sc == 0 and so == 0:
                    return float(cur[6] - other[6])
                elif sc == 0:
                    return float(cur[6] - (other[6] + so))
                else:
                    return float((cur[6] + sc) - other[6])
            if depth <= 0:
                return heuristic(cur, other, sc, so)

            # generate moves
            # order: extra first, then capture approx, then seeds desc
            moves = []
            for i in range(6):
                s = cur[i]
                if s > 0:
                    moves.append(i)
            # quick ordering scores
            scored = []
            for i in moves:
                s = cur[i]
                final = (i + s) % 13
                is_extra = 1 if final == 6 else 0
                is_cap = 0
                if final <= 5:
                    # approx empty check (exact when s<13)
                    # need cur[final]==0 except when final==i (emptied)
                    if final == i:
                        # after empty, before last drop 0 if s%13==0? actually 0, but intermediate fills?
                        # treat as not capture for ordering unless s%13==0
                        if s % 13 == 0:
                            # lands back to start, was 0
                            if other[5-final] > 0:
                                is_cap = 1
                    else:
                        if cur[final] == 0 and other[5-final] > 0:
                            is_cap = 1
                # score: extra dominates, then cap, then seeds
                score = is_extra * 1000 + is_cap * 100 + s
                scored.append((score, i))
            scored.sort(reverse=True)
            ordered = [i for _, i in scored]

            best = -INF
            for m in ordered:
                nc, no, extra = do_move(cur, other, m)
                # terminal after move?
                sc2 = nc[0]+nc[1]+nc[2]+nc[3]+nc[4]+nc[5]
                so2 = no[0]+no[1]+no[2]+no[3]+no[4]+no[5]
                if sc2 == 0 or so2 == 0:
                    if sc2 == 0 and so2 == 0:
                        val = float(nc[6] - no[6])
                    elif sc2 == 0:
                        val = float(nc[6] - (no[6] + so2))
                    else:
                        val = float((nc[6] + sc2) - no[6])
                else:
                    if extra:
                        val = negamax(nc, no, depth-1, alpha, beta)
                    else:
                        val = -negamax(no, nc, depth-1, -beta, -alpha)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best

        # initial root ordering: extra first
        def root_order(lst, cur):
            tmp = []
            for i in lst:
                s = cur[i]
                is_extra = 1 if (i + s) % 13 == 6 else 0
                tmp.append((is_extra, s, i))
            tmp.sort(reverse=True)
            return [i for _, _, i in tmp]

        ordered_root = root_order(legal, root_cur)
        best_move = int(ordered_root[0])

        # iterative deepening
        max_depth = 20
        for depth in range(1, max_depth+1):
            if time.perf_counter() >= deadline:
                break
            try:
                alpha = -INF
                beta = INF
                scores = {}
                # search in current order
                for m in ordered_root:
                    if time.perf_counter() >= deadline:
                        raise Timeout()
                    nc, no, extra = do_move(root_cur, root_other, m)
                    sc2 = nc[0]+nc[1]+nc[2]+nc[3]+nc[4]+nc[5]
                    so2 = no[0]+no[1]+no[2]+no[3]+no[4]+no[5]
                    if sc2 == 0 or so2 == 0:
                        if sc2 == 0 and so2 == 0:
                            val = float(nc[6] - no[6])
                        elif sc2 == 0:
                            val = float(nc[6] - (no[6] + so2))
                        else:
                            val = float((nc[6] + sc2) - no[6])
                    else:
                        if extra:
                            val = negamax(nc, no, depth-1, alpha, beta)
                        else:
                            val = -negamax(no, nc, depth-1, -beta, -alpha)
                    scores[m] = val
                    if val > alpha:
                        alpha = val
                        best_move = int(m)
                # reorder for next depth
                ordered_root = sorted(ordered_root, key=lambda x: scores.get(x, -INF), reverse=True)
                best_move = int(ordered_root[0])
                # early exit if winning by max possible? total seeds bound
                # if time low break
                if time.perf_counter() >= deadline:
                    break
            except Timeout:
                break

        if best_move not in legal:
            return int(legal[0])
        return int(best_move)
    except Exception:
        try:
            for i in range(6):
                if you[i] > 0:
                    return int(i)
        except Exception:
            pass
        return 0
