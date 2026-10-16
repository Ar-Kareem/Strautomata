
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to check for wins easily
    def check_win(state, player):
        # Check rows
        for i in range(3):
            if all(state[i][j] == player for j in range(3)):
                return True
        
        # Check columns
        for j in range(3):
            if all(state[i][j] == player for i in range(3)):
                return True
        
        # Check diagonals
        if all(state[i][i] == player for i in range(3)):
            return True
        if all(state[i][2-i] == player for i in range(3)):
            return True
            
        return False
    
    # Find all empty positions
    empty_positions = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                empty_positions.append((i, j))
    
    # If no empty positions, return first position (shouldn't happen)
    if not empty_positions:
        return (0, 0)
    
    # Try to win immediately
    for pos in empty_positions:
        i, j = pos
        # Create a copy of the board
        test_board = [row[:] for row in board]
        test_board[i][j] = 1  # Place our mark
        if check_win(test_board, 1):
            return pos
    
    # Block opponent from winning
    for pos in empty_positions:
        i, j = pos
        # Create a copy of the board
        test_board = [row[:] for row in board]
        test_board[i][j] = -1  # Place opponent's mark
        if check_win(test_board, -1):
            return pos
    
    # If no immediate win or block, use strategic positioning
    # Center is preferred
    if (1, 1) in empty_positions:
        return (1, 1)
    
    # Corners are preferred next
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if corner in empty_positions:
            return corner
    
    # Edges as last resort
    return empty_positions[0]
