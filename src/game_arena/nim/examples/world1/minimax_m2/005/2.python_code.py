
def policy(piles: list[int]) -> str:
    # Calculate the number of non-zero piles
    non_zero = [p for p in piles if p > 0]
    k = len(non_zero)
    
    # If there are no non-zero piles, no move possible. This should not occur in valid game states.
    if k == 0:
        return "0,0"  # Default, though invalid; game state should be valid.
    
    # Check if all non-zero piles are of size one
    if all(p == 1 for p in non_zero):
        if k % 2 == 0:
            # Even number of non-zero piles: win by taking one from any pile
            for i in range(len(piles)):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Odd number: lose, but return a legal move
            for i in range(len(piles)):
                if piles[i] > 0:
                    return f"{i},1"
    else:
        # There is at least one pile with size > 1
        # Count piles with size > 1
        large_count = sum(1 for p in piles if p > 1)
        if large_count >= 2:
            # Multiple large piles: use nim-sum reduction
            nim_sum = 0
            for p in piles:
                nim_sum ^= p
            if nim_sum == 0:
                return "0,1"  # Losing position, any move
            else:
                for i in range(len(piles)):
                    new_size = piles[i] ^ nim_sum
                    if new_size < piles[i]:
                        take = piles[i] - new_size
                        return f"{i},{take}"
                # Fallback if no reduction found
                return "0,1"
        else:
            # Exactly one pile with size > 1
            # Find the index of that pile
            i = -1
            for idx in range(len(piles)):
                if piles[idx] > 1:
                    i = idx
                    break
            if i == -1:
                return "0,1"  # Fallback
            # Recalculate k as the number of non-zero piles
            k = sum(1 for p in piles if p > 0)
            if k % 2 == 0:
                # k even: reduce to zero
                take = piles[i]
                return f"{i},{take}"
            else:
                # k odd: reduce to one
                take = piles[i] - 1
                return f"{i},{take}"
