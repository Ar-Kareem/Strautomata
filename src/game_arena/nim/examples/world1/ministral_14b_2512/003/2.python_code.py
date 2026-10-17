
def policy(piles: list[int]) -> str:
    # Compute the nim-sum (XOR of all pile sizes)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # If nim-sum is non-zero, make a move that reduces it to zero
    if nim_sum != 0:
        for i in range(len(piles)):
            if (nim_sum ^ piles[i]) < piles[i]:
                # The target is (nim_sum ^ piles[i])
                take = piles[i] - (nim_sum ^ piles[i])
                return f"{i},{take}"

    # If nim-sum is zero, try to leave all piles equal (if possible)
    # Or force the opponent into a losing position
    # If all piles are 1, take all but one from one pile
    if all(pile == 1 for pile in piles):
        # Take all but one from the first pile
        return "0,1"

    # If not all piles are equal, try to make them equal
    # Find the largest pile and reduce it to match the others
    max_pile = max(piles)
    if piles.count(max_pile) == 1:
        # Reduce the max pile to match the next largest
        target = sorted(piles)[-2]
        take = max_pile - target
        return f"{piles.index(max_pile)},{take}"

    # If all piles are equal, take all but one from one pile
    # (This is a losing position, but we must make a move)
    return "0,1"
