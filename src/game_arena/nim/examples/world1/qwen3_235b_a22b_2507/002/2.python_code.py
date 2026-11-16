
def policy(piles: list[int]) -> str:
    # Count the number of piles with more than 1 stone
    big_piles = [i for i in range(4) if piles[i] > 1]
    big_count = len(big_piles)
    
    if big_count == 0:
        # All piles are 0 or 1; take one from the first non-empty pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    elif big_count == 1:
        # Exactly one pile has more than 1 stone
        i = big_piles[0]
        # Count the number of piles with exactly one stone
        ones_count = sum(1 for p in piles if p == 1)
        # We aim to leave an odd number of 1s for the opponent after this move
        # Option 1: reduce the big pile to 1 -> new ones = ones_count + 1
        # Option 2: reduce the big pile to 0 -> new ones = ones_count
        if (ones_count + 1) % 2 == 1:
            # Choose option 1: leave the big pile as 1
            take = piles[i] - 1
            return f"{i},{take}"
        else:
            # Then ones_count % 2 must be 1, so choose option 2: remove the big pile entirely
            take = piles[i]  # take all stones from the pile
            return f"{i},{take}"
    
    else:
        # Two or more piles have more than 1 stone: play normal Nim strategy
        nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
        
        if nim_sum == 0:
            # Current position is losing; make a move that preserves complexity
            # Take one from the largest pile
            max_pile = max(piles)
            for i in range(4):
                if piles[i] == max_pile:
                    return f"{i},1"
        else:
            # Find a move that makes the nim-sum zero
            for i in range(4):
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    return f"{i},{take}"
            # Fallback: should not be reached in normal play
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
