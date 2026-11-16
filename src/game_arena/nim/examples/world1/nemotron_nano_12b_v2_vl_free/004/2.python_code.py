
def policy(piles: list[int]) -> str:
    xor_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    for i in range(4):
        desired = piles[i] ^ xor_sum
        if desired < piles[i]:
            take = piles[i] - desired
            return f"{i},{take}"
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    return "0,0"  # This line is theoretically unreachable
