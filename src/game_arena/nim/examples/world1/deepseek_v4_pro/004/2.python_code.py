
def policy(piles: list[int]) -> str:
    # Misère Nim strategy for 4 piles
    # Compute nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Check if all non-empty piles have size 1 (endgame)
    non_empty = [p for p in piles if p > 0]
    all_ones = all(p == 1 for p in non_empty)
    
    if all_ones:
        # In misère Nim with all piles size 1, we want to leave an odd number of piles
        # So if number of non-empty piles is even, take one whole pile (leaving odd)
        # If odd, we are losing anyway but must make a move; take from any pile (but leave 0 to minimize opponent's options)
        num_non_empty = len(non_empty)
        if num_non_empty % 2 == 0:
            # Leave odd number of 1's -> take a whole pile
            for i, p in enumerate(piles):
                if p == 1:
                    return f"{i},1"
        else:
            # Odd number of 1's, we are in losing position; just take one from any pile with 1
            for i, p in enumerate(piles):
                if p >= 1:
                    return f"{i},1"
    else:
        # Normal misère play: try to make nim-sum zero
        if nim_sum == 0:
            # Already zero nim-sum, any move will make it non-zero
            # Pick largest pile and take one to minimize opponent's advantage
            max_pile = max(range(4), key=lambda i: piles[i])
            return f"{max_pile},1"
        else:
            # Find a pile to reduce to nim_sum XOR pile
            for i, p in enumerate(piles):
                target = p ^ nim_sum
                if target < p:
                    take = p - target
                    # After move, check if we would create the all-ones losing trap
                    new_piles = piles.copy()
                    new_piles[i] = target
                    new_non_empty = [x for x in new_piles if x > 0]
                    if all(x == 1 for x in new_non_empty):
                        # If new state has all ones, ensure we leave odd number
                        if len(new_non_empty) % 2 == 0:
                            # Would leave even number of 1's (bad), so adjust move
                            # Instead, make a move that leaves odd number of 1's
                            # Take one less to leave pile size 2? No, that breaks all-ones.
                            # Alternative: take one more if possible (leave 1 less than target)
                            # Actually, if all piles would be 1 and even count, we should leave an odd count.
                            # This means we should not reduce to exactly target if it creates even 1's.
                            # Try to take one more (if legal) to leave pile as 1, changing count by 1.
                            if take + 1 <= p:
                                # Taking one more reduces the pile to target-1
                                # Since target would be 1, target-1=0, which removes the pile, making odd number of 1's
                                return f"{i},{take + 1}"
                            # If we can't adjust, try another pile
                            continue
                    return f"{i},{take}"
            # If no standard winning move found (shouldn't happen), play safe move
            for i, p in enumerate(piles):
                if p > 0:
                    return f"{i},1"
