
def policy(piles: list[int]) -> str:
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]

    # Case 1: All piles are equal (losing position in standard Nim, but need to avoid in Misère)
    if len(set(piles)) == 1:
        # Take all but one from the largest pile
        max_pile = max(piles)
        if max_pile == 1:
            # If all piles are 1, take from any pile (losing move, but no choice)
            return "0,1"
        else:
            # Find the first pile with max_pile objects and take (max_pile - 1)
            for pile in range(len(piles)):
                if piles[pile] == max_pile:
                    take = max_pile - 1
                    return f"{pile},{take}"

    # Case 2: Nim-sum is zero and not all piles are equal
    if nim_sum == 0:
        # Take 1 from the largest pile to avoid leaving all equal
        max_pile = max(piles)
        for pile in range(len(piles)):
            if piles[pile] == max_pile:
                return f"{pile},1"

    # Case 3: Nim-sum is non-zero or move would leave all piles equal
    # Find a pile where (piles[pile] ^ nim_sum) < piles[pile]
    for pile in range(len(piles)):
        if piles[pile] ^ nim_sum < piles[pile]:
            take = piles[pile] ^ nim_sum
            # Edge case: If taking 'take' would leave a single pile with 1 object and others empty
            if take == 0 and sum(piles) == 1:
                # Take all objects from that pile (since opponent would lose otherwise)
                take = piles[pile]
            return f"{pile},{take}"

    # Fallback: If no move found (shouldn't happen for valid Nim states)
    # Take from the first pile with objects
    for pile in range(len(piles)):
        if piles[pile] > 0:
            return f"{pile},1"
    return "0,1"  # Shouldn't reach here if piles are valid
