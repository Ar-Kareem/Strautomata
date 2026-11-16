
# Misere Nim policy for 4 piles.
# Return format: "pile,take"

def _fmt(pile: int, take: int) -> str:
    return f"{pile},{take}"


def policy(piles: list[int]) -> str:
    p = [int(x) for x in piles]

    positive = [i for i, h in enumerate(p) if h > 0]
    if not positive:
        # Terminal positions should not be queried; no legal move exists.
        return "0,0"

    ones = [i for i, h in enumerate(p) if h == 1]
    bigs = [i for i, h in enumerate(p) if h > 1]

    # Endgame: all non-empty piles are singletons.
    # With misere play, odd singleton count is losing, even is winning;
    # either way the only legal kind of move is to take one singleton.
    if not bigs:
        return _fmt(positive[0], 1)

    # Exactly one pile larger than 1:
    # leave the opponent an odd number of singleton piles.
    if len(bigs) == 1:
        i = bigs[0]
        h = p[i]
        if len(ones) % 2 == 1:
            # Already odd singletons: remove the large pile.
            return _fmt(i, h)
        else:
            # Even singletons: reduce the large pile to one singleton.
            return _fmt(i, h - 1)

    # More than one large pile: normal Nim xor logic applies.
    xor_sum = 0
    for h in p:
        xor_sum ^= h

    if xor_sum != 0:
        # Winning move: reduce one pile so the xor becomes zero.
        # Prefer moves that simplify the game while preserving optimality.
        best_move = None
        best_key = None

        for i, h in enumerate(p):
            target = h ^ xor_sum
            if target < h:
                take = h - target
                new_big_count = 0
                new_total = 0

                for j, v in enumerate(p):
                    nv = target if j == i else v
                    new_total += nv
                    if nv > 1:
                        new_big_count += 1

                key = (new_big_count, new_total)
                if best_move is None or key < best_key:
                    best_move = (i, take)
                    best_key = key

        if best_move is not None:
            return _fmt(best_move[0], best_move[1])

    # xor_sum == 0 with at least two large piles is theoretically losing
    # against perfect play. Return a legal bait move.

    if len(bigs) == 2:
        # Create a one-large-pile position with an even number of singletons.
        # Many normal-Nim or greedy policies will incorrectly take the whole
        # large pile instead of reducing it to one.
        i = min(bigs, key=lambda idx: p[idx])
        if len(ones) % 2 == 0:
            return _fmt(i, p[i])
        else:
            return _fmt(i, p[i] - 1)

    # More than two large piles: remove the smallest large pile to move toward
    # the tricky endgame while always staying legal.
    i = min(bigs, key=lambda idx: p[idx])
    return _fmt(i, p[i])
