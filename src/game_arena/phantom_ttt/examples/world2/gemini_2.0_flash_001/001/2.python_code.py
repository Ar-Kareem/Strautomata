
import random

def check_win(board: list[list[int]], player: int) -> bool:
    """Checks if the given player has won the board."""
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):
            return True
        if all(board[j][i] == player for j in range(3)):
            return True
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False

def get_legal_moves(board: list[list[int]]) -> list[tuple[int, int]]:
    """Returns a list of legal moves (cells with value 0)."""
    legal_moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                legal_moves.append((i, j))
    return legal_moves

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for Phantom Tic Tac Toe.
    """

    # 1. Winning Move
    legal_moves = get_legal_moves(board)
    for row, col in legal_moves:
        temp_board = [row[:] for row in board]  # Create a copy
        temp_board[row][col] = 1
        if check_win(temp_board, 1):
            return (row, col)

    # 2. Block Opponent (Hypothetical)
    for row, col in legal_moves:
        temp_board = [row[:] for row in board]  # Create a copy
        temp_board[row][col] = -1  # Opponent's hypothetical move
        if check_win(temp_board, -1):
            return (row, col)

    # 3. Center Preference
    if board[1][1] == 0:
        return (1, 1)

    # 4. Corner Preference
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for row, col in corners:
        if board[row][col] == 0:
            return (row, col)

    # 5. Edge Preference
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for row, col in edges:
        if board[row][col] == 0:
            return (row, col)
    # 6. Random Legal Move (Fallback)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)

    # Should not reach here if a legal move exists.
    return (0,0)
