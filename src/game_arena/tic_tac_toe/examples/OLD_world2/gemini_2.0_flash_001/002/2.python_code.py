
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 4x4 Tic Tac Toe game.
    """
    # 1. Check for winning moves
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                if check_win(board, 1):
                    board[r][c] = 0  # Reset the board
                    return (r, c)
                board[r][c] = 0  # Reset the board

    # 2. Block opponent's winning moves
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = -1
                if check_win(board, -1):
                    board[r][c] = 0  # Reset the board
                    return (r, c)
                board[r][c] = 0  # Reset the board

    # 3. Choose a random available move
    available_moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                available_moves.append((r, c))

    if available_moves:
        return random.choice(available_moves)
    else:
        # Should not happen in normal gameplay, but handle it anyway
        return (0, 0)


def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    # Check rows
    for r in range(4):
        if all(board[r][c] == player for c in range(4)):
            return True

    # Check columns
    for c in range(4):
        if all(board[r][c] == player for r in range(4)):
            return True

    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True

    if all(board[i][3 - i] == player for i in range(4)):
        return True

    return False


if __name__ == '__main__':
    # Example Usage
    board = [
        [0, 0, 0, 0],
        [0, 1, -1, 0],
        [0, -1, 1, 0],
        [0, 0, 0, 0]
    ]

    row, col = policy(board)
    print(f"Next move: ({row}, {col})")
