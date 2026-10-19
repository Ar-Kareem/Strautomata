
def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # All possible winning lines (rows, columns, diagonals)
    lines = [
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)]
    ]
    
    # Check for a winning move
    for line in lines:
        my_count = 0
        empty_pos = None
        for (r, c) in line:
            if board[r][c] == 1:
                my_count += 1
            else:
                if (r * 3 + c) in legal_moves:
                    empty_pos = (r, c)
        if my_count == 2 and empty_pos is not None:
            return empty_pos
    
    # Prioritize the center if available
    center_move = 1 * 3 + 1
    if center_move in legal_moves:
        return (1, 1)
    
    # Check corners in order
    corners = [0, 2, 6, 8]
    for move in corners:
        if move in legal_moves:
            return (move // 3, move % 3)
    
    # Check edges
    edges = [1, 3, 5, 7]
    for move in edges:
        if move in legal_moves:
            return (move // 3, move % 3)
    
    # Fallback to the first legal move (should never be reached if legal_moves is non-empty)
    move = legal_moves[0]
    return (move // 3, move % 3)
