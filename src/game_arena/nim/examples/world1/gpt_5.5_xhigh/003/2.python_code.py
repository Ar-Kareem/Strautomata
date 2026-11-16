
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim:
    - Taking the last object loses.
    - Return format: 'pile,take'
    """
    ps = [int(x) for x in piles]

    nonzero = [i for i, p in enumerate(ps) if p > 0]
    if not nonzero:
        # Terminal positions should not be queried; no legal move exists.
        return "0,0"

    ones_count = sum(1 for p in ps if p == 1)
    big = [i for i, p in enumerate(ps) if p > 1]

    # If all non-empty piles are size 1, the only legal move is to take 1.
    if not big:
        return f"{nonzero[0]},1"

    # Misere Nim endgame: exactly one pile is larger than 1.
    # Leave an odd number of size-1 piles for the opponent.
    if len(big) == 1:
        i = big[0]
        target = 0 if (ones_count % 2 == 1) else 1
        take = ps[i] - target
        return f"{i},{take}"

    # With at least two piles larger than 1, play normal Nim unless xor is zero.
    xor_sum = 0
    for p in ps:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(ps):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                return f"{i},{take}"

    # The position is losing under perfect play. Any legal move is equivalent
    # theoretically, but choose a move that can punish non-misere opponents.
    if len(big) == 2:
        a, b = big

        # Prefer leaving the larger pile as the only big pile.
        if ps[a] > ps[b]:
            reduce_pile = b
        elif ps[b] > ps[a]:
            reduce_pile = a
        else:
            reduce_pile = a

        # Make the number of singleton piles even; many normal-Nim/greedy
        # policies will then take the whole big pile and lose.
        target = ones_count % 2
        take = ps[reduce_pile] - target
        if 1 <= take <= ps[reduce_pile]:
            return f"{reduce_pile},{take}"

    # General legal fallback for lost xor-zero positions with 3+ big piles.
    i = max(big, key=lambda k: ps[k])
    target = 1 if (ones_count % 2 == 1) else 0
    take = ps[i] - target
    if take < 1:
        take = 1
    return f"{i},{take}"
