
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper function to check if placing a player's mark at (row, col) results in a win
    def is_win(player: int, row: int, col: int) -> bool:
        if board[row][col] != 0:
            return False
        
        # Check row
        row_counts = sum(1 for j in range(4) if board[row][j] == player)
        if row_counts == 3:
            return True
        
        # Check column
        col_counts = sum(1 for i in range(4) if board[i][col] == player)
        if col_counts == 3:
            return True
        
        # Check main diagonal (top-left to bottom-right)
        if row == col:
            diag_counts = sum(1 for i in range(4) if board[i][i] == player)
            if diag_counts == 3:
                return True
        
        # Check anti-diagonal (top-right to bottom-left)
        if row + col == 3:
            anti_diag_counts = sum(1 for i in range(4) if board[i][3-i] == player)
            if anti_diag_counts == 3:
                return True
        
        return False

    # Collect all empty cells
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))

    # 1. Check for a winning move
    for i, j in empty_cells:
        if is_win(1, i, j):
            return (i, j)
    
    # 2. Block opponent's winning move
    block_moves = []
    for i, j in empty_cells:
        if is_win(-1, i, j):
            block_moves.append((i, j))
    if block_moves:
        return block_moves[0]
    
    # 3. Prioritize center cells
    center = [(1,1), (1,2), (2,1), (2,2)]
    for cell in center:
        if cell in empty_cells:
            return cell
    
    # 4. Take corners
    corners = [(0,0), (0,3), (3,0), (3,3)]
    for cell in corners:
        if cell in empty_cells:
            return cell
    
    # 5. Take edges
    edges = [(0,1), (0,2), (1,0), (1,3), (2,0), (2,3), (3,1), (3,2)]
    for cell in edges:
        if cell in empty_cells:
            return cell
    
    # 6. Fallback to the first available cell
    return empty_cells[0]
