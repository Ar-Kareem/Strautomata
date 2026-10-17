
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define all possible lines (rows, columns, diagonals)
    lines = [
        # Rows
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        # Columns
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        # Diagonals
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)]
    ]
    
    # Generate all legal moves (cells marked as 0)
    possible_moves = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    if not possible_moves:
        return (0, 0)  # Fallback if no moves (shouldn't occur)
    
    # Step 1: Check for immediate winning moves
    for (r, c) in possible_moves:
        # Check all lines containing (r, c)
        for line in lines:
            if (r, c) not in line:
                continue
            # Count existing '1's excluding current cell
            count = 0
            for (x, y) in line:
                if (x, y) == (r, c):
                    continue
                if board[x][y] != 1:
                    break
                count += 1
            if count == 2:  # This move completes the line
                return (r, c)
    
    # Step 2: Check for fork opportunities
    for (r, c) in possible_moves:
        # Simulate placing a '1' at (r, c)
        sim_board = [row.copy() for row in board]
        sim_board[r][c] = 1
        fork_count = 0
        # Check all lines for potential wins in next move
        for line in lines:
            ones = 0
            zeros = 0
            for (x, y) in line:
                if sim_board[x][y] == 1:
                    ones += 1
                elif sim_board[x][y] == 0:
                    zeros += 1
            if ones == 2 and zeros == 1:
                fork_count += 1
                if fork_count >= 2:
                    return (r, c)  # Found a fork
    
    # Step 3: Take center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Step 4: Take any available corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for (r, c) in corners:
        if board[r][c] == 0:
            return (r, c)
    
    # Step 5: Take any available edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for (r, c) in edges:
        if board[r][c] == 0:
            return (r, c)
    
    return possible_moves[0]  # Fallback (should never be reached)
