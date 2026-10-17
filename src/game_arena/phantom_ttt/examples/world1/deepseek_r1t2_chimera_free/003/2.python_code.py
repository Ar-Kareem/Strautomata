
def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    # Convert legal moves to (row, col) tuples for easier processing
    empty_cells = [(move // 3, move % 3) for move in legal_moves]
    
    # Identify positions occupied by the current player and the opponent
    my_positions = set()
    opponent_positions = set()
    for row in range(3):
        for col in range(3):
            idx = row * 3 + col
            if board[row][col] == 1:
                my_positions.add((row, col))
            elif idx not in legal_moves:
                opponent_positions.add((row, col))
    
    # Define all possible winning lines (rows, columns, diagonals)
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
    
    # Step 1: Check for any immediate winning move
    for r, c in empty_cells:
        hypothetical_my = my_positions | {(r, c)}
        for line in lines:
            if (r, c) not in line:
                continue
            if all(cell in hypothetical_my for cell in line):
                return (r, c)
    
    # Step 2: Block opponent's potential winning move
    for r, c in empty_cells:
        hypothetical_opponent = opponent_positions | {(r, c)}
        for line in lines:
            if (r, c) not in line:
                continue
            if all(cell in hypothetical_opponent for cell in line):
                return (r, c)
    
    # Step 3: Take the center if available
    if 4 in legal_moves:
        return (1, 1)
    
    # Step 4: Prioritize taking a corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        idx = corner[0] * 3 + corner[1]
        if idx in legal_moves:
            return corner
    
    # Step 5: Take any available edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for edge in edges:
        idx = edge[0] * 3 + edge[1]
        if idx in legal_moves:
            return edge
    
    # Fallback: return first available move (guaranteed by legal_moves)
    return empty_cells[0]
