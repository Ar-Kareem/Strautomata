
def policy(piles):
    # Calculate XOR (nim-sum) of all pile sizes
    xor_sum = 0
    for pile in piles:
        xor_sum ^= pile
    
    # Count piles with more than one object
    multi_object_piles = sum(1 for pile in piles if pile > 1)
    
    # Try to make a winning move (non-zero XOR to zero XOR)
    if xor_sum != 0 or multi_object_piles == 0:
        # Look for a pile to reduce to make XOR zero
        for i in range(4):
            if piles[i] > 0:
                # Calculate what this pile should become to make XOR zero
                target_size = piles[i] ^ xor_sum
                if target_size < piles[i]:
                    # Found a winning move
                    return f"{i},{piles[i] - target_size}"
        
        # If we can't find a XOR-reducing move, just take one from the largest pile
        max_pile_index = piles.index(max(piles))
        return f"{max_pile_index},1"
    else:
        # We're in a losing position (XOR=0 and multiple multi-object piles)
        # Take one object from the largest pile to minimize opponent's advantage
        max_pile_index = piles.index(max(piles))
        return f"{max_pile_index},1"
