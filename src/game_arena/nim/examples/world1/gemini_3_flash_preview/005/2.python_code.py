
def policy(piles: list[int]) -> str:
    # Calculate current Nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # If nim_sum is 0, we are in a losing position in standard Nim.
    # Take 1 from the first available pile and hope for the best.
    if nim_sum == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Standard Nim winning move: find a pile where pile ^ nim_sum < pile
    for i, p in enumerate(piles):
        target = p ^ nim_sum
        if target < p:
            # We found a candidate move. Now check the Misere condition.
            # A Misere play differs only when the move would leave only piles of size 1.
            
            # Simulate the move
            new_piles = list(piles)
            new_piles[i] = target
            
            # Count piles > 1 in the predicted state
            piles_greater_than_one = [x for x in new_piles if x > 1]
            
            if not piles_greater_than_one:
                # If all remaining piles are size 1 (or 0), 
                # we must leave an ODD number of piles of size 1.
                num_ones = sum(1 for x in new_piles if x == 1)
                if num_ones % 2 == 0:
                    # Current move leaves even number of 1s. 
                    # Change current pile to 1 instead of 0 (or 0 instead of 1)
                    # to ensure an odd number of 1s remain.
                    final_val = 1 if num_ones % 2 == 0 and target == 0 else 0
                    # Check if this alternate move is legal
                    if p - final_val >= 1:
                        return f"{i},{p - final_val}"
            
            # If no special Misere adjustment needed, perform the standard XOR move
            return f"{i},{p - target}"

    # Fallback to a legal move if logic fails
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
