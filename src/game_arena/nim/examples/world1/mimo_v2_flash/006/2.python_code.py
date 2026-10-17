
def policy(piles: list[int]) -> str:
    def is_losing(p):
        # Check if position p is losing under misère Nim rules.
        non_zero = [x for x in p if x > 0]
        if not non_zero:
            return False  # Terminal position, but not called in practice.
        # If all non-zero piles are 1, losing if odd count.
        if all(x == 1 for x in non_zero):
            return len(non_zero) % 2 == 1
        # Otherwise, losing if nim-sum is zero.
        nim = 0
        for x in p:
            nim ^= x
        return nim == 0

    # If all piles are 1, take 1 from the first pile.
    if all(p == 1 for p in piles):
        return "0,1"

    # Compute nim-sum (XOR of all piles).
    nim = 0
    for p in piles:
        nim ^= p

    # If nim-sum is non-zero, we are in a winning position.
    if nim != 0:
        candidates = set()
        for i in range(4):
            if piles[i] == 0:
                continue
            # Add common candidate moves.
            candidates.add((i, 1))           # Take 1 stone.
            candidates.add((i, piles[i]))    # Take all stones.
            if piles[i] > 1:
                candidates.add((i, piles[i] - 1))  # Take all but one (leave 1).
            # Add the move that makes nim-sum zero.
            target = piles[i] ^ nim
            if target < piles[i]:
                take = piles[i] - target
                candidates.add((i, take))

        # Check each candidate move to see if it leaves a losing position.
        for (i, take) in candidates:
            if take < 1 or take > piles[i]:
                continue
            new_piles = piles.copy()
            new_piles[i] -= take
            if is_losing(new_piles):
                return f"{i},{take}"

        # Fallback: take 1 from the first non-zero pile (should not occur in winning position).
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"

    else:
        # Nim-sum is zero (losing position). Take 1 from the first non-zero pile.
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
