
def policy(piles):
    """
    Return a legal move for the given 4‑pile misère Nim position.
    The move is a string "pile,take" where pile is a 0‑based index
    and take is the number of objects removed (≥1).
    """
    # classify piles
    ones = [i for i, p in enumerate(piles) if p == 1]          # size‑1 piles
    bigs = [i for i, p in enumerate(piles) if p > 1]           # piles larger than 1

    # --------------------------------------------------------------
    # 1) No pile larger than 1 – we only have 0/1 piles.
    # --------------------------------------------------------------
    if not bigs:
        # There must be at least one non‑zero pile, otherwise the game is over.
        # Any 1‑pile is a legal move; taking it flips the parity of the
        # remaining 1‑piles, which is the correct strategy for misère Nim.
        i = ones[0]                # pick the first size‑1 pile
        return f"{i},1"

    # --------------------------------------------------------------
    # 2) Exactly one pile larger than 1 – special misère handling.
    # --------------------------------------------------------------
    if len(bigs) == 1:
        i = bigs[0]
        b = piles[i]               # size of the unique large pile
        c1 = len(ones)              # how many size‑1 piles exist

        # We want to leave an odd number of size‑1 piles for the opponent.
        if c1 % 2 == 0:            # even ⇒ adding one more 1 makes it odd
            take = b - 1            # reduce the big pile to size 1
        else:                      # odd ⇒ removing the big pile keeps it odd
            take = b                # remove the whole big pile
        return f"{i},{take}"

    # --------------------------------------------------------------
    # 3) Two or more piles larger than 1 – normal Nim rule applies.
    # --------------------------------------------------------------
    # Compute nim‑sum
    nim = 0
    for p in piles:
        nim ^= p

    # If nim != 0 we can win by making nim‑sum zero.
    if nim != 0:
        for i, p in enumerate(piles):
            if p == 0:
                continue
            wanted = p ^ nim
            if wanted < p:               # legal reduction
                take = p - wanted
                return f"{i},{take}"

    # --------------------------------------------------------------
    # 4) Losing position (nim == 0 or no winning move found) –
    #    just take a single object from the first non‑zero pile.
    # --------------------------------------------------------------
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"

    # Fallback (should never be reached because the game ends when all piles are 0)
    return "0,0"
