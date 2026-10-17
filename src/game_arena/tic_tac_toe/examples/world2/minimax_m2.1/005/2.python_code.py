
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define all winning lines for 4x4 Tic Tac Toe
    winning_lines = [
        # Rows
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(3, 0), (3, 1), (3, 2), (3, 3)],
        # Columns
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(0, 3), (1, 3), (2, 3), (3, 3)],
        # Diagonals
        [(0, 0), (1, 1), (2, 2), (3, 3)],
        [(0, 3), (1, 2), (2, 1), (3, 0)]
    ]
    
    # Find all empty cells
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))
    
    # If no empty cells, return first cell (though game should be over)
    if not empty_cells:
        return (0, 0)
    
    # Check for winning move for me
    for (i, j) in empty_cells:
        # Simulate placing my piece
        board[i][j] = 1
        # Check if any winning line is completed
        won = False
        for line in winning_lines:
            if all(board[x][y] == 1 for (x, y) in line):
                won = True
                break
        board[i][j] = 0  # Undo the placement
        if won:
            return (i, j)
    
    # Check for blocking move to prevent opponent win
    for (i, j) in empty_cells:
        # Check if opponent would win by placing here
        would_win = False
        for line in winning_lines:
            # Check if all other cells in the line are opponent's pieces
            other_cells = [cell for cell in line if cell != (i, j)]
            if all(board[x][y] == -1 for (x, y) in other_cells):
                would_win = True
                break
        if would_win:
            return (i, j)
    
    # If no immediate wins or blocks, choose move with highest score
    best_move = None
    best_score = -float('inf')
    for (i, j) in empty_cells:
        # Simulate placing my piece
        board[i][j] = 1
        score = 0
        for line in winning_lines:
            # Check if there is any opponent piece in the line
            has_opponent = False
            num_my_pieces = 0
            for (x, y) in line:
                if board[x][y] == -1:
                    has_opponent = True
                    break
                elif board[x][y] == 1:
                    num_my_pieces += 1
            if not has_opponent:
                score += 3 ** num_my_pieces
        board[i][j] = 0  # Undo the placement
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
