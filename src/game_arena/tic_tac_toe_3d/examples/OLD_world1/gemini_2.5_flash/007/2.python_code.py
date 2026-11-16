
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    n = len(board)
    board_np = np.array(board)

    # 1. Check for a winning move
    # Iterate through all possible lines (rows, columns, depths, diagonals)
    # and see if placing our piece completes a line.
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_np[x, y, z] == 0:
                    # Temporarily place our piece
                    board_np[x, y, z] = 1
                    if check_win(board_np, 1):
                        return (x, y, z)
                    board_np[x, y, z] = 0  # Revert the move

    # 2. Block an opponent's winning move
    # Similar to above, but check if the opponent would win.
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_np[x, y, z] == 0:
                    # Temporarily place opponent's piece
                    board_np[x, y, z] = -1
                    if check_win(board_np, -1):
                        return (x, y, z)
                    board_np[x, y, z] = 0  # Revert the move

    # 3. Prioritize center cells (if applicable, for odd n)
    if n % 2 == 1:
        center = n // 2
        if board_np[center, center, center] == 0:
            return (center, center, center)

    # 4. Check for creating a "fork" (multiple winning lines)
    # This is more complex. For simplicity, we'll implement a basic version.
    # Count potential winning lines for our piece if we place it.
    best_fork_move = None
    max_forks = 0
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_np[x, y, z] == 0:
                    board_np[x, y, z] = 1
                    current_forks = count_winning_lines(board_np, 1)
                    if current_forks > max_forks:
                        max_forks = current_forks
                        best_fork_move = (x, y, z)
                    board_np[x, y, z] = 0

    if best_fork_move is not None:
        return best_fork_move

    # 5. Take any empty corner (prioritize corner cells if not covered by previous steps)
    corners = [(0, 0, 0), (0, 0, n-1), (0, n-1, 0), (0, n-1, n-1),
               (n-1, 0, 0), (n-1, 0, n-1), (n-1, n-1, 0), (n-1, n-1, n-1)]
    for x, y, z in corners:
        if 0 <= x < n and 0 <= y < n and 0 <= z < n and board_np[x, y, z] == 0:
            return (x, y, z)

    # 6. Take any empty edge cell
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_np[x, y, z] == 0:
                    is_corner = (x in (0, n-1) and y in (0, n-1) and z in (0, n-1))
                    is_center = (n % 2 == 1 and x == n // 2 and y == n // 2 and z == n // 2)
                    if not is_corner and not is_center and board_np[x,y,z] == 0:
                        return (x, y, z)

    # 7. Take any available empty cell (fallback)
    # This should cover all remaining empty cells.
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_np[x, y, z] == 0:
                    return (x, y, z)

    # If no empty cells, this should not be reached in a valid game.
    raise Exception("No valid moves left on the board.")

def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won the game on the current board.
    Assumes n is the size of the board (e.g., 3 for 3x3x3).
    """
    n = board.shape[0]

    # Check all possible lines (rows, columns, depths, and various diagonals)

    # 1. 3D Rows (varying x)
    for y in range(n):
        for z in range(n):
            if np.all(board[:, y, z] == player):
                return True

    # 2. 3D Columns (varying y)
    for x in range(n):
        for z in range(n):
            if np.all(board[x, :, z] == player):
                return True

    # 3. 3D Depths (varying z)
    for x in range(n):
        for y in range(n):
            if np.all(board[x, y, :] == player):
                return True

    # 4. Face Diagonals (2D diagonals on each of the 6 faces)
    # XY-planes (z fixed)
    for z in range(n):
        if np.all(board.diagonal(axis1=0, axis2=1, offset=0)[:, z] == player): # Main diagonal
            return True
        if np.all(np.fliplr(board[:, :, z]).diagonal(axis1=0, axis2=1, offset=0) == player): # Anti-diagonal
            return True

    # XZ-planes (y fixed)
    for y in range(n):
        if np.all(board.diagonal(axis1=0, axis2=2, offset=0)[:, y] == player): # Main diagonal
            return True
        if np.all(np.fliplr(board[:, y, :]).diagonal(axis1=0, axis2=1, offset=0) == player): # Anti-diagonal
            return True

    # YZ-planes (x fixed)
    for x in range(n):
        if np.all(board.diagonal(axis1=1, axis2=2, offset=0)[x, :] == player): # Main diagonal
            return True
        if np.all(np.fliplr(board[x, :, :]).diagonal(axis1=0, axis2=1, offset=0) == player): # Anti-diagonal
            return True

    # 5. Space Diagonals (4 main 3D diagonals)
    # Main space diagonal (0,0,0) to (n-1,n-1,n-1)
    if np.all([board[i, i, i] == player for i in range(n)]):
        return True
    # (0,0,n-1) to (n-1,n-1,0)
    if np.all([board[i, i, n - 1 - i] == player for i in range(n)]):
        return True
    # (0,n-1,0) to (n-1,0,n-1)
    if np.all([board[i, n - 1 - i, i] == player for i in range(n)]):
        return True
    # (n-1,0,0) to (0,n-1,n-1)
    if np.all([board[n - 1 - i, i, i] == player for i in range(n)]):
        return True

    return False

def count_winning_lines(board: np.ndarray, player: int) -> int:
    """
    Counts how many potential winning lines a player has on the board.
    A potential winning line is one where player has N-1 pieces and 1 empty cell.
    """
    n = board.shape[0]
    potential_wins = 0

    # Define all possible lines as coordinates. This makes it easier to iterate.

    # Lines along X, Y, Z axes
    lines = []
    # X-axis lines (varying x)
    for y in range(n):
        for z in range(n):
            lines.append([(x, y, z) for x in range(n)])
    # Y-axis lines (varying y)
    for x in range(n):
        for z in range(n):
            lines.append([(x, y, z) for y in range(n)])
    # Z-axis lines (varying z)
    for x in range(n):
        for y in range(n):
            lines.append([(x, y, z) for z in range(n)])

    # Face diagonals
    # XY diagonals (fixed z)
    for z in range(n):
        lines.append([(i, i, z) for i in range(n)]) # Main diagonal
        lines.append([(i, n - 1 - i, z) for i in range(n)]) # Anti-diagonal
    # XZ diagonals (fixed y)
    for y in range(n):
        lines.append([(i, y, i) for i in range(n)]) # Main diagonal
        lines.append([(i, y, n - 1 - i) for i in range(n)]) # Anti-diagonal
    # YZ diagonals (fixed x)
    for x in range(n):
        lines.append([(x, i, i) for i in range(n)]) # Main diagonal
        lines.append([(x, i, n - 1 - i) for i in range(n)]) # Anti-diagonal

    # Space diagonals
    lines.append([(i, i, i) for i in range(n)])
    lines.append([(i, i, n - 1 - i) for i in range(n)])
    lines.append([(i, n - 1 - i, i) for i in range(n)])
    lines.append([(n - 1 - i, i, i) for i in range(n)])

    for line_coords in lines:
        player_count = 0
        empty_count = 0
        opponent_count = 0

        for x, y, z in line_coords:
            if board[x, y, z] == player:
                player_count += 1
            elif board[x, y, z] == 0:
                empty_count += 1
            else:
                opponent_count += 1

        # A potential winning line for 'player' requires:
        # - (n-1) of 'player's pieces
        # - 1 empty cell
        # - 0 of opponent's pieces
        if player_count == n - 1 and empty_count == 1 and opponent_count == 0:
            potential_wins += 1

    return potential_wins
