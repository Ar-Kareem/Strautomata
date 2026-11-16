
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Step 1: Check for immediate captures (horizontal edges)
    for r in range(5):
        for c in range(4):
            if horizontal[r][c] == 0:
                captures = []
                if r > 0:
                    # Check box (r-1, c)
                    if horizontal[r-1][c] == 1 and vertical[r-1][c] == 1 and vertical[r-1][c+1] == 1:
                        captures.append((r-1, c))
                if r < 4:
                    # Check box (r, c)
                    if horizontal[r+1][c] == 1 and vertical[r][c] == 1 and vertical[r][c+1] == 1:
                        captures.append((r, c))
                if captures:
                    return f"{r},{c},H"
    
    # Step 2: Check for immediate captures (vertical edges)
    for r in range(4):
        for c in range(5):
            if vertical[r][c] == 0:
                captures = []
                if c > 0:
                    # Check box (r, c-1)
                    if horizontal[r][c-1] == 1 and horizontal[r+1][c-1] == 1 and vertical[r][c-1] == 1:
                        captures.append((r, c-1))
                if c < 4:
                    # Check box (r, c)
                    if horizontal[r][c] == 1 and horizontal[r+1][c] == 1 and vertical[r][c+1] == 1:
                        captures.append((r, c))
                if captures:
                    return f"{r},{c},V"
    
    # Step 3: Check for danger zones (boxes with three edges drawn)
    for i in range(4):
        for j in range(4):
            edges = [
                horizontal[i][j],        # top
                horizontal[i+1][j],      # bottom
                vertical[i][j],          # left
                vertical[i][j+1]         # right
            ]
            count_drawn = sum(1 for e in edges if e == 1)
            count_available = sum(1 for e in edges if e == 0)
            if count_drawn == 3 and count_available == 1:
                if horizontal[i][j] == 0:
                    return f"{i},{j},H"
                elif horizontal[i+1][j] == 0:
                    return f"{i+1},{j},H"
                elif vertical[i][j] == 0:
                    return f"{i},{j},V"
                elif vertical[i][j+1] == 0:
                    return f"{i},{j+1},V"
    
    # Step 4: Check for safe moves (no captures or dangers)
    for r in range(5):
        for c in range(4):
            if horizontal[r][c] == 0:
                danger_created = False
                for i in range(4):
                    for j in range(4):
                        edges = [
                            horizontal[i][j],        # top
                            horizontal[i+1][j],      # bottom
                            vertical[i][j],          # left
                            vertical[i][j+1]         # right
                        ]
                        count_drawn = sum(1 for e in edges if e == 1)
                        count_available = sum(1 for e in edges if e == 0)
                        if count_drawn == 3 and count_available == 1:
                            danger_created = True
                            break
                    if danger_created:
                        break
                if not danger_created:
                    return f"{r},{c},H"
    
    for r in range(4):
        for c in range(5):
            if vertical[r][c] == 0:
                danger_created = False
                for i in range(4):
                    for j in range(4):
                        edges = [
                            horizontal[i][j],        # top
                            horizontal[i+1][j],      # bottom
                            vertical[i][j],          # left
                            vertical[i][j+1]         # right
                        ]
                        count_drawn = sum(1 for e in edges if e == 1)
                        count_available = sum(1 for e in edges if e == 0)
                        if count_drawn == 3 and count_available == 1:
                            danger_created = True
                            break
                    if danger_created:
                        break
                if not danger_created:
                    return f"{r},{c},V"
    
    # Fallback: Return any available edge
    for r in range(5):
        for c in range(4):
            if horizontal[r][c] == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if vertical[r][c] == 0:
                return f"{r},{c},V"
