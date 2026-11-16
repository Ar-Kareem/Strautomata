
# Python source code for the policy function

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines in 3x3x3 Tic Tac Toe
    all_lines = []
    
    # Axis-aligned lines along x, y, and z axes
    for y in range(3):
        for z in range(3):
            all_lines.append([(x, y, z) for x in range(3)])
    
    for x in range(3):
        for z in range(3):
            all_lines.append([(x, y, z) for y in range(3)])
    
    for x in range(3):
        for y in range(3):
            all_lines.append([(x, y, z) for z in range(3)])
    
    # Diagonals in z-fixed planes (xy planes)
    for z in range(3):
        all_lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        all_lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Diagonals in x-fixed planes (yz planes)
    for x in range(3):
        all_lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        all_lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    
    # Diagonals in y-fixed planes (xz planes)
    for y in range(3):
        all_lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        all_lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    
    # Space diagonals (4 in total)
    space_diagonals = [
        [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
        [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
        [(0, 2, 2), (1, 1, 1), (2, 0, 0)]
    ]
    all_lines.extend(space_diagonals)
    
    # Check for immediate winning move for me
    winning_moves = []
    for line in all_lines:
        my_count = sum(board[i][j][k] == 1 for i, j, k in line)
        if my_count == 2:
            for i, j, k in line:
                if board[i][j][k] == 0:
                    winning_moves.append((i, j, k))
                    break  # Take the first possible winning move
    
    if winning_moves:
        return winning_moves[0]
    
    # Block opponent's winning move
    block_moves = []
    for line in all_lines:
        opponent_count = sum(board[i][j][k] == -1 for i, j, k in line)
        if opponent_count == 2:
            for i, j, k in line:
                if board[i][j][k] == 0:
                    block_moves.append((i, j, k))
                    break  # Block the opponent's immediate win
    
    if block_moves:
        return block_moves[0]
    
    # Heuristic move selection
    priority_order = [
        (1, 1, 1),  # Center cell
        # Corners (highest priority after center)
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2),
        # Face centers
        (1, 1, 0), (1, 1, 2),
        (1, 0, 1), (1, 2, 1),
        (0, 1, 1), (2, 1, 1),
        # Edge centers (one coordinate is 1)
        (1, 0, 0), (1, 0, 2),
        (1, 2, 0), (1, 2, 2),
        (0, 1, 0), (0, 1, 2),
        (2, 1, 0), (2, 1, 2),
        (0, 0, 1), (0, 2, 1),
        (2, 0, 1), (2, 2, 1),
    ]
    
    # Select the first available cell in priority order
    for i, j, k in priority_order:
        if board[i][j][k] == 0:
            return (i, j, k)
    
    # If no empty cells (should never happen), return dummy move
    return (0, 0, 0)
