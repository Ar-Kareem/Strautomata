
def policy(piles: list[int]) -> str:
    # Count piles strictly greater than 1 and piles equal to 1
    gt_one_indices = [i for i, count in enumerate(piles) if count > 1]
    
    if len(gt_one_indices) == 1:
        idx = gt_one_indices[0]
        # Count remaining piles of size 1 (excluding the one > 1)
        ones_count = sum(1 for i, count in enumerate(piles) if i != idx and count == 1)
        # We want to leave the opponent with an odd number of piles of size 1
        if ones_count % 2 == 1:
            # Leave 0 in this pile so the total ones remain odd
            return f"{idx},{piles[idx]}"
        else:
            # Leave 1 in this pile so total ones become ones_count + 1 (odd)
            return f"{idx},{piles[idx] - 1}"
            
    elif len(gt_one_indices) == 0:
        # All piles are <= 1; take 1 from any non-empty pile
        for i, count in enumerate(piles):
            if count == 1:
                return f"{i},1"
                
    else:
        # More than one pile > 1: play standard Nim (set XOR sum to 0)
        xor_sum = 0
        for count in piles:
            xor_sum ^= count
            
        if xor_sum != 0:
            for i, count in enumerate(piles):
                target = count ^ xor_sum
                if target < count:
                    return f"{i},{count - target}"

    # Fallback if already in a losing position (nim-sum == 0): take 1 from the largest pile
    best_idx = max(range(len(piles)), key=lambda i: piles[i])
    return f"{best_idx},1"
