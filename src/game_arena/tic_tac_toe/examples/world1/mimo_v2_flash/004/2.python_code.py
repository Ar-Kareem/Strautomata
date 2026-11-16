
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Smart Tic Tac Toe policy implementing a rule-based Minimax heuristic.
    Prioritizes winning, blocking, forking, and strategic positional control.
    """
    
    # Helper to get available moves
    def get_empty_cells(b):
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]

    # Helper to check if a specific player has won
    def check_win(b, player):
        # Check rows
        for r in range(3):
            if b[r][0] == player and b[r][1] == player and b[r][2] == player:
                return True
        # Check cols
        for c in range(3):
            if b[0][c] == player and b[1][c] == player and b[2][c] == player:
                return True
        # Check diagonals
        if b[0][0] == player and b[1][1] == player and b[2][2] == player:
            return True
        if b[0][2] == player and b[1][1] == player and b[2][0] == player:
            return True
        return False

    empty_cells = get_empty_cells(board)

    # 1. Win: If I can win now, do it.
    for r, c in empty_cells:
        board[r][c] = 1
        if check_win(board, 1):
            board[r][c] = 0  # Reset for safety
            return (r, c)
        board[r][c] = 0  # Backtrack

    # 2. Block: If opponent can win, block them.
    for r, c in empty_cells:
        board[r][c] = -1
        if check_win(board, -1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 3. Fork: Create a winning fork.
    # A fork is where I have two lines (row/col/diag) that can become winning 
    # simultaneously on the next turn.
    
    # Count potential winning lines for (r,c) if I play there
    def count_winning_lines(b, r, c, player):
        count = 0
        # Check Row
        if all(b[r][k] == player or (r == r and k == c) for k in range(3)):
             # Ensure it's a potential line (not blocked by opponent)
             if sum(1 for k in range(3) if b[r][k] == -player) == 0:
                count += 1
        # Check Col
        if all(b[k][c] == player or (k == r and c == c) for k in range(3)):
             if sum(1 for k in range(3) if b[k][c] == -player) == 0:
                count += 1
        # Check Diagonal 1
        if r == c:
            if all(b[k][k] == player or k == r for k in range(3)):
                if sum(1 for k in range(3) if b[k][k] == -player) == 0:
                    count += 1
        # Check Diagonal 2
        if r + c == 2:
            if all(b[k][2-k] == player or k == r for k in range(3)):
                if sum(1 for k in range(3) if b[k][2-k] == -player) == 0:
                    count += 1
        return count

    # Check for creating a fork
    # We look for a move that results in 2 open winning lines
    for r, c in empty_cells:
        board[r][c] = 1
        # Simulate opponent response? No, simple fork creation
        # Count how many lines this move creates that are one step from winning
        lines = 0
        # Row
        if sum(1 for k in range(3) if board[r][k] == 1) >= 2: lines += 1
        # Col
        if sum(1 for k in range(3) if board[k][c] == 1) >= 2: lines += 1
        # Diag 1
        if r == c:
            if sum(1 for k in range(3) if board[k][k] == 1) >= 2: lines += 1
        # Diag 2
        if r + c == 2:
            if sum(1 for k in range(3) if board[k][2-k] == 1) >= 2: lines += 1
        
        # If lines >= 2, we have a fork (or close to it)
        if lines >= 2:
             board[r][c] = 0
             return (r, c)
        board[r][c] = 0

    # 4. Center
    if board[1][1] == 0:
        return (1, 1)

    # 5. Opponent Fork: Block opponent's fork
    # Specific case: Opponent has corners, I have center. I must play a side.
    # This usually happens if opponent is in opposite corners.
    corners = [(0,0), (0,2), (2,0), (2,2)]
    sides = [(0,1), (1,0), (1,2), (2,1)]
    
    # Check if we are in the "Center vs Opposite Corners" trap
    if board[1][1] == 1: # I have center
        my_corners = [c for c in corners if board[c[0]][c[1]] == 1]
        opp_corners = [c for c in corners if board[c[0]][c[1]] == -1]
        
        if len(my_corners) == 0 and len(opp_corners) == 2:
            # Opponent has two opposite corners.
            # I must play a side to block a future fork.
            for s in sides:
                if board[s[0]][s[1]] == 0:
                    return s

    # 6. Opposite Corner
    for r, c in corners:
        if board[r][c] == -1: # Opponent in corner
            opp_r, opp_c = 2-r, 2-c
            if board[opp_r][opp_c] == 0:
                return (opp_r, opp_c)

    # 7. Empty Corner
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)

    # 8. Empty Side
    for r, c in sides:
        if board[r][c] == 0:
            return (r, c)

    # Fallback (should not happen in a valid game)
    return empty_cells[0]
