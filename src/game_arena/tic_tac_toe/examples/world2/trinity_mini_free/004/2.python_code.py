
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define all possible winning lines (rows, columns, diagonals)
    lines = [
        [(0,0), (0,1), (0,2), (0,3)],  # Rows
        [(1,0), (1,1), (1,2), (1,3)],
        [(2,0), (2,1), (2,2), (2,3)],
        [(3,0), (3,1), (3,2), (3,3)],
        [(0,0), (1,0), (2,0), (3,0)],  # Columns
        [(0,1), (1,1), (2,1), (3,1)],
        [(0,2), (1,2), (2,2), (3,2)],
        [(0,3), (1,3), (2,3), (3,3)],
        [(0,0), (1,1), (2,2), (3,3)],  # Diagonals
        [(0,3), (1,2), (2,1), (3,0)]
    ]
    
    # Check for winning moves (3 of your marks + 1 empty)
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:  # Empty cell
                for line in lines:
                    if (i, j) in line:
                        count = 0
                        for (x, y) in line:
                            if (x, y) == (i, j):
                                continue
                            if board[x][y] == 1:
                                count += 1
                            elif board[x][y] == -1:
                                count -= 1
                        if count == 3:  # Three of your marks + one empty
                            return (i, j)
    
    # Check for blocking moves (3 opponent marks + 1 empty)
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                for line in lines:
                    if (i, j) in line:
                        count = 0
                        for (x, y) in line:
                            if (x, y) == (i, j):
                                continue
                            if board[x][y] == -1:
                                count -= 1
                            elif board[x][y] == 1:
                                count += 1
                        if count == -3:  # Three opponent marks + one empty
                            return (i, j)
    
    # Check for fork opportunities (creates two winning threats)
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                fork_lines = []
                for line in lines:
                    if (i, j) in line:
                        count = 0
                        for (x, y) in line:
                            if (x, y) == (i, j):
                                continue
                            if board[x][y] == 1:
                                count += 1
                            elif board[x][y] == -1:
                                count -= 1
                        if count == 2:  # Two of your marks + one empty
                            fork_lines.append(line)
                if len(fork_lines) >= 2:
                    return (i, j)
    
    # Prioritize center (cells (1,1), (1,2), (2,1), (2,2))
    center = [(1,1), (1,2), (2,1), (2,2)]
    for cell in center:
        if board[cell[0]][cell[1]] == 0:
            return cell
    
    # Prioritize corners (0,0), (0,3), (3,0), (3,3)
    corners = [(0,0), (0,3), (3,0), (3,3)]
    for cell in corners:
        if board[cell[0]][cell[1]] == 0:
            return cell
    
    # Prioritize edges (non-corner, non-center cells)
    edges = [(0,1), (0,2), (1,0), (1,3), (2,0), (2,3), (3,1), (3,2)]
    for cell in edges:
        if board[cell[0]][cell[1]] == 0:
            return cell
    
    # Fallback: random empty cell
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    return empty_cells[0] if empty_cells else (0, 0)
