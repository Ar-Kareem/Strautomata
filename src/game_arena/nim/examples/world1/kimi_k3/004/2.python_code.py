
def policy(piles: list[int]) -> str:
    # Classify piles: singletons (size 1), big piles (size > 1), largest pile.
    big = -1          # index of one big pile
    n_big = 0         # number of piles with size > 1
    n_ones = 0        # number of piles with size exactly 1
    first_one = -1    # index of a singleton pile
    largest = -1      # index of the largest pile

    for i, p in enumerate(piles):
        if p > 1:
            n_big += 1
            big = i
        elif p == 1:
            n_ones += 1
            if first_one < 0:
                first_one = i
        if largest < 0 or p > piles[largest]:
            largest = i

    # Game already over (should never be reached); return a dummy string.
    if largest < 0 or piles[largest] == 0:
        return "0,1"

    # Case 1: only piles of size 0 or 1 remain.
    # Misere endgame: we want to leave an ODD number of singletons.
    # Taking one whole singleton does that whenever the position is winnable;
    # if an odd number of singletons remains, the position is lost anyway.
    if n_big == 0:
        return f"{first_one},1"

    # Case 2: exactly one big pile (always a winning position).
    # Reduce it to 0 or 1 so the opponent faces an odd number of singletons.
    if n_big == 1:
        if n_ones % 2 == 0:
            # Leave the big pile at size 1 -> n_ones + 1 (odd) singletons.
            return f"{big},{piles[big] - 1}"
        # Take the entire big pile -> n_ones (odd) singletons remain.
        return f"{big},{piles[big]}"

    # Case 3: two or more big piles -> misere Nim plays like normal Nim.
    # Move to nim-sum (XOR) zero, which is a losing position for the opponent
    # (after such a move at least one big pile always remains).
    s = 0
    for p in piles:
        s ^= p
    if s != 0:
        for i, p in enumerate(piles):
            target = p ^ s
            if target < p:
                return f"{i},{p - target}"

    # Nim-sum already zero: lost against perfect play. Stall by removing a
    # single object from the largest pile, maximizing the opponent's
    # opportunities to err.
    return f"{largest},1"
