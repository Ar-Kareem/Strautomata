
def policy(piles: list[int]) -> str:
    # Check if every non-empty pile has size 1
    non_empty = [p for p in piles if p > 0]
    if all(x == 1 for x in non_empty):
        count = len(non_empty)
        for i, pile in enumerate(piles):
            if pile > 0:
                return f"{i},1"  # Take one entire pile (removing it)
    
    # There is at least one pile with size > 1
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    non_zero_count = sum(1 for p in piles if p > 0)
    if non_zero_count == 1:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},{p-1}"  # Take all but one object

    if nim_sum != 0:
        # Find a move to make nim-sum zero and not leave an all-ones state
        for i, pile in enumerate(piles):
            target = pile ^ nim_sum
            if target < pile:
                new_state = piles.copy()
                new_state[i] = target
                non_empty_new = [p for p in new_state if p > 0]
                if non_empty_new and not all(x == 1 for x in non_empty_new):
                    return f"{i},{pile - target}"
        
        # If no safe move found, take one from the first non-zero pile
        for i, pile in enumerate(piles):
            if pile > 0:
                return f"{i},1"
    else:
        # Nim-sum is zero: losing position, take one from the first non-zero pile
        for i, pile in enumerate(piles):
            if pile > 0:
                return f"{i},1"
