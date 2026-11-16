
def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Check for a winning move
    for move in legal_moves:
        r, c = move // 3, move % 3
        # Check row
        if sum(board[r]) == 2:
            return (r, c)
        # Check column
        if sum(row[c] for row in board) == 2:
            return (r, c)
        # Check main diagonal
        if r == c and sum(board[i][i] for i in range(3)) == 2:
            return (r, c)
        # Check anti-diagonal
        if r + c == 2 and sum(board[i][2-i] for i in range(3)) == 2:
            return (r, c)
    
    # Prioritize center if available
    if 4 in legal_moves:
        return (1, 1)
    
    # Choose corners in order: top-left, top-right, bottom-left, bottom-right
    corners = [0, 2, 6, 8]
    for corner in corners:
        if corner in legal_moves:
            r, c = corner // 3, corner % 3
            return (r, c)
    
    # Choose edges if no better option
    edges = [1, 3, 5, 7]
    for edge in edges:
        if edge in legal_moves:
            r, c = edge // 3, edge % 3
            return (r, c)
    
    # Default to first legal move (shouldn't reach here due to legal_moves constraint)
    move = legal_moves[0]
    return (move // 3, move % 3)
