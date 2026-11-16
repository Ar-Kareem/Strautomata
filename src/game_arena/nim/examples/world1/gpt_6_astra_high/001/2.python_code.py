
def policy(piles: list[int]) -> str:
    nonempty = [i for i, n in enumerate(piles) if n > 0]
    if not nonempty:
        raise ValueError("Terminal position: no legal move exists.")

    large = [i for i in nonempty if piles[i] > 1]
    ones = sum(n == 1 for n in piles)

    # With only singletons, every legal move removes one pile.
    if not large:
        return f"{nonempty[0]},1"

    # Leave an odd number of singletons for the opponent.
    if len(large) == 1:
        i = large[0]
        target = 0 if ones % 2 else 1
        return f"{i},{piles[i] - target}"

    # With at least two large piles, use the normal Nim XOR rule.
    nim_sum = 0
    for n in piles:
        nim_sum ^= n

    if nim_sum:
        for i in nonempty:
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                return f"{i},{piles[i] - target}"

    # This is a losing position against perfect play.
    # Keep the game going with a legal, minimal removal.
    i = max(nonempty, key=lambda j: piles[j])
    return f"{i},1"
