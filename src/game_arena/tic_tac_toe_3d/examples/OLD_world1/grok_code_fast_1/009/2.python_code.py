
def is_win(board, player):
    # Define all winning lines: each is a list of (z, y, x) tuples
    lines = []
    
    # Straight lines along z-axis (fixed x, y)
    for x in range(3):
        for y in range(3):
            lines.append([(z, y, x) for z in range(3)])
    
    # Straight lines along y-axis (fixed z, x)
    for z in range(3):
        for x in range(3):
            lines.append([(z, y, x) for y in range(3)])
    
    # Straight lines along x-axis (fixed z, y)
    for z in range(3):
        for y in range(3):
            lines.append([(z, y, x) for x in range(3)])
    
    # Diagonals in xy planes (fixed z)
    for z in range(3):
        lines.append([(z, i, i) for i in range(3)])      # x inc, y inc
        lines.append([(z, i, 2 - i) for i in range(3)])  # x inc, y dec
    
    # Diagonals in xz planes (fixed y)
    for y in range(3):
        lines.append([(i, y, i) for i in range(3)])      # z inc, x inc
        lines.append([(i, y, 2 - i) for i in range(3)])  # z inc, x dec
    
    # Diagonals in zy planes (fixed x)
    for x in range(3):
        lines.append([(i, i, x) for i in range(3)])      # z inc, y inc
        lines.append([(i, 2 - i, x) for i in range(3)])  # z inc, y dec
    
    # Space diagonals
    lines.append([(i, i, i) for i in range(3)])          # (0,0,0) to (2,2,2)
    lines.append([(i, i, 2 - i) for i in range(3)])      # (0,0,2) to (2,2,0)
    lines.append([(i, 2 - i, i) for i in range(3)])      # (0,2,0) to (2,0,2)
    lines.append([(i, 2 - i, 2 - i) for i in range(3)])  # (0,2,2) to (2,0,0)
    
    # Check if any line is fully occupied by the player
    for line in lines:
        if all(board[z][y][x] == player for z, y, x in line):
            return True
    return False

def can_force_win(board, player):
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    board[z][y][x] = player
                    if is_win(board, player):
                        board[z][y][x] = 0
                        return (x, y, z)
                    board[z][y][x] = 0
    return None

def get_first_empty(board):
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    return (x, y, z)
    return None  # Should not happen in a valid game

def policy(board):
    # Try to win immediately
    win_move = can_force_win(board, 1)
    if win_move is not None:
        return win_move
    
    # Try to block opponent's win
    block_move = can_force_win(board, -1)
    if block_move is not None:
        return block_move
    
    # Otherwise, take the first empty cell
    return get_first_empty(board)
