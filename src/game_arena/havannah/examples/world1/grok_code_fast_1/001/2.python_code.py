
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    N = 15
    # Collect legal moves: unoccupied and valid
    legal = [(r, c) for r in range(N) for c in range(N) 
             if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp]
    
    # Prioritize center if available
    if (7, 7) in legal:
        return (7, 7)
    else:
        # Random legal move, guaranteed non-empty during active game
        return random.choice(legal)
