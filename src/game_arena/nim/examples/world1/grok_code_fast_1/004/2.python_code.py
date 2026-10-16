
def policy(piles: list[int]) -> str:
    total_xor = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    if total_xor == 0:
        # Losing position in normal Nim: take 1 from the largest pile
        max_index = piles.index(max(piles))
        take = 1
        return f"{max_index},{take}"
    else:
        # Winning move: find a pile to adjust to make total_xor zero
        for i in range(4):
            s_i = total_xor ^ piles[i]
            take = piles[i] - s_i
            if 1 <= take <= piles[i]:
                return f"{i},{take}"
        # This should not happen in standard Nim theory, but as a safeguard
        return "0,1"  # Arbitrary legal move if needed
