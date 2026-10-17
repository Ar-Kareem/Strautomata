
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 4x4 Tic Tac Toe game.

    Args:
        board: A 4x4 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of two integers (0-3, 0-3) indicating the row and column you choose.
    """

    possible_moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                possible_moves.append((r, c))

    if not possible_moves:
        return (0, 0)  # Should not happen in a valid game state, but return a safe move

    # 1. Check for winning move
    for r, c in possible_moves:
        temp_board = [row[:] for row in board]
        temp_board[r][c] = 1
        if check_win(temp_board, 1):
            return (r, c)

    # 2. Block opponent's winning move
    for r, c in possible_moves:
        temp_board = [row[:] for row in board]
        temp_board[r][c] = -1
        if check_win(temp_board, -1):
            return (r, c)
    
    # 3. Play in the center if available
    if (1,1) in possible_moves:
        return (1,1)
    if (1,2) in possible_moves:
        return (1,2)
    if (2,1) in possible_moves:
        return (2,1)
    if (2,2) in possible_moves:
        return (2,2)
    

    # 4. Choose a random move
    return random.choice(possible_moves)


def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True

    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True

    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3 - i] == player for i in range(4)):
        return True

    return False


if __name__ == '__main__':
    # Example usage
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    move = policy(board)
    print(f"Next move: {move}")

    board2 = [
        [1, -1, 1, 0],
        [-1, 1, -1, 0],
        [0, -1, 1, 0],
        [0, 0, -1, 0]
    ]
    move2 = policy(board2)
    print(f"Next move {move2}")
