
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winning_move(r: int, c: int, player: int) -> bool:
        # Simulate the move on a copy of the board
        new_board = [row.copy() for row in board]
        new_board[r][c] = player

        # Check row
        if all(cell == player for cell in new_board[r]):
            return True
        # Check column
        if all(new_board[i][c] == player for i in range(3)):
            return True
        # Check main diagonal
        if r == c and all(new_board[i][i] == player for i in range(3)):
            return True
        # Check anti-diagonal
        if r + c == 2 and all(new_board[i][2 - i] == player for i in range(3)):
            return True
        return False

    # Check for immediate winning move
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                if is_winning_move(row, col, 1):
                    return (row, col)
    
    # Check for opponent's winning move to block
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                if is_winning_move(row, col, -1):
                    return (row, col)
    
    # Priority-based heuristic strategy
    priority_order = [(1, 1),  # Center
                      (0, 0), (0, 2), (2, 0), (2, 2),  # Corners
                      (0, 1), (1, 0), (1, 2), (2, 1)]  # Edges
    
    for row, col in priority_order:
        if board[row][col] == 0:
            return (row, col)
    
    # Fallback (should never reach here if board is valid)
    raise RuntimeError("No valid move found")
