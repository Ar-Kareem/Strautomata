
def check_win(board: list[list[int]], player: int) -> bool:
    # Check horizontal, vertical and diagonal for winning
    for row in range(6):
        for col in range(7):
            if col + 3 < 7 and all(board[row][col + i] == player for i in range(4)):  # horizontal
                return True
            if row + 3 < 6 and all(board[row + i][col] == player for i in range(4)):  # vertical
                return True
            if row + 3 < 6 and col + 3 < 7 and all(board[row + i][col + i] == player for i in range(4)):  # diagonal \
                return True
            if row - 3 >= 0 and col + 3 < 7 and all(board[row - i][col + i] == player for i in range(4)):  # diagonal /
                return True
    return False

def policy(board: list[list[int]]) -> int:
    # Check for winning move
    for col in range(7):
        if board[0][col] == 0:  # If column is not full
            # Simulate the move
            for row in range(5, -1, -1):
                if board[row][col] == 0:
                    board[row][col] = 1  # Place current player's disc
                    if check_win(board, 1):  # Check if this move results in a win
                        return col
                    board[row][col] = 0  # Undo move
                    break

    # Check for opponent's winning move and block
    for col in range(7):
        if board[0][col] == 0:  # If column is not full
            # Simulate the opponent's move
            for row in range(5, -1, -1):
                if board[row][col] == 0:
                    board[row][col] = -1  # Place opponent's disc
                    if check_win(board, -1):  # Check if this move results in a win for the opponent
                        board[row][col] = 0  # Undo move
                        return col
                    board[row][col] = 0  # Undo move
                    break

    # If no immediate threats or wins, choose column based on some preference
    for col in [3, 2, 4, 1, 5, 0, 6]:  # Prioritize center column first
        if board[0][col] == 0:  # If column is not full
            return col

    raise ValueError("No valid moves available")
