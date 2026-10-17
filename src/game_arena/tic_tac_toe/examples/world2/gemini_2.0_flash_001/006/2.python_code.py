
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 4x4 Tic Tac Toe game based on the provided board.

    Args:
        board (list[list[int]]): A 4x4 list of lists representing the game board.
                                 0 represents an empty cell, 1 represents your move, and -1 represents the opponent's move.

    Returns:
        tuple[int, int]: A tuple of two integers (row, col) representing the chosen move.
                         The chosen cell must be empty.
    """

    def check_win(board, player):
        """Checks if the given player has won the game."""
        for row in range(4):
            if all(board[row][col] == player for col in range(4)):
                return True
        for col in range(4):
            if all(board[row][col] == player for row in range(4)):
                return True
        if all(board[i][i] == player for i in range(4)):
            return True
        if all(board[i][3 - i] == player for i in range(4)):
            return True
        return False

    def find_winning_move(board, player):
        """Finds a move that wins the game for the given player."""
        for row in range(4):
            for col in range(4):
                if board[row][col] == 0:
                    board[row][col] = player
                    if check_win(board, player):
                        board[row][col] = 0  # Reset the board
                        return (row, col)
                    board[row][col] = 0  # Reset the board
        return None

    # 1. Check for a winning move
    winning_move = find_winning_move(board, 1)
    if winning_move:
        return winning_move

    # 2. Check for a blocking move
    blocking_move = find_winning_move(board, -1)
    if blocking_move:
        return blocking_move

    # 3. Strategic Placement: Prioritize center, then corners
    center_moves = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for row, col in center_moves:
        if board[row][col] == 0:
            return (row, col)

    corner_moves = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for row, col in corner_moves:
        if board[row][col] == 0:
            return (row, col)

    # 4. Random Move: Choose a random empty cell
    possible_moves = []
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                possible_moves.append((row, col))

    if possible_moves:
        return random.choice(possible_moves)
    else:
        # Should not happen with proper game logic, but handle edge case
        return (0, 0)
