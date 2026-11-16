
def policy(piles: list[int]) -> str:
    n = len(piles)
    total_xor = 0
    for v in piles:
        total_xor ^= v

    def losing_for_next(after: list[int]) -> bool:
        """True if `after` is a P-position (losing for the player to move)
        under misere rules: last move loses."""
        xx = 0
        has_big = False
        ones = 0
        for v in after:
            xx ^= v
            if v > 1:
                has_big = True
            elif v == 1:
                ones += 1
        if has_big:
            return xx == 0
        # All piles are 0 or 1: player to move loses iff odd number of singles.
        return (ones % 2) == 1

    chosen = None

    if total_xor != 0:
        # Winning position: search for a move that leaves a P-position.
        candidates = []
        for i in range(n):
            size = piles[i]
            if size == 0:
                continue
            # Classic nim move: bring XOR to zero.
            target = size ^ total_xor
            if target < size:
                candidates.append((i, size - target))
            # Endgame parity fixes for singleton endgames.
            if size > 1:
                candidates.append((i, size - 1))  # leave a 1
                candidates.append((i, size))      # leave a 0
            else:  # size == 1
                candidates.append((i, 1))
        for i, take in candidates:
            after = piles[:]
            after[i] = piles[i] - take
            if losing_for_next(after):
                chosen = (i, take)
                break

    # Fallback (already-losing position, or pathological input): first legal move.
    if chosen is None:
        for i in range(n):
            if piles[i] > 0:
                chosen = (i, 1)
                break
    if chosen is None:
        # No objects remain; nothing legal exists, but output must not be empty.
        return "0,1"

    return f"{chosen[0]},{chosen[1]}"
