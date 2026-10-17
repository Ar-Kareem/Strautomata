
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Plays a move in Tic-Tac-Toe.
    Strategy:
    1. Take the center (1,1) if empty.
    2. Take a corner if empty.
    3. Take an edge if empty.
    """
    # 1. Check if I already have a winning move (or just need to block) - 
    #    Actually, in a solved game, we just need a good heuristic. 
    #    Taking the center is the strongest opening.
    
    # Center
    if board[1][1] == 0:
        return (1, 1)
    
    # Corners: (0,0), (0,2), (2,0), (2,2)
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)
            
    # Edges: (0,1), (1,0), (1,2), (2,1)
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in edges:
        if board[r][c] == 0:
            return (r, c)
            
    # Should never be reached if called on a non-full board, 
    # but included to satisfy the requirement of a legal move.
    return (0, 0)
