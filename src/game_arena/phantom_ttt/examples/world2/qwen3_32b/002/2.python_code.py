
def policy(board: list[list[int]]) -> tuple[int, int]:
    lines = [
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)],
    ]
    
    # Check for winning move
    for line in lines:
        counts = [board[r][c] for r, c in line]
        if counts.count(1) == 2:
            for r, c in line:
                if board[r][c] == 0:
                    return (r, c)
    
    # Check for blocking move
    candidate_moves = []
    for line in lines:
        counts = [board[r][c] for r, c in line]
        mine = counts.count(1)
        if mine <= 1:
            zeros = counts.count(0)
            if zeros >= 2:
                for r, c in line:
                    if board[r][c] == 0:
                        candidate_moves.append((r, c))
    
    if candidate_moves:
        from collections import Counter
        cnt = Counter(candidate_moves)
        max_count = max(cnt.values())
        possible_cells = [cell for cell, count in cnt.items() if count == max_count]
        
        # Priority order: center, corners, edges
        def priority_key(cell):
            r, c = cell
            if (r, c) == (1, 1):
                return 0
            elif (r, c) in [(0,0), (0,2), (2,0), (2,2)]:
                return 1
            elif (r, c) in [(0,1), (1,0), (1,2), (2,1)]:
                return 2
            else:
                return 3
        
        possible_cells.sort(key=priority_key)
        return possible_cells[0]
    
    # Default strategy: center, then corners, then edges
    if board[1][1] == 0:
        return (1, 1)
    
    for cell in [(0,0), (0,2), (2,0), (2,2)]:
        r, c = cell
        if board[r][c] == 0:
            return (r, c)
    
    for cell in [(0,1), (1,0), (1,2), (2,1)]:
        r, c = cell
        if board[r][c] == 0:
            return (r, c)
    
    # Fallback (should never reach here)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return (r, c)
    
    return (0, 0)
