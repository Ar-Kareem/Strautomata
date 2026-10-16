
def policy(piles: list[int]) -> str:
    greater_than_one = [i for i, p in enumerate(piles) if p > 1]
    
    # Case 1: Exactly one pile has size > 1.
    # We can directly force a win by leaving an odd number of piles of size 1.
    if len(greater_than_one) == 1:
        idx = greater_than_one[0]
        ones_count = sum(1 for i, p in enumerate(piles) if i != idx and p == 1)
        if ones_count % 2 == 1:
            # Leave ones_count ones by clearing this pile entirely.
            take = piles[idx]
        else:
            # Leave ones_count + 1 ones by reducing this pile to 1.
            take = piles[idx] - 1
        return f"{idx},{take}"

    # Case 2: All piles have size <= 1.
    if len(greater_than_one) == 0:
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        return "0,0"

    # Case 3: At least two piles have size > 1.
    # Standard Nim XOR-sum strategy.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                return f"{i},{p - target}"

    # Fallback if xor_sum == 0 (defensive move: take 1 from the largest pile)
    max_idx = max(range(len(piles)), key=lambda i: piles[i])
    return f"{max_idx},1"
