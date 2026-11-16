
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Selects the next move for a 3x3x3 Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of three integers indicating the empty cell you choose (x, y, z).
    """

    # Convert the board to a numpy array for easier manipulation
    board = np.array(board)

    # 1. Check for winning move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x, y, z] == 0:
                    # Simulate the move
                    board_copy = board.copy()
                    board_copy[x, y, z] = 1

                    # Check if the move wins the game
                    if check_win(board_copy, 1):
                        return (x, y, z)

    # 2. Block opponent's winning move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x, y, z] == 0:
                    # Simulate the move
                    board_copy = board.copy()
                    board_copy[x, y, z] = -1

                    # Check if the move wins the game for the opponent
                    if check_win(board_copy, -1):
                        return (x, y, z)

    # 3. Choose the center if available
    if board[1, 1, 1] == 0:
        return (1, 1, 1)

    # 4. Choose a corner if available
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if board[corner[0], corner[1], corner[2]] == 0:
            return corner

    # 5. Choose any available move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x, y, z] == 0:
                    return (x, y, z)

    # If no move is available, return (0, 0, 0) as a default
    return (0, 0, 0)


def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won the 3x3x3 Tic Tac Toe game.

    Args:
        board: The 3x3x3 game board as a numpy array.
        player: The player to check for (1 or -1).

    Returns:
        True if the player has won, False otherwise.
    """
    # Check rows
    for x in range(3):
        for y in range(3):
            if np.all(board[x, y, :] == player):
                return True
            if np.all(board[x, :, y] == player):
                return True
            if np.all(board[:, x, y] == player):
                return True

    # Check diagonals in each 2D plane
    for x in range(3):
        if np.all(np.diag(board[x, :, :]) == player):
            return True
        if np.all(np.diag(np.fliplr(board[x, :, :])) == player):
            return True
        if np.all(np.diag(board[:, x, :]) == player):
            return True
        if np.all(np.diag(np.fliplr(board[:, x, :])) == player):
            return True
        if np.all(np.diag(board[:, :, x]) == player):
            return True
        if np.all(np.diag(np.fliplr(board[:, :, x])) == player):
            return True

    # Check space diagonals
    if np.all(np.diag([board[i, i, i] for i in range(3)]) == player):
        return True
    if np.all(np.diag([board[i, i, 2 - i] for i in range(3)]) == player):
        return True
    if np.all(np.diag([board[i, 2 - i, i] for i in range(3)]) == player):
        return True
    if np.all(np.diag([board[2 - i, i, i] for i in range(3)]) == player):
        return True
    
    # The following checks diagonals such as {(0, 0, 0), (1, 1, 2), (2,  2, 1))
    if all(board[i, i, (i+1)%3] == player for i in range(3)):
       return True
    if all(board[i, (i+1)%3, i] == player for i in range(3)):
       return True
    if all(board[(i+1)%3, i, i] == player for i in range(3)):
       return True
       
    if all(board[i, i, (i+2)%3] == player for i in range(3)):
       return True
    if all(board[i, (i+2)%3,i] == player for i in range(3)):
       return True
    if all(board[(i+2)%3,i, i] == player for i in range(3)):
       return True

    # Check for board[i,j,k] for different permutations of i,j,k starting with 0,1,2
    if all(board[i, (i+1)%3, (i+2)%3] == player for i in range(3)):
       return True

    if all(board[i, (i+2)%3, (i+1)%3] == player for i in range(3)):
       return True
    
    if all(board[(i+1)%3, (i+2)%3, i] == player for i in range(3)):
       return True

    if all(board[ (i+2)%3, (i+1)%3, i] == player for i in range(3)):
       return True

    if all(board[(i+1)%3, i, (i+2)%3] == player for i in range(3)):
       return True

    if all(board[(i+2)%3, i, (i+1)%3] == player for i in range(3)):
       return True
    

    return False
