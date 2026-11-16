
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # List of all possible moves (row, col)
    moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] != 1]

    # Check for immediate win
    for move in moves:
        # Simulate placing our mark
        temp_board = [row[:] for row in board]
        temp_board[move[0]][move[1]] = 1

        # Check if this move wins
        if check_win(temp_board, 1):
            return move

    # Check for opponent's potential win and block it
    for move in moves:
        # Simulate opponent placing their mark (we don't know where they are)
        # We'll assume they might be in any 0 cell
        temp_board = [row[:] for row in board]
        temp_board[move[0]][move[1]] = -1  # -1 represents opponent

        # Check if opponent would win with this move
        if check_win(temp_board, -1):
            return move

    # Prefer center if available
    if (1, 1) in moves:
        return (1, 1)

    # Prefer corners if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [c for c in corners if c in moves]
    if available_corners:
        return random.choice(available_corners)

    # If no strategic move, choose randomly from available moves
    return random.choice(moves)

def check_win(board: list[list[int]], player: int) -> bool:
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True

    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return True
    if board[0][2] == board[1][1] == board[2][0] == player:
        return True

    return False
