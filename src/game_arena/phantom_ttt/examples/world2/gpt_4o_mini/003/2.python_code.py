
def policy(board: list[list[int]]) -> int:
    # Helper function to check if a player has won given the board state
    def is_winning(board):
        # Check all rows, columns and diagonals for a winning condition
        for i in range(3):
            if all(board[i][j] == 1 for j in range(3)) or all(board[j][i] == 1 for j in range(3)):
                return True
        # Check diagonals
        if all(board[i][i] == 1 for i in range(3)) or all(board[i][2 - i] == 1 for i in range(3)):
            return True
        return False

    # Possible moves (row, col)
    possible_moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

    # Check for immediate win
    for row, col in possible_moves:
        board[row][col] = 1  # Simulate the move
        if is_winning(board):
            return (row, col)
        board[row][col] = 0  # Undo the move

    # If no immediate win, check for possible blocks (assuming opponent is also trying to win)
    for row, col in possible_moves:
        board[row][col] = 0  # Assume opponent would play here
        if is_winning(board):
            board[row][col] = 0  # Undo the move
            return (row, col)  # Block the opponent's winning move
        board[row][col] = 0  # Undo the move

    # Final fallback: just pick any available move
    return possible_moves[0]
