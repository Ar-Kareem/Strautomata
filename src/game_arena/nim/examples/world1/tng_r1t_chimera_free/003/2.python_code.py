
def policy(piles: list[int]) -> str:
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    if nim_sum != 0:
        for i in range(4):
            if piles[i] > (piles[i] ^ nim_sum):
                take = piles[i] - (piles[i] ^ nim_sum)
                # Check if this move leads to all piles being empty
                new_piles = piles.copy()
                new_piles[i] -= take
                if all(p == 0 for p in new_piles):
                    # Avoid losing by taking one less if possible
                    if piles[i] > 1:
                        take = piles[i] - 1
                        return f"{i},{take}"
                return f"{i},{take}"
    # If no winning move, take 1 from the first non-zero pile
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
