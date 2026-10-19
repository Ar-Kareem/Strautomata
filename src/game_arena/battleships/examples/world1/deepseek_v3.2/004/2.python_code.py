
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """Return (row, col) for next shot."""
    size = 10
    # Ship lengths (we assume all are still alive for probability calculation)
    ship_lengths = [5, 4, 3, 3, 2]
    
    # Helper to get cell value safely
    def get_cell(r, c):
        if 0 <= r < size and 0 <= c < size:
            return board[r][c]
        return None
    
    # 1. Target mode: find hits that have unknown neighbors
    hits_with_unknown = []
    for r in range(size):
        for c in range(size):
            if board[r][c] == 1:  # hit
                # Check if any adjacent cell is unknown (0)
                neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
                for nr, nc in neighbors:
                    if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == 0:
                        hits_with_unknown.append((r, c))
                        break
    
    if hits_with_unknown:
        # Try to find connected hits to determine orientation
        # Group hits that are adjacent in a line
        # For simplicity, for each hit, check if it has a neighbor hit in horizontal or vertical direction
        # Then target the ends of the line
        processed = set()
        for r, c in hits_with_unknown:
            if (r, c) in processed:
                continue
            # Check horizontal line
            line = [(r, c)]
            # left
            cr, cc = r, c
            while cc > 0 and board[cr][cc-1] == 1:
                cc -= 1
                line.append((cr, cc))
            # right
            cr, cc = r, c
            while cc < size-1 and board[cr][cc+1] == 1:
                cc += 1
                line.append((cr, cc))
            line = list(set(line))
            if len(line) > 1:
                # We have a horizontal line, target leftmost or rightmost unknown neighbor
                line.sort(key=lambda x: x[1])
                leftmost = line[0]
                rightmost = line[-1]
                # Check left of leftmost
                if leftmost[1] > 0 and board[leftmost[0]][leftmost[1]-1] == 0:
                    return (leftmost[0], leftmost[1]-1)
                # Check right of rightmost
                if rightmost[1] < size-1 and board[rightmost[0]][rightmost[1]+1] == 0:
                    return (rightmost[0], rightmost[1]+1)
                processed.update(line)
                continue
            
            # Check vertical line
            line = [(r, c)]
            # up
            cr, cc = r, c
            while cr > 0 and board[cr-1][cc] == 1:
                cr -= 1
                line.append((cr, cc))
            # down
            cr, cc = r, c
            while cr < size-1 and board[cr+1][cc] == 1:
                cr += 1
                line.append((cr, cc))
            line = list(set(line))
            if len(line) > 1:
                # Vertical line
                line.sort(key=lambda x: x[0])
                topmost = line[0]
                bottommost = line[-1]
                # Check above topmost
                if topmost[0] > 0 and board[topmost[0]-1][topmost[1]] == 0:
                    return (topmost[0]-1, topmost[1])
                # Check below bottommost
                if bottommost[0] < size-1 and board[bottommost[0]+1][bottommost[1]] == 0:
                    return (bottommost[0]+1, bottommost[1])
                processed.update(line)
                continue
            
            # Single hit, target any unknown neighbor
            neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
            random.shuffle(neighbors)  # Shuffle to avoid bias
            for nr, nc in neighbors:
                if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == 0:
                    return (nr, nc)
    
    # 2. Hunt mode: probability density targeting
    # For each unknown cell, compute how many possible ship placements cover it
    density = [[0 for _ in range(size)] for _ in range(size)]
    
    # Precompute all possible placements for each ship length
    # A placement is a list of (r,c) cells
    for length in ship_lengths:
        # Horizontal placements
        for r in range(size):
            for c in range(size - length + 1):
                # Check if all cells in this placement are not misses (-1)
                valid = True
                for i in range(length):
                    if board[r][c+i] == -1:
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        density[r][c+i] += 1
        # Vertical placements
        for r in range(size - length + 1):
            for c in range(size):
                valid = True
                for i in range(length):
                    if board[r+i][c] == -1:
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        density[r+i][c] += 1
    
    # Find unknown cells with maximum density
    max_density = -1
    candidates = []
    for r in range(size):
        for c in range(size):
            if board[r][c] == 0:  # unknown
                if density[r][c] > max_density:
                    max_density = density[r][c]
                    candidates = [(r, c)]
                elif density[r][c] == max_density:
                    candidates.append((r, c))
    
    if candidates:
        # Tie-break: prefer cells with parity (even sum) for checkerboard pattern in early game
        # Count how many unknown cells remain to decide if early game
        unknown_count = sum(1 for row in board for cell in row if cell == 0)
        if unknown_count > 50:  # early game
            # Filter to cells with even parity (row+col even)
            even_candidates = [(r, c) for (r, c) in candidates if (r + c) % 2 == 0]
            if even_candidates:
                candidates = even_candidates
        return random.choice(candidates)
    
    # Fallback: should not happen, but return any unknown cell
    for r in range(size):
        for c in range(size):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)  # should never reach here
