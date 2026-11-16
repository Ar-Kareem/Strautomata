
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Find all unknown cells
    unknown = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    
    if not unknown:
        return (0, 0)  # Should not happen in normal gameplay
    
    # Find all hit cells that might be part of unsunk ships
    hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]
    
    # Priority 1: Extend existing ship lines
    ship_lines = find_ship_lines(board)
    for line in ship_lines:
        extensions = get_line_extensions(line, board)
        if extensions:
            return extensions[0]
    
    # Priority 2: Hunt around isolated hits
    for r, c in hits:
        # Check if this hit has unknown neighbors (indicating unsunk ship)
        has_unknown_neighbor = False
        for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                has_unknown_neighbor = True
                break
        
        if has_unknown_neighbor:
            # Target adjacent unknown cells
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
    
    # Priority 3: Systematic search using checkerboard pattern
    # This ensures we hit any ship of length 2 or more
    for spacing in [2, 1]:  # Try spacing 2 first, then fill in
        for offset in range(spacing):
            for r in range(10):
                for c in range(10):
                    if board[r][c] == 0 and (r + c) % spacing == offset:
                        return (r, c)
    
    # Fallback - should not reach here
    return unknown[0]


def find_ship_lines(board):
    """Find sequences of 2 or more consecutive hits"""
    lines = []
    visited = set()
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1 and (r, c) not in visited:
                # Check horizontal line
                line = [(r, c)]
                for dc in [1, -1]:
                    nc = c + dc
                    while 0 <= nc < 10 and board[r][nc] == 1:
                        if dc == 1:
                            line.append((r, nc))
                        else:
                            line.insert(0, (r, nc))
                        nc += dc
                
                if len(line) > 1:
                    lines.append(line)
                    visited.update(line)
                    continue
                
                # Check vertical line
                line = [(r, c)]
                for dr in [1, -1]:
                    nr = r + dr
                    while 0 <= nr < 10 and board[nr][c] == 1:
                        if dr == 1:
                            line.append((nr, c))
                        else:
                            line.insert(0, (nr, c))
                        nr += dr
                
                if len(line) > 1:
                    lines.append(line)
                    visited.update(line)
                else:
                    visited.add((r, c))
    
    return lines


def get_line_extensions(line, board):
    """Get valid extensions for a line of hits"""
    if len(line) < 2:
        return []
    
    extensions = []
    
    # Determine if line is horizontal or vertical
    if line[0][0] == line[1][0]:  # Horizontal
        r = line[0][0]
        min_c = min(pos[1] for pos in line)
        max_c = max(pos[1] for pos in line)
        
        # Check left extension
        if min_c > 0 and board[r][min_c - 1] == 0:
            extensions.append((r, min_c - 1))
        
        # Check right extension  
        if max_c < 9 and board[r][max_c + 1] == 0:
            extensions.append((r, max_c + 1))
            
    else:  # Vertical
        c = line[0][1]
        min_r = min(pos[0] for pos in line)
        max_r = max(pos[0] for pos in line)
        
        # Check up extension
        if min_r > 0 and board[min_r - 1][c] == 0:
            extensions.append((min_r - 1, c))
        
        # Check down extension
        if max_r < 9 and board[max_r + 1][c] == 0:
            extensions.append((max_r + 1, c))
    
    return extensions
