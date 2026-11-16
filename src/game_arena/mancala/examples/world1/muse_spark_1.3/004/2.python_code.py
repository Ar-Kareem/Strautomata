
import time

class _Timeout(Exception):
    pass

def policy(you: list[int], opponent: list[int]) -> int:
    try:
        t_start = time.perf_counter()
        deadline = t_start + 0.90

        y0 = list(you)
        o0 = list(opponent)

        legal_root = [i for i in range(6) if y0[i] > 0]
        if len(legal_root) == 0:
            return 0
        if len(legal_root) == 1:
            return int(legal_root[0])

        # ---------- helpers (local for speed) ----------
        def do_move(y, o, mv):
            # b[0:6]=y pits, b[6]=y store, b[7:13]=o pits
            b0 = y[0]; b1 = y[1]; b2 = y[2]; b3 = y[3]; b4 = y[4]; b5 = y[5]
            bs = y[6]
            c0 = o[0]; c1 = o[1]; c2 = o[2]; c3 = o[3]; c4 = o[4]; c5 = o[5]
            os_ = o[6]
            b = [b0, b1, b2, b3, b4, b5, bs, c0, c1, c2, c3, c4, c5]
            stones = b[mv]
            b[mv] = 0
            q, r = divmod(stones, 13)
            if q:
                for j in range(13):
                    b[j] += q
            if r:
                pos = mv
                for _ in range(r):
                    pos += 1
                    if pos == 13:
                        pos = 0
                    b[pos] += 1
                last = pos
            else:
                last = mv
            extra = (last == 6)
            if (not extra) and last < 6 and b[last] == 1:
                opp_idx = 12 - last
                if b[opp_idx] > 0:
                    b[6] += b[last] + b[opp_idx]
                    b[last] = 0
                    b[opp_idx] = 0
            new_y = [b[0], b[1], b[2], b[3], b[4], b[5], b[6]]
            new_o = [b[7], b[8], b[9], b[10], b[11], b[12], os_]
            return new_y, new_o, extra

        def is_term(y, o):
            return (y[0] == 0 and y[1] == 0 and y[2] == 0 and y[3] == 0 and y[4] == 0 and y[5] == 0) or \
                   (o[0] == 0 and o[1] == 0 and o[2] == 0 and o[3] == 0 and o[4] == 0 and o[5] == 0)

        def term_val(y, o, is_max):
            sy = y[6] + y[0] + y[1] + y[2] + y[3] + y[4] + y[5]
            so = o[6] + o[0] + o[1] + o[2] + o[3] + o[4] + o[5]
            if is_max:
                return (sy - so) * 10.0
            else:
                return (so - sy) * 10.0

        def heuristic(y, o, is_max):
            if is_max:
                rs = y[6]; os_ = o[6]
                sum_r = y[0]+y[1]+y[2]+y[3]+y[4]+y[5]
                sum_o = o[0]+o[1]+o[2]+o[3]+o[4]+o[5]
                pos_r = y[1]+2*y[2]+3*y[3]+4*y[4]+5*y[5]
                pos_o = o[1]+2*o[2]+3*o[3]+4*o[4]+5*o[5]
                mob_r = (y[0]>0)+(y[1]>0)+(y[2]>0)+(y[3]>0)+(y[4]>0)+(y[5]>0)
                mob_o = (o[0]>0)+(o[1]>0)+(o[2]>0)+(o[3]>0)+(o[4]>0)+(o[5]>0)
                return (rs - os_) + 0.15*(sum_r - sum_o) + 0.02*(pos_r - pos_o) + 0.05*(mob_r - mob_o) + 0.1
            else:
                rs = o[6]; os_ = y[6]
                sum_r = o[0]+o[1]+o[2]+o[3]+o[4]+o[5]
                sum_o = y[0]+y[1]+y[2]+y[3]+y[4]+y[5]
                pos_r = o[1]+2*o[2]+3*o[3]+4*o[4]+5*o[5]
                pos_o = y[1]+2*y[2]+3*y[3]+4*y[4]+5*y[5]
                mob_r = (o[0]>0)+(o[1]>0)+(o[2]>0)+(o[3]>0)+(o[4]>0)+(o[5]>0)
                mob_o = (y[0]>0)+(y[1]>0)+(y[2]>0)+(y[3]>0)+(y[4]>0)+(y[5]>0)
                return (rs - os_) + 0.15*(sum_r - sum_o) + 0.02*(pos_r - pos_o) + 0.05*(mob_r - mob_o) - 0.1

        nodes = [0]

        def check_timeout():
            if (nodes[0] & 1023) == 0:
                if time.perf_counter() > deadline:
                    raise _Timeout()

        import sys
        sys.setrecursionlimit(10000)

        def search(y, o, is_max, depth, alpha, beta):
            nodes[0] += 1
            check_timeout()
            if is_term(y, o):
                return term_val(y, o, is_max)
            if depth <= 0:
                return heuristic(y, o, is_max)

            # generate children
            # collect (mv, new_y, new_o, extra, gain)
            children = []
            y6 = y[6]
            for mv in range(6):
                if y[mv] == 0:
                    continue
                ny, no, ex = do_move(y, o, mv)
                gain = ny[6] - y6
                # order key: extra first, then gain
                key = (1 if ex else 0) * 1000 + gain
                children.append((key, mv, ny, no, ex))
            if not children:
                return term_val(y, o, is_max)
            # best-first for player to move
            children.sort(key=lambda x: x[0], reverse=True)

            if is_max:
                best = -1e18
                for _, mv, ny, no, ex in children:
                    if ex:
                        v = search(ny, no, True, depth-1, alpha, beta)
                    else:
                        v = search(no, ny, False, depth-1, alpha, beta)
                    if v > best:
                        best = v
                    if best > alpha:
                        alpha = best
                    if alpha >= beta:
                        break
                return best
            else:
                best = 1e18
                for _, mv, ny, no, ex in children:
                    if ex:
                        v = search(ny, no, False, depth-1, alpha, beta)
                    else:
                        v = search(no, ny, True, depth-1, alpha, beta)
                    if v < best:
                        best = v
                    if best < beta:
                        beta = best
                    if alpha >= beta:
                        break
                return best

        # initial greedy ordering for root
        init_infos = []
        for mv in legal_root:
            ny, no, ex = do_move(y0, o0, mv)
            gain = ny[6] - y0[6]
            key = (1 if ex else 0) * 1000 + gain + ny[5]*0.01
            init_infos.append((key, mv, ny, no, ex))
        init_infos.sort(key=lambda x: x[0], reverse=True)
        best_move = int(init_infos[0][1])

        # if game already terminal (opp empty), just return greedy
        if is_term(y0, o0):
            return best_move

        # iterative deepening
        # order list evolves with search results
        ordered = init_infos
        max_depth = 15
        for depth in range(1, max_depth+1):
            if time.perf_counter() > deadline - 0.02:
                break
            try:
                alpha = -1e18
                beta = 1e18
                cur_best_val = -1e18
                cur_best_mv = ordered[0][1]
                # search in current order
                for _, mv, ny, no, ex in ordered:
                    if ex:
                        v = search(ny, no, True, depth-1, alpha, beta)
                    else:
                        v = search(no, ny, False, depth-1, alpha, beta)
                    if v > cur_best_val:
                        cur_best_val = v
                        cur_best_mv = mv
                    if v > alpha:
                        alpha = v
                best_move = int(cur_best_mv)
                # re-order by value for next iteration: re-evaluate quickly?
                # build new ordered with values
                scored = []
                for _, mv, ny, no, ex in ordered:
                    # quick re-score using last search would need values; approximate by re-search? just move best first
                    pass
                # move best first
                new_ordered = []
                best_info = None
                for info in ordered:
                    if info[1] == best_move:
                        best_info = info
                    else:
                        new_ordered.append(info)
                if best_info is not None:
                    ordered = [best_info] + new_ordered
                # early exit if winning by huge margin and deep enough
                if cur_best_val > 500 and depth >= 6:
                    break
                # if time low, stop deepening
                if time.perf_counter() > deadline - 0.05:
                    break
            except _Timeout:
                break
            except Exception:
                break

        if best_move not in legal_root:
            return int(legal_root[0])
        return int(best_move)
    except Exception:
        try:
            for i in range(6):
                if you[i] > 0:
                    return int(i)
        except Exception:
            pass
        return 0
