
def policy(piles: list[int]) -> str:
    try:
        n = len(piles)
        # ensure length 4 handling
        if n == 0:
            return "0,1"
        # find any legal fallback
        def fallback():
            for i, v in enumerate(piles):
                if v > 0:
                    return f"{i},1"
            return "0,1"

        # count
        big_idx = [i for i, v in enumerate(piles) if v > 1]
        big = len(big_idx)
        ones = sum(1 for v in piles if v == 1)

        # Case: all piles <=1
        if big == 0:
            for i, v in enumerate(piles):
                if v > 0:
                    return f"{i},1"
            return fallback()

        # Case: exactly one big pile -> always winning, leave odd ones
        if big == 1:
            b = big_idx[0]
            H = piles[b]
            k = ones  # number of 1-piles
            if k % 2 == 1:
                # take all
                return f"{b},{H}"
            else:
                # leave 1: take H-1
                take = H - 1
                if take < 1:
                    take = 1
                if take > H:
                    take = H
                return f"{b},{take}"

        # Case: >=2 big piles
        x = 0
        for v in piles:
            x ^= v

        if x != 0:
            # winning: normal xor move, keep max remaining (min take)
            best = None
            best_rem = -1
            for i, v in enumerate(piles):
                if v == 0:
                    continue
                target = v ^ x
                if target < v:
                    take = v - target
                    if take < 1 or take > v:
                        continue
                    rem = sum(piles) - take
                    if rem > best_rem:
                        best_rem = rem
                        best = (i, take)
            if best is not None:
                return f"{best[0]},{best[1]}"
            # should not happen, fallback
            return fallback()
        else:
            # losing: try to trap normal-Nim player
            # look for move leaving exactly one big with even ones
            best_trap = None
            best_trap_rem = -1
            for i, v in enumerate(piles):
                if v == 0:
                    continue
                for take in range(1, v + 1):
                    nv = v - take
                    # build new position
                    # count big and ones quickly
                    nb_big = 0
                    nb_ones = 0
                    for j, w in enumerate(piles):
                        cw = nv if j == i else w
                        if cw > 1:
                            nb_big += 1
                        elif cw == 1:
                            nb_ones += 1
                    if nb_big == 1 and (nb_ones % 2 == 0):
                        rem = sum(piles) - take
                        if rem > best_trap_rem:
                            best_trap_rem = rem
                            best_trap = (i, take)
            if best_trap is not None:
                return f"{best_trap[0]},{best_trap[1]}"
            # no trap: prolong - take 1 from largest pile
            # find largest
            mx = -1
            mi = -1
            for i, v in enumerate(piles):
                if v > mx:
                    mx = v
                    mi = i
            if mx > 0:
                return f"{mi},1"
            return fallback()
    except Exception:
        try:
            for i, v in enumerate(piles):
                if v > 0:
                    return f"{i},1"
        except Exception:
            pass
        return "0,1"
