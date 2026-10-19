
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Determine target sides based on color
    if color == 'b':
        target_sides = [0, 10]  # Black connects top (0) and bottom (10)
    else:
        target_sides = [0, 10]  # White connects left (0) and right (10)
    
    # Generate all empty cells
    empty_cells = []
    for i in range(11):
        for j in range(11):
            if (i, j) not in me and (i, j) not in opp:
                empty_cells.append((i, j))
    
    # Prioritize edge moves
    for cell in empty_cells:
        i, j = cell
        if color == 'b':
            if i == 0 or i == 10:
                return cell
        else:
            if j == 0 or j == 10:
                return cell
    
    # Prioritize moves adjacent to own stones
    for cell in empty_cells:
        i, j = cell
        neighbors = [
            (i-1, j), (i-1, j+1),
            (i, j-1), (i, j+1),
            (i+1, j), (i+1, j+1)
        ]
        for ni, nj in neighbors:
            if (ni, nj) in me:
                return cell
    
    # Prioritize moves adjacent to opponent's stones
    for cell in empty_cells:
        i, j = cell
        neighbors = [
            (i-1, j), (i-1, j+1),
            (i, j-1), (i, j+1),
            (i+1, j), (i+1, j+1)
        ]
        for ni, nj in neighbors:
            if (ni, nj) in opp:
                return cell
    
    # Fallback to random move
    return random.choice(empty_cells)
