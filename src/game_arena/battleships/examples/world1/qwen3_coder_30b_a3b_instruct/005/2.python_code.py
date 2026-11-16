
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Find all hit cells (1) and their adjacent unknown cells (0)
    hits = []
    adjacent_unknowns = []
    
    # Scan the board
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hits.append((i, j))
                # Check adjacent cells
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                        adjacent_unknowns.append((ni, nj))
    
    # If we have hits, fire at adjacent unknowns
    if adjacent_unknowns:
        # Return the first adjacent unknown cell we found
        return adjacent_unknowns[0]
    
    # If no hits, choose any random unknown cell
    unknowns = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                unknowns.append((i, j))
    
    if unknowns:
        return random.choice(unknowns)
    
    # This shouldn't happen in normal game flow
    # but if somehow all cells are fired at, return (0,0)
    return (0, 0)
