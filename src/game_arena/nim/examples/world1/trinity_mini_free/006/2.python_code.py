
def policy(piles: list[int]) -> str:
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    if nim_sum != 0:
        for i in range(4):
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                return f"{i},{target}"
    else:
        for i in range(4):
            if piles[i] > 1:
                return f"{i},1"
        return "0,1"
