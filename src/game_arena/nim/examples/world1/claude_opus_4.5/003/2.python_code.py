
def policy(piles: list[int]) -> str:
    # Count piles with more than 1 object and piles with exactly 1 object
    def analyze(p):
        big = sum(1 for x in p if x > 1)
        ones = sum(1 for x in p if x == 1)
        return big, ones
    
    # Calculate nim-sum (XOR of all piles)
    def nim_sum(p):
        result = 0
        for x in p:
            result ^= x
        return result
    
    # Check if a move is legal
    def is_legal(pile_idx, take, p):
        return 0 <= pile_idx < 4 and 1 <= take <= p[pile_idx]
    
    # Apply a move and return new state
    def apply_move(p, pile_idx, take):
        new_p = p[:]
        new_p[pile_idx] -= take
        return new_p
    
    big_piles, one_piles = analyze(piles)
    xor = nim_sum(piles)
    
    # Endgame: all piles have at most 1 object
    if big_piles == 0:
        # We want to leave an odd number of 1s for opponent
        # If currently odd number of 1s, take one (leave even, opponent takes last)
        # If currently even number of 1s, we're in losing position, just take any
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
    
    # If only one pile has more than 1 object, handle specially
    if big_piles == 1:
        # Find the big pile
        for i in range(4):
            if piles[i] > 1:
                big_idx = i
                big_val = piles[i]
                break
        
        # After our move on the big pile, we want odd number of total piles with 1 object
        # Current ones count is one_piles
        # If we leave 0 in big pile: total ones = one_piles (want odd)
        # If we leave 1 in big pile: total ones = one_piles + 1 (want odd)
        
        if one_piles % 2 == 0:
            # Leave 1 in big pile, making total ones = one_piles + 1 (odd)
            take = big_val - 1
            if take >= 1:
                return f"{big_idx},{take}"
            # If big_val == 1, can't leave 1, take it
            return f"{big_idx},1"
        else:
            # Leave 0 in big pile, making total ones = one_piles (odd)
            return f"{big_idx},{big_val}"
    
    # Normal play: try to make XOR = 0
    if xor != 0:
        for i in range(4):
            if piles[i] > 0:
                target = piles[i] ^ xor
                if target < piles[i]:
                    take = piles[i] - target
                    new_piles = apply_move(piles, i, take)
                    new_big, new_ones = analyze(new_piles)
                    
                    # Check if this leads to endgame with wrong parity
                    if new_big == 0 and new_ones % 2 == 0:
                        # This would be bad, try other moves
                        continue
                    
                    return f"{i},{take}"
        
        # If all XOR-zeroing moves lead to bad endgame, just make any legal move
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # XOR is already 0, we're in losing position, make any legal move
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    
    # Should never reach here if game state is valid
    return "0,1"
