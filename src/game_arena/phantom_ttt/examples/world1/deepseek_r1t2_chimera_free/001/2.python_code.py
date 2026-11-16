
def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    # Define all possible winning lines (rows, columns, diagonals)
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
    
    # Check for immediate winning moves
    for line in lines:
        our_count = 0
        empty_pos = None
        for (r, c) in line:
            if board[r][c] == 1:
                our_count += 1
            else:
                move_idx = r * 3 + c
                if move_idx in legal_moves:
                    empty_pos = (r, c)
        if our_count == 2 and empty_pos is not None:
            return empty_pos

    # Prioritize center (index 4)
    if 4 in legal_moves:
        return (1, 1)
    
    # Next, try corners in fixed order (indices 0, 2, 6, 8)
    corners = [0, 2, 6, 8]
    for idx in corners:
        if idx in legal_moves:
            return (idx // 3, idx % 3)
    
    # Finally, edges in fixed order (indices 1, 3, 5, 7)
    edges = [1, 3, 5, 7]
    for idx in edges:
        if idx in legal_moves:
            return (idx // 3, idx % 3)
    
    # Fallback (should not occur as legal_moves is non-empty)
    idx = legal_moves[0]
    return (idx // 3, idx % 3)
