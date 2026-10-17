
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(b: list[list[int]], player: int) -> bool:
        # Check rows, columns, and diagonals for a win
        for i in range(3):
            if all(b[i][j] == player for j in range(3)) or all(b[j][i] == player for j in range(3)):
                return True
        if all(b[i][i] == player for i in range(3)) or all(b[i][2 - i] == player for i in range(3)):
            return True
        return False

    def get_available_moves(b: list[list[int]]) -> list[tuple[int, int]]:
        return [(i, j) for i in range(3) for j in range(3) if b[i][j] == 0]

    # Check for immediate win
    for i, j in get_available_moves(board):
        board[i][j] = 1  # Try the move
        if check_win(board, 1):
            return (i, j)  # Return winning move
        board[i][j] = 0  # Undo move

    # Check for blocking opponent's win
    for i, j in get_available_moves(board):
        board[i][j] = -1  # Try the opponent's move
        if check_win(board, -1):
            board[i][j] = 0  # Undo move
            return (i, j)  # Return blocking move
        board[i][j] = 0  # Undo move

    # Center move
    if board[1][1] == 0:
        return (1, 1)

    # Corner moves
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)

    # Last option: choose any available space
    available_moves = get_available_moves(board)
    if available_moves:
        return available_moves[0]  # Return first available position

    # Just in case there are no available moves, although shouldn't happen
    return (-1, -1)
