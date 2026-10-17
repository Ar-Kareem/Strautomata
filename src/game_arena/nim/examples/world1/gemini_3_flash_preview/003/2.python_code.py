
def policy(piles: list[int]) -> str:
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Count how many piles have more than 1 object
    piles_gt_1 = sum(1 for p in piles if p > 1)

    # Winning strategy for Misere Nim
    if nim_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ nim_sum
            if target < p:
                # Potential move: change piles[i] to target
                new_piles = [piles[j] if i != j else target for j in range(len(piles))]
                new_piles_gt_1 = sum(1 for x in new_piles if x > 1)
                
                # Special case for Misere Play:
                # If the standard Nim move leaves only piles of size 1
                if new_piles_gt_1 == 0:
                    # We want to leave an odd number of piles of size 1
                    ones_count_others = sum(1 for j, x in enumerate(piles) if i != j and x == 1)
                    # If current count of other ones is even, make this pile 1
                    # If current count of other ones is odd, make this pile 0
                    final_val = 1 if (ones_count_others % 2 == 0) else 0
                    return f"{i},{p - final_val}"
                else:
                    # Standard Nim move
                    return f"{i},{p - target}"

    # If already in a losing position (nim_sum == 0) or no winning move found,
    # just take 1 from the largest available pile to stay in the game.
    max_val = max(piles)
    max_idx = piles.index(max_val)
    return f"{max_idx},1"
