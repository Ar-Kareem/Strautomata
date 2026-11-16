
def policy(piles):
    # Check if all piles are 1
    if all(p == 1 for p in piles):
        # If all piles are 1, the outcome depends on the number of piles
        # Return a move taking one from the first pile
        return "0,1"
    else:
        nim = 0
        for p in piles:
            nim ^= p
        if nim != 0:
            # Find a pile where reducing it to (pile ^ nim) is possible
            for i, p in enumerate(piles):
                target = p ^ nim
                if target < p:
                    take = p - target
                    return f"{i},{take}"
        else:
            # Nim-sum is zero; any move will leave a winning position for the opponent
            # Take one from the first pile (legal move)
            return "0,1"
