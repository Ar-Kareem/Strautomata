
def policy(piles: list[int]) -> str:
    try:
        n = len(piles)
        # collect non-empty
        non_empty = [i for i in range(n) if piles[i] > 0]
        if not non_empty:
            # terminal, no legal move - return dummy to avoid crash
            return "0,1"
        # helper to make legal fallback
        def fallback():
            for i in range(n):
                if piles[i] > 0:
                    return f"{i},1"
            return "0,1"

        max_p = max(piles) if n > 0 else 0
        # all piles 0/1
        if max_p <= 1:
            # winning iff count even, but any move must remove one pile
            for i in non_empty:
                return f"{i},1"
            return fallback()

        big_idx = [i for i in range(n) if piles[i] > 1]
        big = len(big_idx)

        if big == 1:
            b = big_idx[0]
            H = piles[b]
            k = sum(1 for p in piles if p == 1)
            if k % 2 == 0:
                # leave k+1 ones (odd) -> reduce to 1
                take = H - 1
                if take < 1:
                    take = H
                if take > H:
                    take = H
                return f"{b},{take}"
            else:
                # leave k ones (odd) -> remove pile
                take = H
                return f"{b},{take}"
        else:
            # big >= 2
            x = 0
            for p in piles:
                x ^= p
            if x != 0:
                # winning: normal Nim move to xor 0
                for i in range(n):
                    p = piles[i]
                    if p > 0:
                        target = p ^ x
                        if target < p:
                            take = p - target
                            if 1 <= take <= p:
                                return f"{i},{take}"
                # fallback, should not happen
                i_max = max(non_empty, key=lambda i: piles[i])
                return f"{i_max},1"
            else:
                # losing P-position: try to trap imperfect opponent
                if big == 2:
                    # move to single-big position to confuse normal-Nim players
                    # keep larger pile, reduce smaller to 1
                    sorted_big = sorted(big_idx, key=lambda i: piles[i])
                    i_small = sorted_big[0]
                    take = piles[i_small] - 1
                    if take >= 1 and take <= piles[i_small]:
                        return f"{i_small},{take}"
                    else:
                        # reduce to 0
                        return f"{i_small},{piles[i_small]}"
                else:
                    # big >=3 : prolong game, take 1 from largest
                    i_max = max(non_empty, key=lambda i: piles[i])
                    # ensure legal
                    return f"{i_max},1"
    except Exception:
        # absolute guarantee of a string; try to find legal
        try:
            for i in range(len(piles)):
                if piles[i] > 0:
                    return f"{i},1"
        except Exception:
            pass
        return "0,1"
