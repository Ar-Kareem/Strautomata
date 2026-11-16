
import numpy as np

def policy(piles: list[int]) -> str:
    # Find all legal moves
    moves = []
    for pile in range(4):
        for take in range(1, piles[pile] + 1):
            moves.append((pile, take))
    
    # Check if all piles are 0 or 1 (endgame phase)
    if all(p <= 1 for p in piles):
        # Count number of ones
        ones = sum(p for p in piles if p == 1)
        # We want to leave an even number of ones (so opponent is forced to take last)
        for pile in range(4):
            if piles[pile] == 1:
                if (ones - 1) % 2 == 0:
                    return f"{pile},1"
        # If no such move (should not happen if at least one 1), fallback
        for pile in range(4):
            if piles[pile] > 0:
                return f"{pile},1"
    
    # Normal Nim strategy with misère adjustment
    # Compute current XOR (nim-sum)
    xor_all = 0
    for p in piles:
        xor_all ^= p
    
    # Try to find a move that makes nim-sum zero
    # But avoid moves that leave only piles of size 1 and odd count
    best_move = None
    for pile in range(4):
        for take in range(1, piles[pile] + 1):
            new_piles = piles[:]
            new_piles[pile] -= take
            # Check if this move leads to a "bad" state: all piles <= 1 and odd count
            if all(p <= 1 for p in new_piles):
                ones = sum(p for p in new_piles if p == 1)
                if ones % 2 == 1:
                    # This is bad: avoid if possible
                    continue
            # Compute new nim-sum
            new_xor = 0
            for p in new_piles:
                new_xor ^= p
            if new_xor == 0:
                return f"{pile},{take}"  # Perfect normal move
            # Store a fallback
            if best_move is None:
                best_move = (pile, take)
    
    # If no good move found (unlikely), fallback to any legal move
    if best_move is not None:
        return f"{best_move[0]},{best_move[1]}"
    
    # Last resort: just make a move
    for pile in range(4):
        if piles[pile] > 0:
            return f"{pile},1"
