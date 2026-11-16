
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define the winning lines for a 4x4 board
    lines = [
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
    
    def check_win(board, player):
        """Check if the player has a winning line on the board."""
        for line in lines:
            win = True
            for i, j in line:
                if board[i][j] != player:
                    win = False
                    break
            if win:
                return True
        return False
    
    def evaluate_board(board):
        """Evaluate the board and return a score."""
        score = 0
        for line in lines:
            count_1 = 0
            count_minus1 = 0
            for i, j in line:
                if board[i][j] == 1:
                    count_1 += 1
                elif board[i][j] == -1:
                    count_minus1 += 1
            if count_1 > 0 and count_minus1 > 0:
                score += 0  # Line is blocked
            elif count_1 > 0:
                score += 10 ** count_1
            elif count_minus1 > 0:
                score -= 10 ** count_minus1
        return score
    
    # Get all empty cells
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))
    
    # Check for immediate win
    for i, j in empty_cells:
        board_copy = [row[:] for row in board]
        board_copy[i][j] = 1
        if check_win(board_copy, 1):
            return (i, j)
    
    # Check for critical cells to block opponent
    critical_cells = set()
    for line in lines:
        count_1 = 0
        count_minus1 = 0
        empty_cell = None
        for i, j in line:
            val = board[i][j]
            if val == 1:
                count_1 += 1
            elif val == -1:
                count_minus1 += 1
            elif val == 0:
                empty_cell = (i, j)
        if count_minus1 == 3 and count_1 == 0 and empty_cell is not None:
            critical_cells.add(empty_cell)
    
    if critical_cells:
        # Choose the first critical cell found
        critical_list = list(critical_cells)
        return critical_list[0]
    
    # Use heuristic to choose the best move
    best_score = -float('inf')
    best_move = None
    for i, j in empty_cells:
        board_copy = [row[:] for row in board]
        board_copy[i][j] = 1
        score = evaluate_board(board_copy)
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
