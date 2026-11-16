
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert lists to sets for O(1) lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    occupied = my_stones | opp_stones
    
    # Define a 20x20 grid (index 0 unused, as rows/cols start at 1)
    # Preference scores: corners high, edges medium, center low
    scores = np.zeros((20, 20), dtype=int)
    for r in range(1, 20):
        for c in range(1, 20):
            if r == 1 or r == 19 or c == 1 or c == 19:
                scores[r][c] = 5  # Edges and corners
            else:
                scores[r][c] = 1  # Center
    
    # Find all empty spots with their scores, sorted by score desc, then row, then col
    candidates = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in occupied:
                candidates.append((scores[r][c], r, c))
    
    # If no candidates (though unlikely), pass
    if not candidates:
        return (0, 0)
    
    # Select the best: highest score, then smallest r, then smallest c
    best = max(candidates)
    return (best[1], best[2])
