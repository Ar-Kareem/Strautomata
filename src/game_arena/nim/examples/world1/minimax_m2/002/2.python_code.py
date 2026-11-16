
def policy(piles):
    # Find indices of non-zero piles
    non_zero_indices = [i for i in range(4) if piles[i] > 0]
    if not non_zero_indices:
        # Should not happen as game is over, but return a default move
        return "0,1"
    non_zero_piles = [piles[i] for i in non_zero_indices]
    
    # Check if all non-zero piles are size 1
    if all(p == 1 for p in non_zero_piles):
        k = len(non_zero_piles)
        i = non_zero_indices[0]
        return f"{i},1"
    else:
        # Count number of piles with size > 1
        A = sum(1 for p in piles if p > 1)
        if A == 1:
            # Find the index of the pile with size > 1
            i = next(i for i in range(4) if piles[i] > 1)
            k = len(non_zero_piles)
            if k % 2 == 0:
                take = piles[i]
                return f"{i},{take}"
            else:
                take = piles[i] - 1
                return f"{i},{take}"
        else:
            S = 0
            for p in piles:
                S ^= p
            for i in range(4):
                p = piles[i]
                if p > 0:
                    x = p - (S ^ p)
                    if x >= 1 and x <= p:
                        return f"{i},{x}"
            i = non_zero_indices[0]
            return f"{i},1"
