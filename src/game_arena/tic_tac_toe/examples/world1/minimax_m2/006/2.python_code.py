
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define all winning lines: rows, columns, and diagonals
    winning_lines = [
        [(0, 0), (0, 1), (0, 2)],  # Row 0
        [(1, 0), (1, 1), (1, 2)],  # Row 1
        [(2, 0), (2, 1), (2, 2)],  # Row 2
        [(0, 0), (1, 0), (2, 0)],  # Column 0
        [(0, 1), (1, 1), (2, 1)],  # Column 1
        [(0, 2), (1, 2), (2, 2)],  # Column 2
        [(0, 0), (1, 1), (2, 2)],  # Main diagonal
        [(0, 2), (1, 1), (2, 0)]   # Anti-diagonal
    ]
    
    # First, check for a winning move
    for line in winning_lines:
        values = [board[i][j] for i, j in line]
        if sum(values) == 2:  # I have two pieces and one empty
            for cell in line:
                if board[cell[0]][cell[1]] == 0:
                    return cell  # Return the winning move
    
    # If no winning move, check for a blocking move
    for line in winning_lines:
        values = [board[i][j] for i, j in line]
        if sum(values) == -2:  # Opponent has two pieces and one empty
            for cell in line:
                if board[cell[0]][cell[1]] == 0:
                    return cell  # Return the blocking move
    
    # If no win or block, take the center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Otherwise, take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for cell in corners:
        if board[cell[0]][cell[1]] == 0:
            return cell
    
    # Finally, take a side if available
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for cell in sides:
        if board[cell[0]][cell[1]] == 0:
            return cell
    
    # Fallback: should not happen if board is not full
    return (0, 0)
