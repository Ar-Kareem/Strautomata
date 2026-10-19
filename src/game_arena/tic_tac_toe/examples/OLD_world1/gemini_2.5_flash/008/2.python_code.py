
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a Tic-Tac-Toe game using a simple heuristic.

    Args:
        board: A 3x3 list of lists representing the Tic-Tac-Toe board.
               0: empty, 1: AI (you), -1: opponent.

    Returns:
        A tuple of two integers (row, col) indicating the chosen move.
    """

    player = 1  # AI is player 1
    opponent = -1

    # 1. Check for a winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = player
                if check_win(board, player):
                    return (r, c)
                board[r][c] = 0  # Undo the move

    # 2. Block opponent's winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = opponent
                if check_win(board, opponent):
                    return (r, c)
                board[r][c] = 0  # Undo the move

    # 3. Take the center if available
    if board[1][1] == 0:
        return (1, 1)

    # 4. Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)  # Randomize corner choice for less predictability
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)

    # 5. Take any empty side cell
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    random.shuffle(sides)  # Randomize side choice
    for r, c in sides:
        if board[r][c] == 0:
            return (r, c)

    # This case should ideally not be reached if the board is not full and valid
    # As a fallback, return any empty cell
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return (r, c)

    # If the board is full (should have been caught by win/draw conditions earlier)
    return (-1, -1) # Indicate an error or no possible move

def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    # Check rows
    for r in range(3):
        if all(board[r][c] == player for c in range(3)):
            return True
    # Check columns
    for c in range(3):
        if all(board[r][c] == player for r in range(3)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False

if __name__ == '__main__':
    # Example usage:
    # Test cases
    test_boards = [
        # Empty board
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        # Will win on next move (horizontal)
        [[1, 1, 0], [0, 0, 0], [0, 0, 0]],
        # Will win on next move (vertical)
        [[1, 0, 0], [1, 0, 0], [0, 0, 0]],
        # Block opponent win (horizontal)
        [[-1, -1, 0], [0, 0, 0], [0, 0, 0]],
        # Block opponent win (vertical)
        [[-1, 0, 0], [-1, 0, 0], [0, 0, 0]],
        # Take center
        [[-1, 0, 0], [0, 0, 0], [0, 0, 0]],
        # Take corner
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        # Take a side
        [[1, -1, 0], [-1, 1, 0], [0, 0, 0]],
        # Complex board, AI wins
        [[1, -1, 0], [1, 0, 0], [0, 0, -1]],
        # Complex board, block opponent
        [[1, 1, -1], [0, 0, 0], [0, 0, -1]],
        # Draw game example (no winning or blocking moves immediately)
        [[1, -1, 1], [-1, 1, -1], [0, 1, -1]],
        [[1, 0, 0], [0, -1, 0], [0, 0, 1]], # Opponent has blocked center, take corner
        [[0, 0, 0], [0, -1, 0], [0, 0, 0]], # Opponent took center, take corner
    ]

    for i, board_state in enumerate(test_boards):
        print(f"--- Test Board {i+1} ---")
        for row in board_state:
            print(row)
        move = policy(board_state)
        print(f"Recommended move: {move}
")
