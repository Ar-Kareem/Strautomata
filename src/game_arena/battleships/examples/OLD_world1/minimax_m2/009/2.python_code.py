
def policy(board: list[list[int]]) -> tuple[int, int]:
    # First, collect all hit cells (value 1)
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
    
    if hits:
        # Build horizontal segments
        horizontal_segments = []
        for r in range(10):
            c = 0
            while c < 10:
                if board[r][c] == 1:
                    start = c
                    while c < 10 and board[r][c] == 1:
                        c += 1
                    end = c - 1
                    horizontal_segments.append((r, start, end))
                else:
                    c += 1
        
        # Build vertical segments
        vertical_segments = []
        for c in range(10):
            r = 0
            while r < 10:
                if board[r][c] == 1:
                    start = r
                    while r < 10 and board[r][c] == 1:
                        r += 1
                    end = r - 1
                    vertical_segments.append((start, end, c))
                else:
                    r += 1
        
        candidates = set()
        
        # Process horizontal segments
        for r, start, end in horizontal_segments:
            # Extend left
            if start - 1 >= 0 and board[r][start - 1] == 0:
                candidates.add((r, start - 1))
            # Extend right
            if end + 1 < 10 and board[r][end + 1] == 0:
                candidates.add((r, end + 1))
        
        # Process vertical segments
        for start, end, c in vertical_segments:
            # Extend up
            if start - 1 >= 0 and board[start - 1][c] == 0:
                candidates.add((start - 1, c))
            # Extend down
            if end + 1 < 10 and board[end + 1][c] == 0:
                candidates.add((end + 1, c))
        
        if candidates:
            candidates_list = list(candidates)
            candidates_list.sort(key=lambda x: (x[0], x[1]))
            return candidates_list[0]
    
    # If no candidates from hits, use pattern-based selection
    zero_cells = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                zero_cells.append((r, c))
    
    # Sort by: (r+c) mod 2 (even first), then by row, then by column
    zero_cells.sort(key=lambda x: ((x[0] + x[1]) % 2, x[0], x[1]))
    
    # It's guaranteed there is at least one 0 cell
    return zero_cells[0]
