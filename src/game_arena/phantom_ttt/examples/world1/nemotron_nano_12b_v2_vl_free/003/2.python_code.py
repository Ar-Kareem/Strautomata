
def priority(move):
    """Assigns priority to a cell based on its position in the Tic Tac Toe grid."""
    priority_map = [3, 2, 3, 2, 4, 2, 3, 2, 3]  # Priorities for cells 0-8
    return priority_map[move]

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    """
    Returns the next move for Phantom Tic Tac Toe as a tuple (row, col).
    
    - First checks for moves that immediately win the game.
    - Then checks for moves that create a fork (two possible winning lines).
    - Finally selects the highest priority move using the Tic Tac Toe strategy.
    """
    # Step 1: Check for immediate win
    for move in legal_moves:
        row, col = divmod(move, 3)
        # Check row
        row_sum = sum(board[row][c] for c in range(3))
        if row_sum + 1 == 3:
            return (row, col)
        # Check column
        col_sum = sum(board[r][col] for r in range(3))
        if col_sum + 1 == 3:
            return (row, col)
        # Check left diagonal
        if row == col:
            diag_sum = sum(board[i][i] for i in range(3))
            if diag_sum + 1 == 3:
                return (row, col)
        # Check right diagonal
        if row + col == 2:
            diag_sum = board[0][2] + board[1][1] + board[2][0]
            if diag_sum + 1 == 3:
                return (row, col)
    
    # Step 2: Check for fork (two lines that would be completed by this move)
    for move in legal_moves:
        row, col = divmod(move, 3)
        possible_lines = [
            [(row, c) for c in range(3)],  # row
            [(r, col) for r in range(3)],  # column
        ]
        # Add diagonals if applicable
        if row == col:
            possible_lines.append([(0,0), (1,1), (2,2)])
        if row + col == 2:
            possible_lines.append([(0,2), (1,1), (2,0)])
        
        fork_count = 0
        for line in possible_lines:
            line_sum = sum(board[r][c] for r, c in line)
            if line_sum == 2:
                fork_count += 1
        if fork_count >= 2:
            return (row, col)
    
    # Step 3: Prioritize moves based on strategic importance
    # Center first, then corners, then edges
    sorted_moves = sorted(legal_moves, key=lambda x: (-priority(x), x))
    chosen_move = sorted_moves[0]
    row, col = divmod(chosen_move, 3)
    return (row, col)
