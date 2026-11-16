
def policy(piles: list[int]) -> str:
    try:
        n = len(piles)
        # find any legal fallback
        fb_pile = -1
        for i in range(n):
            try:
                if piles[i] >= 1:
                    fb_pile = i
                    break
            except Exception:
                continue
        if fb_pile == -1:
            # no legal move, must still return something
            return "0,1"

        def legal(i, take):
            try:
                return 0 <= i < n and take >= 1 and take <= piles[i]
            except Exception:
                return False

        # count big piles >1 and ones ==1
        k = 0
        ones_idx = []
        big_idx = []
        for i in range(n):
            v = piles[i]
            if v > 1:
                k += 1
                big_idx.append(i)
            elif v == 1:
                ones_idx.append(i)

        # Case k == 0 : all 0/1
        if k == 0:
            # must take a 1-pile; winning iff even number of ones
            for i in ones_idx:
                return f"{i},1"
            return f"{fb_pile},1"

        # Case k == 1 : exactly one pile >1
        if k == 1:
            b = big_idx[0]
            s = len(ones_idx)
            B = piles[b]
            if s % 2 == 0:
                # leave 1
                take = B - 1
                if take < 1:
                    take = B
                if legal(b, take):
                    return f"{b},{take}"
            else:
                # remove whole pile to leave s ones (odd)
                take = B
                if legal(b, take):
                    return f"{b},{take}"
            # fallback (should not happen)
            return f"{fb_pile},1"

        # Case k >= 2 : normal play
        x = 0
        for v in piles:
            x ^= int(v)
        if x != 0:
            for i in range(n):
                v = piles[i]
                if v == 0:
                    continue
                target = v ^ x
                if target < v:
                    take = v - target
                    if legal(i, take):
                        return f"{i},{take}"
            # should have found one, fallback
            return f"{fb_pile},1"
        else:
            # Losing P-position: try to trap imperfect opponent
            # If k==2 we can move to k'==1 in one move
            if k == 2:
                # try to leave k'==1 with tricky parity
                # heuristic: reduce a big pile to 0 or 1
                # prefer move that makes normal (xor-0) differ from misere
                best = None
                for b in big_idx:
                    for t in (1, 0):
                        if t >= piles[b]:
                            continue
                        if t < 0:
                            continue
                        take = piles[b] - t
                        if not legal(b, take):
                            continue
                        # resulting position
                        # count ones after (approx)
                        # choose first viable; prefer t==1 then t==0
                        best = (b, take)
                        break
                    if best is not None:
                        break
                if best is not None:
                    return f"{best[0]},{best[1]}"
            # For k>2 or otherwise: minimal damage, take 1 from largest
            # to prolong game and maximize mistake chance
            mx = -1
            mi = fb_pile
            for i in range(n):
                if piles[i] > mx:
                    mx = piles[i]
                    mi = i
            if legal(mi, 1):
                return f"{mi},1"
            return f"{fb_pile},1"
    except Exception:
        # ultimate safety: try to find any legal move
        try:
            for i in range(len(piles)):
                if piles[i] >= 1:
                    return f"{i},1"
        except Exception:
            pass
        return "0,1"
