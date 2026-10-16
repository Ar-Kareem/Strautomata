
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Define all possible lines (rows, cols, diagonals) of length 4
    lines = []
    
    # Rows
    for i in range(4):
        lines.append(board[i, :])
    
    # Columns
    for j in range(4):
        lines.append(board[:, j])
    
    # Diagonals
    lines.append(np.array([board[i, i] for i in range(4)]))  # Main diagonal
    lines.append(np.array([board[i, 3-i] for i in range(4)]))  # Anti-diagonal
    
    # Check for immediate win
    for i, line in enumerate(lines):
        if np.sum(line) == 3:  # Three 1's and one 0, so I can win
            # Find the empty position in this line
            empty_idx = np.where(line == 0)[0][0]
            if i < 4:  # It's a row
                return (i, empty_idx)
            elif i < 8:  # It's a column
                return (empty_idx, i - 4)
            elif i == 8:  # Main diagonal
                return (empty_idx, empty_idx)
            else:  # Anti-diagonal
                return (empty_idx, 3 - empty_idx)
    
    # Check for opponent win (block)
    for i, line in enumerate(lines):
        if np.sum(line) == -3:  # Three -1's and one 0
            empty_idx = np.where(line == 0)[0][0]
            if i < 4:  # Row
                return (i, empty_idx)
            elif i < 8:  # Column
                return (empty_idx, i - 4)
            elif i == 8:  # Main diagonal
                return (empty_idx, empty_idx)
            else:  # Anti-diagonal
                return (empty_idx, 3 - empty_idx)
    
    # No immediate win or block. Choose a strategic move.
    # Priority: center (positions (1,1), (1,2), (2,1), (2,2)) > corners > edges
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    corner_positions = [(0,0), (0,3), (3,0), (3,3)]
    edge_positions = [(0,1), (0,2), (1,0), (1,3), (2,0), (2,3), (3,1), (3,2)]
    
    # Find all empty cells
    empty_cells = []
    for r in range(4):
        for c in range(4):
            if board[r, c] == 0:
                empty_cells.append((r, c))
    
    # Try center first
    for pos in center_positions:
        if pos in empty_cells:
            return pos
    
    # Then corners
    for pos in corner_positions:
        if pos in empty_cells:
            return pos
    
    # Then any edge
    for pos in edge_positions:
        if pos in empty_cells:
            return pos
    
    # Fallback: any empty cell (should not happen if board has empty spots, but return first)
    if empty_cells:
        return empty_cells[0]
    
    # Should not reach here in a valid game, but return (0,0) as fallback
    return (0, 0)
