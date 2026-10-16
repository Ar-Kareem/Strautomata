
import random

def policy(piles: list[int]) -> str:
    # Helper to check if all piles are 0 or 1
    def all_le_one(piles):
        return all(p <= 1 for p in piles)
    
    # Find moves that make nim-sum zero (for normal-play winning move)
    def winning_moves(piles, nim_sum):
        moves = []
        for i, p in enumerate(piles):
            if p == 0:
                continue
            target = p ^ nim_sum  # pile size after move in normal play
            if target < p:  # can remove (p - target) objects
                take = p - target
                if take >= 1 and take <= p:
                    moves.append((i, take))
        return moves
    
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    # Special misère case: all piles <= 1
    if all_le_one(piles):
        # In misère nim with all piles <=1, take 1 if odd total piles of 1.
        # Actually simpler: in all <=1, take 1 from largest pile (>=1)
        # But careful: if piles are [1,1,1,1] -> taking 1 leaves [1,1,1,0], which is winning for opponent.
        # Wait, misère: [1,1,1,1], player to move loses if normal play? Let's follow standard rule:
        # In misère Nim with all piles <=1: winning move is take entire pile if number of piles with 1 is odd? Actually:
        # Standard rule: In misère nim, if all piles are 0 or 1, treat as normal play EXCEPT when only ones remain.
        # But known: In misère nim, if all piles size <=1, move to leave odd number of piles of size 1.
        # Let's implement that:
        ones = sum(piles)
        if ones % 2 == 1:
            # current position winning, take 1 from any pile
            for i, p in enumerate(piles):
                if p == 1:
                    return f"{i},1"
        else:
            # losing position, take 1 anyway (must move)
            for i, p in enumerate(piles):
                if p == 1:
                    return f"{i},1"
    
    # Not all piles <= 1
    if nim_sum == 0:
        # Losing position in normal play, but misère: remove objects to leave exactly one pile >1
        # Try to leave all piles <=1 except one pile with 1 object.
        # Find largest pile >1 and reduce to 1
        candidates = [(i, p) for i, p in enumerate(piles) if p > 1]
        if candidates:
            i, p = max(candidates, key=lambda x: x[1])
            take = p - 1
            return f"{i},{take}"
        else:
            # fallback: take from largest pile
            i = max(range(4), key=lambda x: piles[x])
            take = piles[i]
            return f"{i},{take}"
    
    # nim_sum != 0: winning in normal play
    moves = winning_moves(piles, nim_sum)
    
    # Filter moves that don't leave all piles <=1 (which would be bad in misère)
    safe_moves = []
    for i, take in moves:
        new_piles = piles.copy()
        new_piles[i] -= take
        if not all_le_one(new_piles):
            safe_moves.append((i, take))
    
    if safe_moves:
        # choose move removing most objects (aggressive)
        i, take = max(safe_moves, key=lambda x: x[1])
        return f"{i},{take}"
    
    # All winning moves leave all piles <=1 → adjust to avoid losing misère endgame
    # Try to leave odd number of piles of size 1 after move
    for i, take in moves:
        new_piles = piles.copy()
        new_piles[i] -= take
        if sum(new_piles) % 2 == 1:
            return f"{i},{take}"
    
    # fallback: first winning move
    if moves:
        i, take = moves[0]
        return f"{i},{take}"
    
    # No winning move (shouldn't happen since nim_sum !=0), take from largest pile
    i = max(range(4), key=lambda x: piles[x])
    take = 1
    return f"{i},{take}"
