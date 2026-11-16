
def policy(me, opp, color):
    board_size = 11
    board = [[None for _ in range(board_size)] for _ in range(board_size)]
    
    # Place stones on the board
    for r, c in me:
        board[r][c] = color
    for r, c in opp:
        board[r][c] = 'w' if color == 'b' else 'b'
    
    # Directions for neighbors (excluding (i-1,j-1) and (i+1,j+1))
    directions = [(-1, 0), (0, -1), (0, 1), (1, 0), (1, -1), (-1, 1)]
    
    def is_winning_move(row, col, player_color):
        # Check if the color reaches its end
        if player_color == 'b': 
            end_row = board_size - 1
            target_row = row
            target_col = col
            visited = set()
            return dfs_check(target_row, target_col, player_color, visited, end_row)
        else:  
            end_col = board_size - 1
            target_row = row
            target_col = col
            visited = set()
            return dfs_check(target_row, target_col, player_color, visited, end_col, axis='col')

    def dfs_check(r, c, color, visited, end, axis='row'):
        if (axis == 'row' and r == end) or (axis == 'col' and c == end):
            return True
        visited.add((r, c))
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size:
                if board[nr][nc] == color and (nr, nc) not in visited:
                    if dfs_check(nr, nc, color, visited, end, axis):
                        return True
        
        return False
    
    # Evaluate moves
    best_move = None
    for r in range(board_size):
        for c in range(board_size):
            if board[r][c] is None:  # It's an empty space
                # Check if this is a winning move
                if is_winning_move(r, c, color):
                    return (r, c)  # Immediate win
                # Make a temporary move
                board[r][c] = color
                # Check for opponent win
                if is_winning_move(r, c, 'w' if color == 'b' else 'b'):
                    best_move = (r, c)  # Block opponent
                board[r][c] = None  # Undo move

    # If a blocking move was found that prevents opponent from winning, take it
    if best_move:
        return best_move

    # If no immediate threats or blocks, return a random legal move
    for r in range(board_size):
        for c in range(board_size):
            if board[r][c] is None:
                return (r, c)

    # Fallback (should not reach here in a valid game)
    return (0, 0)
