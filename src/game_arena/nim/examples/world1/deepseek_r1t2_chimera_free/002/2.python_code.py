
def policy(piles: list[int]) -> str:
    # Check if all piles are 0 or 1
    if all(p <= 1 for p in piles):
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
    else:
        nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
        if nim_sum == 0:
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            for i in range(4):
                if piles[i] == 0:
                    continue
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    # Check if this move would leave all piles empty
                    all_zero = True
                    for j in range(4):
                        if j == i:
                            if target != 0:
                                all_zero = False
                        else:
                            if piles[j] != 0:
                                all_zero = False
                    if all_zero:
                        # Avoid leaving all zeros; take one less to leave one object
                        return f"{i},{piles[i] - 1}"
                    else:
                        return f"{i},{take}"
    # Fallback: take 1 from first non-zero pile (should not reach here)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
