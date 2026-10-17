
def policy(piles: list[int]) -> str:
    # Check if all piles are 1
    all_ones = all(p == 1 for p in piles)
    if all_ones:
        count = sum(piles)  # This equals the number of piles since all are 1s
        if count % 2 == 0:
            # If even count, take one to leave odd count which is a losing position for the opponent
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # If odd count, we have to take a pile, but we can't win. Just return any valid move.
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
    
    # Compute the nim-sum for the current state
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    if nim_sum != 0:
        # Find a move that makes the nim-sum zero
        for i in range(4):
            if piles[i] == 0:
                continue
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"
        # If no such target found (shouldn't happen), take one from the first non-zero pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    else:
        # Nim-sum is zero; take one from the first non-zero pile as a losing move
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
