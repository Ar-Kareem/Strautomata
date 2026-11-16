
import functools

def policy(piles: list[int]) -> str:
    # Misère Nim optimal policy for 4 piles
    n = 4
    
    def is_all_one(piles_state):
        return all(p == 1 for p in piles_state if p > 0)
    
    def count_nonempty(piles_state):
        return sum(1 for p in piles_state if p > 0)
    
    # Compute nim-sum
    nim_sum = functools.reduce(lambda x, y: x ^ y, piles)
    
    # Check if all piles size 0 or 1
    if all(p <= 1 for p in piles):
        # Misère endgame: all piles are 0 or 1
        ones = [i for i, p in enumerate(piles) if p == 1]
        if len(ones) % 2 == 1:
            # Odd number of ones: take a whole pile (any one)
            pile = ones[0]
            take = 1
        else:
            # Even number of ones: take from a pile to leave odd ones
            # Find a pile with p == 1
            if len(ones) > 0:
                pile = ones[0]
                take = 1
            else:
                # All zeros, shouldn't happen since game ends before this
                # But fallback: take from first non-empty
                for i in range(n):
                    if piles[i] > 0:
                        pile = i
                        take = 1
                        break
        return f"{pile},{take}"
    
    # Not all <=1
    if nim_sum != 0:
        # Winning move: make nim-sum zero
        for i in range(n):
            if piles[i] == 0:
                continue
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                # Check if this move results in all piles <=1
                new_piles = piles[:]
                new_piles[i] -= take
                if all(p <= 1 for p in new_piles):
                    # Adjust for misère: if after move all piles <=1,
                    # ensure we leave odd number of piles of size 1
                    ones_after = sum(1 for p in new_piles if p == 1)
                    if ones_after % 2 == 0:
                        # This move leaves even ones: not winning in misère
                        # Try alternative: take fewer from same pile to leave odd ones
                        if piles[i] > 1:
                            take = piles[i] - 1
                        else:
                            # Just take 1
                            take = 1
                return f"{i},{take}"
        # fallback (should not happen)
        for i in range(n):
            if piles[i] > 0:
                return f"{i},1"
    
    # Losing position (nim_sum == 0)
    # Take 1 from largest pile to prolong
    max_val = max(piles)
    for i in range(n):
        if piles[i] == max_val:
            return f"{i},1"
    # fallback
    for i in range(n):
        if piles[i] > 0:
            return f"{i},1"
    return "0,1"  # should never reach here
