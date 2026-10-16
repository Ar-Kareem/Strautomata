
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Build the board state (15x15)
    board = [[0] * 15 for _ in range(15)]
    for r, c in me:
        board[r][c] = 1
    for r, c in opp:
        board[r][c] = 2
    
    # Hex grid neighbor offsets (6 directions)
    dirs = [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (1, 1)]
    
    # Check for immediate winning moves
    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c] or board[r][c] != 0:
                continue
            board[r][c] = 1  # Simulate placing my stone
            
            # Check if this move wins
            if check_win(board, r, c, 1, dirs):
                board[r][c] = 0  # Revert
                return (r, c)
            
            # Check if this move blocks opponent's win
            if check_win(board, r, c, 2, dirs):
                board[r][c] = 0
                return (r, c)
            
            board[r][c] = 0  # Revert
    
    # If no threats, choose move blocking most opponent stones
    best_move = None
    best_block = -1
    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c] or board[r][c] != 0:
                continue
            block_count = 0
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 15 and 0 <= nc < 15 and board[nr][nc] == 2:
                    block_count += 1
            if block_count > best_block:
                best_block = block_count
                best_move = (r, c)
    
    return best_move

def check_win(board, r, c, color, dirs):
    # Check all 6 directions for a winning line
    for dr, dc in dirs:
        count = 1  # Current stone
        # Check in the direction (dr, dc)
        nr, nc = r + dr, c + dc
        while 0 <= nr < 15 and 0 <= nc < 15 and board[nr][nc] == color:
            count += 1
            nr += dr
            nc += dc
        # Check opposite direction
        nr, nc = r - dr, c - dc
        while 0 <= nr < 15 and 0 <= nc < 15 and board[nr][nc] == color:
            count += 1
            nr -= dr
            nc -= dc
        if count >= 5:  # Win condition (5+ stones in a line)
            return True
    return False
