
def policy(piles: list[int]) -> str:
    # Count non-zero piles
    nonzero_count = sum(1 for p in piles if p > 0)
    
    # Check if all non-zero piles are size 1
    all_ones = all(p == 1 for p in piles if p > 0)
    
    if nonzero_count == 0:
        # Game over, but return a valid move anyway
        return "0,0"
    elif all_ones:
        # All piles are size 1
        if nonzero_count % 2 == 0:
            # Current player wins: reduce the number of non-zero piles by 1
            for i in range(len(piles)):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Current player loses: make any move
            for i in range(len(piles)):
                if piles[i] > 0:
                    return f"{i},1"
    else:
        # Not all piles are size 1
        # Check if there is exactly one pile with size >1
        large_piles = [i for i in range(len(piles)) if piles[i] > 1]
        if len(large_piles) == 1:
            i = large_piles[0]
            if nonzero_count % 2 == 0:
                # Reduce the large pile to 0
                take_amount = piles[i]
                return f"{i},{take_amount}"
            else:
                # Reduce the large pile to 1
                take_amount = piles[i] - 1
                return f"{i},{take_amount}"
        else:
            # Use normal Nim strategy
            S = 0
            for p in piles:
                S ^= p
            if S == 0:
                # Current player loses: make a move that reduces the largest pile
                max_pile = max(piles)
                for i in range(len(piles)):
                    if piles[i] == max_pile and piles[i] > 0:
                        return f"{i},1"
            else:
                # Find a move to set nim-sum to 0
                for i in range(len(piles)):
                    if piles[i] > 0:
                        pj = piles[i] ^ S
                        if pj < piles[i]:
                            take_amount = piles[i] - pj
                            return f"{i},{take_amount}"
                # Fallback: if no move found, reduce the largest pile
                max_pile = max(piles)
                for i in range(len(piles)):
                    if piles[i] == max_pile and piles[i] > 0:
                        return f"{i},1"
