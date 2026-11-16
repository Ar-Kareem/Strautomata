
from functools import reduce
from operator import xor

def policy(piles: list[int]) -> str:
    """
    Misère Nim policy for 4 piles. Return a legal move string "pile,take".
    Rules: player who takes last object loses.
    """
    # Ensure we have 4 piles (spec says length 4, but be robust)
    piles = list(piles)
    n = len(piles)

    # Find indices and counts
    nonzero_idxs = [i for i, p in enumerate(piles) if p > 0]
    if not nonzero_idxs:
        # No legal move; this situation shouldn't happen in the arena,
        # but return a dummy legal-looking move if possible (will be illegal).
        # To avoid returning an illegal move, we try to return "0,1" only if pile 0 has >=1.
        # Since all piles are zero, there is no legal move. As a fallback (shouldn't be used),
        # return "0,0" which is definitely illegal, but this branch is expected never to run.
        return "0,1"

    num_nonzero = len(nonzero_idxs)
    num_gt1 = sum(1 for p in piles if p > 1)

    # Helper to format move
    def fmt(i, take):
        if take < 1:
            take = 1
        if take > piles[i]:
            take = piles[i]
        return f"{i},{take}"

    # Case 1: all nonzero piles are 1 (i.e., max(piles) <= 1)
    if max(piles) <= 1:
        # If even number of nonzero piles, this is winning: remove one entire pile (take 1)
        # If odd, it's losing but we still must make a legal move: take 1 from any nonzero pile.
        i = nonzero_idxs[0]
        return fmt(i, 1)

    # Otherwise, at least one pile > 1: try to play like normal Nim (make XOR zero),
    # but avoid the pathological move that hands the opponent the correct parity when it matters.
    total_xor = reduce(xor, piles, 0)

    if total_xor == 0:
        # Losing position under normal Nim; make a safe reasonable move:
        # Prefer removing 1 from a pile >1 (safe), else remove 1 from any nonzero pile.
        for i in range(n):
            if piles[i] > 1:
                return fmt(i, 1)
        # fallback
        i = nonzero_idxs[0]
        return fmt(i, 1)
    else:
        # Try to find a pile to reduce such that XOR becomes zero
        for i in range(n):
            p = piles[i]
            target = p ^ total_xor
            if target < p:
                take = p - target  # amount to remove
                # Simulate resulting piles to check for the special misère adjustment:
                new_piles = piles.copy()
                new_piles[i] = target
                # Count how many piles would be >1 after this move
                num_gt1_after = sum(1 for val in new_piles if val > 1)
                # If the result would have no pile >1 (all piles 0/1),
                # then applying the standard move might flip the misère outcome.
                # In that case, instead remove p-1 (leaving one stone in this pile)
                # provided that's a legal (non-zero) removal.
                if num_gt1_after == 0:
                    # Only adjust if p > 1 (it is by construction here)
                    # leave exactly one in this pile
                    adj_take = p - 1
                    if adj_take >= 1 and adj_take <= p:
                        return fmt(i, adj_take)
                    # otherwise fall back to original take
                return fmt(i, take)
        # If no pile satisfies target < p (shouldn't happen when xor != 0),
        # fallback to a safe move: remove 1 from first pile >1, else any nonzero pile.
        for i in range(n):
            if piles[i] > 1:
                return fmt(i, 1)
        return fmt(nonzero_idxs[0], 1)
