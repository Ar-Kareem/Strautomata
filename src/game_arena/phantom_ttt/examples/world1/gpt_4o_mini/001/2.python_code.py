
def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    def check_win_condition(positions):
        values = [board[pos // 3][pos % 3] for pos in positions]
        if values.count(1) == 2 and values.count(0) == 1:
            return positions[values.index(0)]  # Return the index of the empty cell
        return None
    
    # Winning combinations: (row, column, diagonal)
    win_conditions = [
        (0, 1, 2),  # First row
        (3, 4, 5),  # Second row
        (6, 7, 8),  # Third row
        (0, 3, 6),  # First column
        (1, 4, 7),  # Second column
        (2, 5, 8),  # Third column
        (0, 4, 8),  # Main diagonal
        (2, 4, 6)   # Anti diagonal
    ]
    
    # First, check for winning moves
    for condition in win_conditions:
        move = check_win_condition(condition)
        if move is not None and move in legal_moves:
            return move
    
    # Secondly, check for blocking moves
    def check_block_condition(positions):
        values = [board[pos // 3][pos % 3] for pos in positions]
        if values.count(0) == 1 and values.count(1) == 0:
            return positions[values.index(0)]  # Return the index of the empty cell
        return None
    
    for condition in win_conditions:
        move = check_block_condition(condition)
        if move is not None and move in legal_moves:
            return move
    
    # No win or block available, pick a random legal move not confirmed
    for move in legal_moves:
        if board[move // 3][move % 3] == 0:  # Prefer moves that are still open
            return move
    
    # Fallback: Just return the first legal move if no better option is found
    return legal_moves[0]
