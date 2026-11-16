
def _xor_sum(p):
    x = 0
    for v in p:
        x ^= v
    return x

def _is_P(p):
    # True if P-position (losing for player to move) under misere (last loses)
    # terminal [0,0,0,0] is N (previous player lost), handled as k=0 even -> False
    big = sum(1 for v in p if v > 1)
    k = sum(1 for v in p if v == 1)
    if big == 0:
        return (k % 2 == 1)
    if big == 1:
        return False
    return (_xor_sum(p) == 0)

def _big_count(p):
    return sum(1 for v in p if v > 1)

def policy(piles: list[int]) -> str:
    try:
        p = list(piles)
        # terminal: no move, must return something
        if sum(p) == 0:
            return "0,1"
        # first legal fallback
        fallback = None
        for i in range(4):
            if i < len(p) and p[i] > 0:
                fallback = f"{i},1"
                break
        if fallback is None:
            return "0,1"

        # enumerate all moves (cap for huge piles)
        total_sum = sum(p)
        # helper to apply move
        def apply(idx, take):
            q = p.copy()
            q[idx] -= take
            return q

        # Find winning moves to P
        # Use theory for speed when huge, else brute
        if total_sum > 300:
            # theory direct move
            big = _big_count(p)
            k = sum(1 for v in p if v == 1)
            x = _xor_sum(p)
            if big == 0:
                # k even -> N, take one
                for i in range(4):
                    if p[i] > 0:
                        return f"{i},1"
                return fallback
            if big == 1:
                # must be N, reduce large to 0/1 for odd
                large_idx = max(range(4), key=lambda i: p[i])
                if k % 2 == 1:  # odd -> take all
                    return f"{large_idx},{p[large_idx]}"
                else:
                    take = p[large_idx] - 1
                    if take < 1:
                        take = 1
                    return f"{large_idx},{take}"
            else:
                # big >=2
                if x != 0:
                    # find xor-zero move with maximal remaining sum (minimal take)
                    best = None
                    best_sum = -1
                    for i in range(4):
                        if p[i] == 0:
                            continue
                        target = p[i] ^ x
                        if target < p[i] and target >= 0:
                            take = p[i] - target
                            if take >= 1:
                                s = total_sum - take
                                if s > best_sum:
                                    best_sum = s
                                    best = (i, take)
                    if best is not None:
                        return f"{best[0]},{best[1]}"
                # losing or no normal move: if big==2 go to big==1 max sum
                if big == 2:
                    best = None
                    best_sum = -1
                    for i in range(4):
                        if p[i] > 1:
                            for target in (0, 1):
                                if target < p[i]:
                                    take = p[i] - target
                                    q = apply(i, take)
                                    if _big_count(q) == 1:
                                        s = sum(q)
                                        if s > best_sum:
                                            best_sum = s
                                            best = (i, take)
                    if best is not None:
                        return f"{best[0]},{best[1]}"
                # otherwise take 1 from largest
                li = max(range(4), key=lambda i: p[i])
                return f"{li},1"

        # small/medium: exhaustive
        all_moves = []
        for i in range(4):
            for take in range(1, p[i] + 1):
                q = apply(i, take)
                all_moves.append((i, take, q))

        winning = []
        for i, take, q in all_moves:
            if _is_P(q):
                winning.append((i, take, q))

        if winning:
            # choose winning with maximal sum (minimal take) to prolong / confuse
            winning.sort(key=lambda t: sum(t[2]), reverse=True)
            i, take, _ = winning[0]
            return f"{i},{take}"

        # losing position: no move to P
        big = _big_count(p)
        if big == 2:
            # prefer to 1-large with max sum (traps normal-play bots)
            cand = []
            for i, take, q in all_moves:
                if _big_count(q) == 1:
                    # avoid suicide to terminal? terminal has big 0, so not here
                    cand.append((i, take, q))
            if cand:
                cand.sort(key=lambda t: sum(t[2]), reverse=True)
                i, take, _ = cand[0]
                return f"{i},{take}"

        # general losing heuristic: minimise opponent winning ratio
        # avoid immediate suicide (move to terminal) unless forced
        best_move = None
        best_ratio = 2.0
        best_total = -1
        non_suicide_exists = any(sum(q) != 0 for _, _, q in all_moves)
        for i, take, q in all_moves:
            s = sum(q)
            if s == 0:
                # taking last loses immediately
                if non_suicide_exists:
                    continue
                else:
                    # forced loss
                    return f"{i},{take}"
            # count opponent winning moves from q
            tot = s  # total moves = sum (since each stone count = options, ones have 1)
            # tot == sum because sum of options = sum piles
            win_cnt = 0
            # enumerate opponent moves from q
            for j in range(4):
                v = q[j]
                if v == 0:
                    continue
                # for each take2, test P
                # small optimization: early break not needed
                for take2 in range(1, v + 1):
                    r = q.copy()
                    r[j] -= take2
                    if _is_P(r):
                        win_cnt += 1
            ratio = win_cnt / tot if tot > 0 else 2.0
            if ratio < best_ratio - 1e-12 or (abs(ratio - best_ratio) < 1e-12 and tot > best_total):
                best_ratio = ratio
                best_total = tot
                best_move = (i, take)
        if best_move is not None:
            return f"{best_move[0]},{best_move[1]}"
        return fallback
    except Exception:
        try:
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        except Exception:
            pass
        return "0,1"
