
def policy(piles: list[int]) -> str:
    # Misère Nim optimal strategy
    
    # Case 1: All piles are 0 or 1
    if all(p <= 1 for p in piles):
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        # Should not reach here (all zeros), but return valid format
        return "0,0"
    
    # Calculate nim-sum
    xor_sum = 0
    for p in piles:
        xor_sum ^= p
    
    # Case 2: P-position (losing), make any move
    if xor_sum == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Case 3: N-position (winning), find correct move
    for i, p in enumerate(piles):
        target = p ^ xor_sum
        if target < p:
            # Check if all other piles are 0 or 1 (misère exception)
            others_all_small = True
            other_ones_count = 0
            for j, pj in enumerate(piles):
                if j != i:
                    if pj > 1:
                        others_all_small = False
                        break
                    if pj == 1:
                        other_ones_count += 1
            
            # Adjust if we would leave only 1s in an even count
            if others_all_small:
                if target == 1 and other_ones_count % 2 == 1:
                    # Would leave even number of 1s, change to 0
                    target = 0
                elif target == 0 and other_ones_count % 2 == 0:
                    # Would leave even number of 1s, change to 1
                    target = 1
            
            return f"{i},{p - target}"
    
    # Fallback
    return "0,1"
