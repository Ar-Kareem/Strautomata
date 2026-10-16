
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def is_winning_move(x, y, z, player):
        original = board[x][y][z]
        board[x][y][z] = player
        win = False
        # Check along x-axis
        if all(board[i][y][z] == player for i in range(3)):
            win = True
        # Check along y-axis
        elif all(board[x][i][z] == player for i in range(3)):
            win = True
        # Check along z-axis
        elif all(board[x][y][i] == player for i in range(3)):
            win = True
        else:
            # Check face diagonals in xy plane
            if x == y:
                if all(board[i][i][z] == player for i in range(3)):
                    win = True
            if not win and x + y == 2:
                if all(board[i][2 - i][z] == player for i in range(3)):
                    win = True
            # Check face diagonals in xz plane
            if not win and x == z:
                if all(board[i][y][i] == player for i in range(3)):
                    win = True
            if not win and x + z == 2:
                if all(board[i][y][2 - i] == player for i in range(3)):
                    win = True
            # Check face diagonals in yz plane
            if not win and y == z:
                if all(board[x][i][i] == player for i in range(3)):
                    win = True
            if not win and y + z == 2:
                if all(board[x][i][2 - i] == player for i in range(3)):
                    win = True
            # Check space diagonals
            if not win:
                # Check main space diagonal (x=y=z)
                if x == y and y == z:
                    if all(board[i][i][i] == player for i in range(3)):
                        win = True
                # Check other space diagonals
                if not win and x == y and x + z == 2:
                    if all(board[i][i][2 - i] == player for i in range(3)):
                        win = True
                if not win and x == z and x + y == 2:
                    if all(board[i][2 - i][i] == player for i in range(3)):
                        win = True
                if not win and y == z and x + y == 2:
                    if all(board[2 - i][i][i] == player for i in range(3)):
                        win = True
        board[x][y][z] = original
        return win

    # Find all empty cells
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_cells.append( (x, y, z) )
    
    # Prioritize winning moves
    for cell in empty_cells:
        x, y, z = cell
        if is_winning_move(x, y, z, 1):
            return cell
    
    # Block opponent's winning moves
    for cell in empty_cells:
        x, y, z = cell
        if is_winning_move(x, y, z, -1):
            return cell
    
    # Choose center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Choose a corner if available
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for corner in corners:
        x, y, z = corner
        if board[x][y][z] == 0:
            return corner
    
    # Fallback: choose first available edge
    return empty_cells[0]
