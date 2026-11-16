
def policy(board: list[list[int]]) -> tuple[int, int]:
    # First, look for any hit that has an unknown neighbor
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:  # hit found
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10:
                        if board[nr][nc] == 0:  # unknown
                            return (nr, nc)
    
    # No unresolved hit found — go into hunt mode: compute likelihood map
    score = [[0] * 10 for _ in range(10)]
    ship_lengths = [2, 3, 3, 4, 5]  # including two ships of length 3
    
    for length in ship_lengths:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - length + 1):
                # Check if this segment is valid (no misses)
                valid = True
                for i in range(length):
                    if board[r][c+i] == -1:  # miss in the way
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        score[r][c+i] += 1
        # Vertical placements
        for c in range(10):
            for r in range(10 - length + 1):
                valid = True
                for i in range(length):
                    if board[r+i][c] == -1:  # miss in the way
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        score[r+i][c] += 1
    
    # Find the unknown cell with the highest score
    best_score = -1
    best_cell = (0, 0)
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:  # only consider unknown cells
                if score[r][c] > best_score:
                    best_score = score[r][c]
                    best_cell = (r, c)
    return best_cell
