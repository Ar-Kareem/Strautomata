
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Precompute all 49 winning lines if not already done
    if not hasattr(policy, "_lines"):
        lines = []
        # Axis-aligned lines (27 total)
        for i in range(3):
            for j in range(3):
                lines.append([(i, j, 0), (i, j, 1), (i, j, 2)])  # z-axis
                lines.append([(i, 0, j), (i, 1, j), (i, 2, j)])  # y-axis
                lines.append([(0, i, j), (1, i, j), (2, i, j)])  # x-axis
        
        # Face diagonals (18 total)
        for k in range(3):
            lines.append([(0, 0, k), (1, 1, k), (2, 2, k)])  # xy plane diag 1
            lines.append([(0, 2, k), (1, 1, k), (2, 0, k)])  # xy plane diag 2
        for j in range(3):
            lines.append([(0, j, 0), (1, j, 1), (2, j, 2)])  # xz plane diag 1
            lines.append([(0, j, 2), (1, j, 1), (2, j, 0)])  # xz plane diag 2
        for i in range(3):
            lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])  # yz plane diag 1
            lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])  # yz plane diag 2
        
        # Space diagonals (4 total)
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])
        
        # Map each cell to the lines that pass through it
        cell_to_lines = {}
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    cell_to_lines[(i, j, k)] = []
        for line_idx, line in enumerate(lines):
            for cell in line:
                cell_to_lines[cell].append(line_idx)
        
        policy._lines = lines
        policy._cell_to_lines = cell_to_lines
    
    lines = policy._lines
    cell_to_lines = policy._cell_to_lines
    
    # Get empty cells
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))
    
    if not empty_cells:
        # Should not happen in a valid game, but return a dummy
        return (0, 0, 0)
    
    # Helper to check if player has won by placing at cell
    def is_winning_move(cell, player):
        i, j, k = cell
        for line_idx in cell_to_lines[cell]:
            line = lines[line_idx]
            # Count marks in this line after hypothetical placement
            count_player = 0
            count_empty = 0
            for (x, y, z) in line:
                val = board[x][y][z]
                if val == player:
                    count_player += 1
                elif val == 0:
                    count_empty += 1
            # If we place at cell, cell becomes player, so if currently empty:
            count_player += 1  # The cell we're placing into
            count_empty -= 1
            if count_player == 3 and count_empty == 0:
                return True
        return False
    
    # Helper to check if move creates a fork (two threats)
    def creates_fork(cell, player):
        i, j, k = cell
        threat_count = 0
        for line_idx in cell_to_lines[cell]:
            line = lines[line_idx]
            count_player = 0
            count_opponent = 0
            count_empty = 0
            for (x, y, z) in line:
                val = board[x][y][z]
                if val == player:
                    count_player += 1
                elif val == 0:
                    count_empty += 1
                else:
                    count_opponent += 1
            
            # After placing at cell:
            if board[i][j][k] == 0:
                count_player += 1
                count_empty -= 1
            
            # A threat is 2 of player, 0 of opponent, 1 empty
            if count_player == 2 and count_opponent == 0 and count_empty == 1:
                threat_count += 1
        return threat_count >= 2
    
    # Priority 1: Find winning move
    for cell in empty_cells:
        if is_winning_move(cell, 1):
            return cell
    
    # Priority 2: Block opponent winning move
    for cell in empty_cells:
        if is_winning_move(cell, -1):
            return cell
    
    # Priority 3: Create fork
    for cell in empty_cells:
        if creates_fork(cell, 1):
            return cell
    
    # Priority 4: Block opponent fork
    for cell in empty_cells:
        if creates_fork(cell, -1):
            return cell
    
    # Priority 5: Center
    if (1, 1, 1) in empty_cells:
        return (1, 1, 1)
    
    # Priority 6: Corners
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for cell in corners:
        if cell in empty_cells:
            return cell
    
    # Priority 7: Any available move
    return empty_cells[0]
