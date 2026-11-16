
def policy(piles: list[int]) -> str:
    # Check if all piles are ones or zero
    if all(p == 0 or p == 1 for p in piles):
        # Count non-zero piles
        non_zero = [i for i, p in enumerate(piles) if p > 0]
        count = len(non_zero)
        if count == 0:
            # Game over, but should not happen
            return "0,1"
        # Take one from the first non-zero pile
        return f"{non_zero[0]},1"
    
    # Calculate nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    if nim_sum != 0:
        # Find moves that set nim-sum to zero
        moves = []
        bad_moves = []
        for i in range(4):
            if piles[i] == 0:
                continue
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                new_piles = piles.copy()
                new_piles[i] = target
                if all(p == 0 or p == 1 for p in new_piles):
                    new_count = sum(1 for p in new_piles if p > 0)
                    if new_count % 2 == 0:
                        bad_moves.append((i, take))
                    else:
                        moves.append((i, take))
                else:
                    moves.append((i, take))
        
        if moves:
            i, take = moves[0]
            return f"{i},{take}"
        else:
            # Try to leave all-ones with odd count by taking one from a pile > 1
            for i in range(4):
                if piles[i] > 1:
                    new_piles = piles.copy()
                    new_piles[i] = new_piles[i] - 1
                    if all(p == 0 or p == 1 for p in new_piles):
                        new_count = sum(1 for p in new_piles if p > 0)
                        if new_count % 2 == 1:
                            return f"{i},1"
            # If no good move, use a bad move
            if bad_moves:
                i, take = bad_moves[0]
                return f"{i},{take}"
            else:
                # Fallback: find any move that sets nim-sum to zero
                for i in range(4):
                    if piles[i] == 0:
                        continue
                    target = piles[i] ^ nim_sum
                    if target < piles[i]:
                        take = piles[i] - target
                        return f"{i},{take}"
                return "0,1"
    else:
        # nim-sum is zero, losing position
        # Try to leave all-ones with odd count
        for i in range(4):
            if piles[i] > 1:
                new_piles = piles.copy()
                new_piles[i] = new_piles[i] - 1
                if all(p == 0 or p == 1 for p in new_piles):
                    new_count = sum(1 for p in new_piles if p > 0)
                    if new_count % 2 == 1:
                        return f"{i},1"
        # Fallback: take one from first non-zero pile
        non_zero = [i for i, p in enumerate(piles) if p > 0]
        if non_zero:
            return f"{non_zero[0]},1"
        else:
            return "0,1"
