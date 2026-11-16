
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Precompute all winning lines in 3D Tic Tac Toe
    # Lines are represented as lists of (i,j,k) tuples
    lines = []
    
    # Horizontal lines (3 layers × 3 rows)
    for layer in range(3):
        for row in range(3):
            lines.append([(layer, row, col) for col in range(3)])
    
    # Vertical lines (3 layers × 3 columns)
    for layer in range(3):
        for col in range(3):
            lines.append([(layer, row, col) for row in range(3)])
    
    # Lines along third dimension (3 rows × 3 columns)
    for row in range(3):
        for col in range(3):
            lines.append([(layer, row, col) for layer in range(3)])
    
    # Face diagonals (3 layers × 2 diagonals per face)
    for layer in range(3):
        # Main diagonal of the layer
        lines.append([(layer, 0, 0), (layer, 1, 1), (layer, 2, 2)])
        # Anti-diagonal of the layer
        lines.append([(layer, 0, 2), (layer, 1, 1), (layer, 2, 0)])
    
    # Side face diagonals (columns)
    for col in range(3):
        # Main diagonal in column plane
        lines.append([(0, 0, col), (1, 1, col), (2, 2, col)])
        # Anti-diagonal in column plane
        lines.append([(0, 2, col), (1, 1, col), (2, 0, col)])
    
    # Side face diagonals (rows)
    for row in range(3):
        # Main diagonal in row plane
        lines.append([(0, row, 0), (1, row, 1), (2, row, 2)])
        # Anti-diagonal in row plane
        lines.append([(0, row, 2), (1, row, 1), (2, row, 0)])
    
    # Space diagonals (4 main ones)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    # Additional space diagonals (6 more)
    lines.append([(0, 0, 1), (1, 1, 1), (2, 2, 1)])
    lines.append([(0, 1, 0), (1, 1, 1), (2, 1, 2)])
    lines.append([(0, 2, 1), (1, 1, 1), (2, 0, 1)])
    lines.append([(0, 1, 2), (1, 1, 1), (2, 1, 0)])
    lines.append([(1, 0, 0), (1, 1, 1), (1, 2, 2)])
    lines.append([(1, 0, 2), (1, 1, 1), (1, 2, 0)])
    
    # Get all empty cells
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))
    
    # If no empty cells, return (0,0,0) as fallback (shouldn't happen in valid game)
    if not empty_cells:
        return (0, 0, 0)
    
    # If only one empty cell, take it
    if len(empty_cells) == 1:
        return empty_cells[0]
    
    best_score = float('-inf')
    best_move = empty_cells[0]
    
    for move in empty_cells:
        i, j, k = move
        score = 0
        
        # Score based on winning lines
        for line in lines:
            if (i, j, k) not in line:
                continue
                
            # Count my marks and opponent marks in this line
            my_count = 0
            opp_count = 0
            empty_count = 0
            empty_pos = None
            
            for (li, lj, lk) in line:
                val = board[li][lj][lk]
                if val == 1:
                    my_count += 1
                elif val == -1:
                    opp_count += 1
                else:
                    empty_count += 1
                    empty_pos = (li, lj, lk)
            
            # Check if this move completes a line for me
            if my_count == 2 and empty_count == 1 and empty_pos == (i, j, k):
                score += 1000
            
            # Check if this move blocks opponent's immediate win
            if opp_count == 2 and empty_count == 1 and empty_pos == (i, j, k):
                score += 800
            
            # Check for two-in-a-line threats (after this move)
            # Simulate the move
            board[i][j][k] = 1
            
            # Check if this move creates a two-in-a-line threat
            my_count_after = 0
            opp_count_after = 0
            empty_count_after = 0
            
            for (li, lj, lk) in line:
                val = board[li][lj][lk]
                if val == 1:
                    my_count_after += 1
                elif val == -1:
                    opp_count_after += 1
                else:
                    empty_count_after += 1
            
            if my_count_after == 2 and empty_count_after == 1:
                score += 10
            
            if opp_count_after == 2 and empty_count_after == 1:
                score += 9
            
            # Undo the simulated move
            board[i][j][k] = 0
        
        # Center control (1,1,1) is most important
        if (i, j, k) == (1, 1, 1):
            score += 5
        
        # Corners are next (they participate in more lines than edges)
        corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
                   (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
        if (i, j, k) in corners:
            score += 3
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
