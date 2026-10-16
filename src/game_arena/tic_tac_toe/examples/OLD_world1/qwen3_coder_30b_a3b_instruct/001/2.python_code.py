
def policy(board: list[list[int]]) -> int:
    import numpy as np
    
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Flatten the board to 1D array for easier indexing
    flat_board = board_np.flatten()
    
    # Find all empty cells (0)
    empty_cells = np.where(flat_board == 0)[0]
    
    # If no empty cells, return None (though this shouldn't happen in valid game)
    if len(empty_cells) == 0:
        return None
    
    # Check for winning moves first
    for cell in empty_cells:
        # Create a copy of the board
        test_board = flat_board.copy()
        test_board[cell] = 1  # Try placing our mark
        
        # Check if this creates a winning line
        test_board_reshaped = test_board.reshape(3, 3)
        
        # Check rows
        for row in test_board_reshaped:
            if np.sum(row) == 3:
                return cell + 1  # Return 1-based index
        
        # Check columns
        for col in test_board_reshaped.T:
            if np.sum(col) == 3:
                return cell + 1  # Return 1-based index
        
        # Check diagonals
        if np.sum(np.diag(test_board_reshaped)) == 3:
            return cell + 1
        if np.sum(np.diag(np.fliplr(test_board_reshaped))) == 3:
            return cell + 1
    
    # If no winning move, check for blocking opponent's win
    for cell in empty_cells:
        # Create a copy of the board
        test_board = flat_board.copy()
        test_board[cell] = -1  # Try placing opponent's mark
        
        # Check if this creates a winning line for opponent
        test_board_reshaped = test_board.reshape(3, 3)
        
        # Check rows
        for row in test_board_reshaped:
            if np.sum(row) == -3:
                return cell + 1  # Return 1-based index
        
        # Check columns
        for col in test_board_reshaped.T:
            if np.sum(col) == -3:
                return cell + 1  # Return 1-based index
        
        # Check diagonals
        if np.sum(np.diag(test_board_reshaped)) == -3:
            return cell + 1
        if np.sum(np.diag(np.fliplr(test_board_reshaped))) == -3:
            return cell + 1
    
    # If no immediate threat or win, prioritize center, then corners, then edges
    # Center is position 4 (1-based) = index 4
    if 4 in empty_cells:
        return 5
    
    # Corners are positions 1, 3, 7, 9 (indices 0, 2, 6, 8)
    corners = [0, 2, 6, 8]
    empty_corners = [c for c in corners if c in empty_cells]
    if empty_corners:
        return empty_corners[0] + 1
    
    # If no corners available, return any empty cell
    return empty_cells[0] + 1
