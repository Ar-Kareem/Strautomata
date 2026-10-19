
def policy(piles: list[int]) -> str:
    # 1. Check for the "All 1s" scenario to distinguish from general Nim
    is_all_ones = True
    for p in piles:
        if p != 0 and p != 1:
            is_all_ones = False
            break

    if is_all_ones:
        # 2. Misère Nim Endgame Strategy
        # Count piles with exactly 1 object
        count_ones = sum(1 for p in piles if p == 1)
        
        # If count_ones is odd, it's a winning position (we leave even count for opponent).
        # If count_ones is even, it's a losing position (we leave odd count for opponent).
        # In both cases, the correct move is to remove 1 from a pile of size 1.
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"

    # 3. General Nim Strategy (Standard Nim for non-ending positions)
    # Calculate Nim-sum
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]

    if nim_sum == 0:
        # We are in a losing position.
        # Make a legal move that minimizes impact. Remove 1 from the first non-empty pile.
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    else:
        # We are in a winning position.
        # Find a move that makes the nim_sum 0.
        for i in range(4):
            # We can modify pile i if the target size is valid (smaller than current)
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"

    # Should not be reached given valid game states
    return "0,1"
