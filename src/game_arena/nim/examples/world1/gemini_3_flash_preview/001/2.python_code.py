
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Standard Nim strategy: try to make nim_sum 0
    # In Misere play, this is the same as long as there's more than one pile > 1
    move = None

    if nim_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ nim_sum
            if target < p:
                # Potential move found: reduce pile i to 'target'
                # Check if this move leads to the special Misere endgame
                remaining_piles_after_move = [piles[j] if i != j else target for j in range(4)]
                piles_greater_than_one = [x for x in remaining_piles_after_move if x > 1]
                
                if not piles_greater_than_one:
                    # Special Endgame: All piles will be 0 or 1.
                    # We must leave an ODD number of piles of size 1.
                    count_ones = sum(1 for x in remaining_piles_after_move if x == 1)
                    if count_ones % 2 == 0:
                        # Even number of 1s? Change this pile to 1 to make it odd
                        # This is only legal if the current pile was the one we were changing
                        move = f"{i},{p - 1}"
                    else:
                        # Odd number of 1s? Change this pile to 0
                        move = f"{i},{p}"
                else:
                    # Standard play: make nim_sum zero
                    move = f"{i},{p - target}"
                break

    # If no winning move (nim_sum was 0) or logic failed, take 1 from the first non-empty pile
    if not move:
        for i, p in enumerate(piles):
            if p > 0:
                move = f"{i},1"
                break
    
    return move
