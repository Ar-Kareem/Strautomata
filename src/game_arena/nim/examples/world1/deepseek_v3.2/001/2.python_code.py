
import sys

def policy(piles: list[int]) -> str:
    # Misère Nim with 4 piles
    # Step 1: Compute nim-sum
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]

    if nim_sum != 0:
        # Find a winning move
        for i in range(4):
            if piles[i] == 0:
                continue
            target_size = piles[i] ^ nim_sum
            if target_size < piles[i]:
                take = piles[i] - target_size
                # Check misère adjustment for all piles <= 1 after move
                new_piles = piles.copy()
                new_piles[i] = target_size
                # If all resulting piles are 0 or 1
                if all(p <= 1 for p in new_piles):
                    # In misère Nim with all piles 0 or 1,
                    # we want to leave odd number of piles of size 1
                    ones_count = sum(p == 1 for p in new_piles)
                    if ones_count % 2 == 0:
                        # Need to make odd number of 1s
                        # Two cases: we are taking from a pile of size 1 or >1
                        if piles[i] == 1:
                            # Taking last 1 from this pile makes it 0
                            # That reduces ones_count by 1 -> parity flips, but
                            # Let's reconsider: if after move ones_count is even,
                            # current move is wrong. Instead take fewer or more?
                            # Actually, if we are taking from a pile > 1:
                            if piles[i] > 1:
                                # Maybe take more so that it becomes 0 not 1
                                # That reduces ones_count further
                                # If taking to 1 gives even ones, taking to 0 gives odd
                                # So adjust take to remove whole pile
                                take = piles[i]  # remove entire pile
                            else:
                                # piles[i]==1: removing it reduces ones count by 1,
                                # but we computed even ones after move.
                                # So we can't avoid even if only one 1 available? Then just take 1.
                                # Actually if only one pile of 1 exists and others 0,
                                # then taking it leaves all 0s (even number of 1s? zero is even)
                                # In misère, leaving all 0s means opponent took last? Wait
                                # Let's simplify: if after move all <=1, ensure ones odd.
                                # If impossible (like 2 piles size 1 left), just play normal move.
                                pass
                        else:
                            # piles[i] > 1
                            # We can take entire pile or leave 1.
                            # If leaving 1 gives even ones, leaving 0 might give odd.
                            if sum(1 for j, p in enumerate(piles) if p == 1) % 2 == 0:
                                # Currently even ones excluding pile i
                                # If we leave 0: ones same as before (since pile i was >1, not 1)
                                # Actually pile i currently >1, so not counted in ones.
                                # So leaving 0: ones_count = previous ones_count (even)
                                # leaving 1: ones_count = previous ones_count + 1 (odd)
                                # So we want odd -> leave 1
                                # target_size should be 1
                                target_size = 1
                                take = piles[i] - target_size
                            else:
                                # Currently odd ones excluding pile i
                                # leaving 0 -> ones_count odd (good)
                                # leaving 1 -> ones_count even (bad)
                                target_size = 0
                                take = piles[i] - target_size
                return f"{i},{take}"

    # If nim_sum == 0 (losing position) or no winning move found (shouldn't happen):
    # Take 1 from the largest non‑zero pile
    for take in range(1, max(piles) + 1):
        for i in range(4):
            if piles[i] >= take:
                return f"{i},{take}"
    # Should never reach here (at least one pile > 0 since game not ended)
    # Fallback: first legal move
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
