
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winning(pr: int, pc: int, player: int) -> bool:
        temp = [list(row) for row in board]
        temp[pr][pc] = player
        # Check row
        if all(cell == player for cell in temp[pr]):
            return True
        # Check column
        if all(temp[i][pc] == player for i in range(3)):
            return True
        # Check main diagonal
        if pr == pc and all(temp[i][i] == player for i in range(3)):
            return True
        # Check anti-diagonal
        if pr + pc == 2 and all(temp[i][2-i] == player for i in range(3)):
            return True
        return False

    # Check for winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0 and is_winning(r, c, 1):
                return (r, c)
    
    # Block opponent's winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0 and is_winning(r, c, -1):
                return (r, c)
    
    # Prioritize strategic moves
    priority = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in priority:
        if board[r][c] == 0:
            return (r, c)
    
    return (0, 0)  # Fallback, shouldn't occur
