
def policy(piles: list[int]) -> str:
    p = [max(0, int(x)) for x in piles]
    try:
        s = 0
        for x in p:
            s ^= x
        big = [i for i, x in enumerate(p) if x > 1]
        ones = sum(1 for x in p if x == 1)

        if len(big) == 0:
            # Only piles of size 0/1: take a whole 1-pile.
            # Wins iff the number of 1-piles was even (leaving odd for opponent).
            for i, x in enumerate(p):
                if x == 1:
                    return f"{i},1"
        elif len(big) == 1:
            # Misère endgame correction: leave an ODD number of 1-piles.
            i = big[0]
            b = p[i]
            if ones % 2 == 0:
                take = b - 1  # leave this pile at size 1
            else:
                take = b      # remove this pile entirely
            if take >= 1:
                return f"{i},{take}"
        else:
            if s != 0:
                # Classic Nim move: zero the nim-sum.
                # With >=2 big piles this always yields a misere P-position.
                for i, x in enumerate(p):
                    t = x ^ s
                    if t < x:
                        return f"{i},{x - t}"
            # Losing position: maximize opponent's chance to blunder.
            if len(big) == 2:
                # Leave exactly one big pile: the normal-Nim response is always wrong in misere.
                i = big[0]
                return f"{i},{p[i]}"
            # Otherwise take 1 from the largest pile to prolong the game.
            i = max(range(len(p)), key=lambda j: p[j])
            if p[i] >= 1:
                return f"{i},1"
    except Exception:
        pass
    # Safety fallback: return any legal move.
    for i, x in enumerate(p):
        if x >= 1:
            return f"{i},1"
    return "0,1"
