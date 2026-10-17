
def policy(piles: list[int]) -> str:
    try:
        n = len(piles)
        # find any legal move as fallback
        first_non_empty = -1
        for i in range(n):
            if piles[i] > 0:
                first_non_empty = i
                break
        if first_non_empty == -1:
            # no legal move (game already over), must return something
            return "0,1"

        xor_sum = 0
        for x in piles:
            xor_sum ^= x
        mx = max(piles) if n > 0 else 0
        cnt_large = sum(1 for x in piles if x > 1)
        cnt_one = sum(1 for x in piles if x == 1)

        # Case 1: all piles 0/1
        if mx <= 1:
            # winning iff even number of ones (xor==0)
            # optimal is to take 1 from any 1-pile (flips parity)
            for i in range(n):
                if piles[i] > 0:
                    return f"{i},1"
            return f"{first_non_empty},1"

        # Case 2: some pile > 1
        if xor_sum != 0:
            # winning position
            if cnt_large >= 2:
                # normal Nim move to xor 0
                for i in range(n):
                    target = piles[i] ^ xor_sum
                    if target < piles[i]:
                        take = piles[i] - target
                        if take >= 1 and take <= piles[i]:
                            return f"{i},{take}"
                # fallback (should not happen): take 1 from largest
                idx = max(range(n), key=lambda i: piles[i])
                return f"{idx},1"
            elif cnt_large == 1:
                # exactly one large heap
                idx = -1
                for i in range(n):
                    if piles[i] > 1:
                        idx = i
                        break
                L = piles[idx]
                s = cnt_one  # number of 1-piles
                if s % 2 == 1:
                    # leave s ones (odd) -> take all
                    return f"{idx},{L}"
                else:
                    # leave s+1 ones (odd) -> leave 1
                    take = L - 1
                    if take < 1:
                        take = 1
                    if take > L:
                        take = L
                    return f"{idx},{take}"
            else:
                # should not happen (mx>1 implies cnt_large>=1)
                idx = max(range(n), key=lambda i: piles[i])
                return f"{idx},1"
        else:
            # losing P-position (xor==0, mx>1): stall
            # prefer to keep >=2 heaps >1 to force xor computation
            for i in range(n):
                if piles[i] > 0:
                    if piles[i] >= 1:
                        # try take 1
                        nl = piles[i] - 1
                        cnt = 0
                        for j in range(n):
                            v = piles[j] if j != i else nl
                            if v > 1:
                                cnt += 1
                        if cnt >= 2:
                            return f"{i},1"
            # otherwise take 1 from largest
            idx = max(range(n), key=lambda i: piles[i])
            # piles[idx] > 0 guaranteed because mx>1
            return f"{idx},1"
    except Exception:
        # absolute fallback: return first legal move
        try:
            for i, x in enumerate(piles):
                if x > 0:
                    return f"{i},1"
        except Exception:
            pass
        return "0,1"
