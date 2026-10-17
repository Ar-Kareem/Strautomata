
import random
from typing import List, Tuple
import numpy as np

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship targeting policy for a 10x10 grid.

    board: list of lists with values:
      0 -> unknown
     -1 -> miss
      1 -> hit

    Returns a tuple (row, col) of an unknown cell to fire at.
    """
    # Convert to numpy array for convenience
    arr = np.array(board, dtype=int)
    if arr.shape != (10, 10):
        # Defensive: if shape unexpected, search for any unknown in a safe way
        for r in range(len(board)):
            for c in range(len(board[r])):
                if board[r][c] == 0:
                    return r, c
        # fallback
        return 0, 0

    # Ship lengths remaining in standard Battleship
    ship_lengths = [5, 4, 3, 3, 2]

    rows, cols = 10, 10

    # Heatmap of counts for each unknown cell
    heat = np.zeros((rows, cols), dtype=int)

    # For every ship length, count all placements that do not overlap misses.
    # Placements may overlap hits (we don't know which hits belong to which ship),
    # but they must not include any cell marked as miss (-1).
    for L in ship_lengths:
        # Horizontal placements
        for r in range(rows):
            for c in range(cols - L + 1):
                segment = arr[r, c:c+L]
                # invalid if any miss in placement
                if np.any(segment == -1):
                    continue
                # valid placement: increment heat on unknown cells within
                for offset in range(L):
                    rr, cc = r, c + offset
                    if arr[rr, cc] == 0:
                        heat[rr, cc] += 1
        # Vertical placements
        for c in range(cols):
            for r in range(rows - L + 1):
                segment = arr[r:r+L, c]
                if np.any(segment == -1):
                    continue
                for offset in range(L):
                    rr, cc = r + offset, c
                    if arr[rr, cc] == 0:
                        heat[rr, cc] += 1

    # Helper: get set of unknown neighbor coordinates adjacent to any hit
    hit_positions = list(zip(*np.where(arr == 1)))
    adjacent_unknowns = set()
    for (r, c) in hit_positions:
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols and arr[rr, cc] == 0:
                adjacent_unknowns.add((rr, cc))

    # If we have hits, prioritize adjacent unknowns (target mode).
    if adjacent_unknowns:
        # From adjacent unknowns choose the one with highest heat score.
        best_score = -1
        best_cells = []
        for cell in adjacent_unknowns:
            score = int(heat[cell])
            if score > best_score:
                best_score = score
                best_cells = [cell]
            elif score == best_score:
                best_cells.append(cell)
        # If all scores are zero, still choose one adjacent unknown at random.
        choice = random.choice(best_cells)
        return choice

    # Otherwise (hunt mode), pick unknown cell with maximum heat.
    # If heat is all zeros, pick any unknown cell.
    unknown_positions = list(zip(*np.where(arr == 0)))
    if not unknown_positions:
        # No unknowns left (shouldn't happen normally) -> return (0,0)
        return 0, 0

    # Flatten heat for unknown cells only
    max_heat = -1
    best_cells = []
    for cell in unknown_positions:
        score = int(heat[cell])
        if score > max_heat:
            max_heat = score
            best_cells = [cell]
        elif score == max_heat:
            best_cells.append(cell)

    if max_heat <= 0:
        # Heatmap offers no guidance (e.g., many misses). Use parity heuristic:
        # prefer (r+c) % 2 == 0 pattern for some efficiency, fallback to random.
        parity_cells = [cell for cell in unknown_positions if (cell[0] + cell[1]) % 2 == 0]
        if parity_cells:
            return random.choice(parity_cells)
        else:
            return random.choice(unknown_positions)

    return random.choice(best_cells)


# If run as a script, a tiny self-test to ensure function returns valid coordinates.
if __name__ == "__main__":
    # Empty board
    b = [[0]*10 for _ in range(10)]
    r, c = policy(b)
    assert 0 <= r < 10 and 0 <= c < 10 and b[r][c] == 0
    # Some hits and misses
    b[4][4] = 1
    b[4][5] = -1
    r, c = policy(b)
    assert 0 <= r < 10 and 0 <= c < 10 and b[r][c] == 0
    print("policy() basic checks passed.")
