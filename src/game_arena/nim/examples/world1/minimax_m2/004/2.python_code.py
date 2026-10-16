
def policy(piles: list[int]) -> str:
    # Count the number of piles with size greater than 1
    k = sum(1 for p in piles if p > 1)
    
    if k == 0:
        # All piles have size <=1. Find a pile with size 1 and take one object.
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        # If no size-1 pile found, it should not happen if all piles are non-zero, but return default move if needed.
        # This case should not occur as per problem constraints.
        return "0,1"  # Default move, but should not be used.
    
    elif k == 1:
        # Find the unique pile with size >1
        for i, p in enumerate(piles):
            if p > 1:
                L = p
                # Count the number of size-1 piles
                m = sum(1 for p2 in piles if p2 == 1)
                if m % 2 == 1:  # m is odd
                    take = L
                    return f"{i},{take}"
                else:  # m is even
                    take = L - 1
                    return f"{i},{take}"
    
    else:  # k >= 2
        # Compute the Nim-sum (XOR of all piles)
        S = 0
        for p in piles:
            S ^= p
        
        if S != 0:
            # Find a pile to reduce to set Nim-sum to zero
            for i, p in enumerate(piles):
                if p ^ S < p:
                    take = p - (p ^ S)
                    return f"{i},{take}"
        else:
            # Nim-sum is zero, make any legal move by taking one object from a non-empty pile
            for i, p in enumerate(piles):
                if p >= 1:
                    return f"{i},1"
    
    # Fallback return, should not be reached
    return "0,1"
