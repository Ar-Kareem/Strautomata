
def policy(piles: list[int]) -> str:
    """
    Compute optimal move for Misère Nim (4 piles).
    The player who takes the last object loses.
    
    Based on Bouton's theorem for misère Nim:
    - If all piles ≤ 1: P-position iff odd number of 1s
    - Otherwise: P-position iff nim-sum = 0
    """
    n = len(piles)
    
    # Identify big piles (> 1) and count ones
    big_piles = [i for i in range(n) if piles[i] > 1]
    ones_count = sum(1 for p in piles if p == 1)
    
    # Case 1: All piles are 0 or 1
    if len(big_piles) == 0:
        # Take from any pile with size 1
        for i in range(n):
            if piles[i] == 1:
                return f"{i},1"
        # Game already over - return default
        return "0,1"
    
    # Case 2: Exactly one pile > 1
    if len(big_piles) == 1:
        big_idx = big_piles[0]
        k = piles[big_idx]
        if ones_count % 2 == 0:
            # Even 1s: leave 1 in big pile (total 1s becomes odd)
            return f"{big_idx},{k-1}"
        else:
            # Odd 1s: take all from big pile (leaves odd 1s)
            return f"{big_idx},{k}"
    
    # Case 3: Two or more piles > 1 - use Nim XOR strategy
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    if nim_sum == 0:
        # P-position: any legal move (we're losing with perfect opponent)
        for i in range(n):
            if piles[i] > 0:
                return f"{i},1"
        return "0,1"
    
    # N-position: find move that makes nim_sum = 0
    for i in range(n):
        if piles[i] > 0:
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
    
    # Fallback (should not reach here if nim_sum != 0)
    for i in range(n):
        if piles[i] > 0:
            return f"{i},1"
    return "0,1"
