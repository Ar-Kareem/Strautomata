
# Precomputed pattern: all cells in checkerboard order (even parity first, then odd parity)
PATTERN = []
for i in range(10):
    for j in range(10):
        if (i + j) % 2 == 0:
            PATTERN.append((i, j))
for i in range(10):
    for j in range(10):
        if (i + j) % 2 == 1:
            PATTERN.append((i, j))

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Find all hit cells
    hits = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hits.append((i, j))
    
    # If there are no hits, use the checkerboard pattern
    if not hits:
        for (i, j) in PATTERN:
            if board[i][j] == 0:
                return (i, j)
        # If no cell in pattern is 0, scan the entire board
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    return (i, j)
        # Should not happen, but return (0,0) arbitrarily if no unknown cell is found
        return (0, 0)
    
    # Otherwise, we have hits. Try to extend from hits.
    candidate_dict = {}
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for (i, j) in hits:
        for (dx, dy) in directions:
            x, y = i, j
            chain_length = 0
            # Move in the direction until we hit a non-hit or go out of bounds
            while 0 <= x + dx * (chain_length + 1) < 10 and 0 <= y + dy * (chain_length + 1) < 10 and board[x + dx * (chain_length + 1)][y + dy * (chain_length + 1)] == 1:
                chain_length += 1
            
            # Calculate the candidate cell after the chain
            nx = x + dx * (chain_length + 1)
            ny = y + dy * (chain_length + 1)
            
            # If the candidate is within bounds and is unknown, consider it
            if 0 <= nx < 10 and 0 <= ny < 10 and board[nx][ny] == 0:
                if (nx, ny) not in candidate_dict:
                    candidate_dict[(nx, ny)] = chain_length
                else:
                    candidate_dict[(nx, ny)] = max(candidate_dict[(nx, ny)], chain_length)
    
    # If we found candidates, choose the one from the longest chain
    if candidate_dict:
        # Sort by chain_length descending, then by candidate lex order
        sorted_candidates = sorted(candidate_dict.items(), key=lambda x: (-x[1], x[0]))
        return sorted_candidates[0][0]
    
    # If no candidates from hits, fall back to the pattern
    for (i, j) in PATTERN:
        if board[i][j] == 0:
            return (i, j)
    # Fallback: scan the entire board
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)
    # Should not happen
    return (0, 0)
