
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game.

    Args:
        board: A 4x4 list of lists representing the game board.
               0: empty, 1: AI (you), -1: Opponent.

    Returns:
        A tuple of two integers (row, col) indicating the chosen move.
    """

    player = 1  # AI is player 1

    # 1. Check for an immediate win
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = player
                if check_win(board, player):
                    return r, c
                board[r][c] = 0  # Undo the move

    # 2. Block opponent's immediate win
    opponent = -1
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = opponent
                if check_win(board, opponent):
                    return r, c
                board[r][c] = 0  # Undo the move

    # 3. Try to establish a winning line of 3 for AI
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = player
                if check_three_in_a_row(board, player) > 0:
                    return r, c
                board[r][c] = 0

    # 4. Block opponent's winning line of 3
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = opponent
                if check_three_in_a_row(board, opponent) > 0: # Check if opponent can make 3 in a row
                    board[r][c] = 0  # Undo
                    return r, c # Block by placing our piece
                board[r][c] = 0

    # 5. Take the center (or near center) if available
    center_moves = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for r, c in center_moves:
        if board[r][c] == 0:
            return r, c

    # 6. Take a corner if available
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for r, c in corners:
        if board[r][c] == 0:
            return r, c

    # 7. Take any available empty cell (randomly if multiple)
    empty_cells = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empty_cells.append((r, c))

    if empty_cells:
        return random.choice(empty_cells)
    
    # Should not happen in a valid game state
    return -1, -1


def check_win(board: list[list[int]], player: int) -> bool:
    """Checks if the given player has won the game."""
    # Check rows
    for r in range(4):
        for c in range(1): # Check for 4 in a row in each row
            if all(board[r][c+i] == player for i in range(4)):
                return True

    # Check columns
    for c in range(4):
        for r in range(1): # Check for 4 in a row in each column
            if all(board[r+i][c] == player for i in range(4)):
                return True

    # Check diagonals
    # Main diagonal
    for r in range(1):
        for c in range(1):
            if all(board[r+i][c+i] == player for i in range(4)):
                return True
    
    # Anti-diagonal
    for r in range(1):
        for c in range(3, 4): # Start from col 3, go to 0
            if all(board[r+i][c-i] == player for i in range(4)):
                return True

    return False

def check_three_in_a_row(board: list[list[int]], player: int) -> int:
    """
    Counts potential lines of 3 for the given player.
    This doesn't mean a guaranteed win, just a potential threat/opportunity.
    """
    count = 0

    # Check rows
    for r in range(4):
        for c in range(2): # Check blocks of 3
            if all(board[r][c+i] == player for i in range(3)) and board[r][c+3] == 0:
                count += 1
            if all(board[r][c+i] == player for i in range(3)) and c > 0 and board[r][c-1] == 0:
                count += 1
            if board[r][c] == player and board[r][c+2] == player and board[r][c+1] == 0: # X 0 X
                count += 1

    # Check columns
    for c in range(4):
        for r in range(2):
            if all(board[r+i][c] == player for i in range(3)) and board[r+3][c] == 0:
                count += 1
            if all(board[r+i][c] == player for i in range(3)) and r > 0 and board[r-1][c] == 0:
                count += 1
            if board[r][c] == player and board[r+2][c] == player and board[r+1][c] == 0: # X 0 X
                count += 1

    # Check diagonals (main)
    for r in range(2):
        for c in range(2):
            if all(board[r+i][c+i] == player for i in range(3)):
                # Check if the 4th position is empty to extend
                if r + 3 < 4 and c + 3 < 4 and board[r+3][c+3] == 0:
                    count += 1
                # Check if the position before is empty to extend
                if r > 0 and c > 0 and board[r-1][c-1] == 0:
                    count += 1
            if board[r][c] == player and board[r+2][c+2] == player and board[r+1][c+1] == 0:
                count += 1

    # Check diagonals (anti)
    for r in range(2):
        for c in range(2, 4): # c goes from 2 to 3
            if all(board[r+i][c-i] == player for i in range(3)):
                # Check if the 4th position is empty to extend
                if r + 3 < 4 and c - 3 >= 0 and board[r+3][c-3] == 0:
                    count += 1
                # Check if the position before is empty to extend
                if r > 0 and c < 3 and board[r-1][c+1] == 0:
                    count += 1
            if board[r][c] == player and board[r+2][c-2] == player and board[r+1][c-1] == 0:
                count += 1

    return count
