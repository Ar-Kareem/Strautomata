
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper function to check if placing 'player' at (r,c) would win
    def is_winning_move(r, c, player):
        # Check row
        if sum(1 for cell in board[r] if cell == player) == 3:
            return True
        # Check column
        if sum(1 for i in range(4) if board[i][c] == player) == 3:
            return True
        # Check main diagonal (r == c)
        if r == c and sum(board[i][i] == player for i in range(4)) == 3:
            return True
        # Check anti-diagonal (r + c == 3)
        if r + c == 3 and sum(board[i][3-i] == player for i in range(4)) == 3:
            return True
        return False

    # Step 1: Check for a winning move for the AI (player 1)
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0 and is_winning_move(r, c, 1):
                return (r, c)

    # Step 2: Check for opponent's winning move and block
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0 and is_winning_move(r, c, -1):
                return (r, c)

    # Step 3: Choose the best available position based on priority
    # Priority order: center, corners, edges
    preferred_order = [
        (1,1), (1,2), (2,1), (2,2),
        (0,0), (0,3), (3,0), (3,3),
        (0,1), (0,2), (1,0), (1,3),
        (2,0), (2,3), (3,1), (3,2)
    ]
    for r, c in preferred_order:
        if board[r][c] == 0:
            return (r, c)

    # Fallback in case no empty cell found (should not happen)
    return (0, 0)
