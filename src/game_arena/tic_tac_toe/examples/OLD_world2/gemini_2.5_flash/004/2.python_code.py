
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game.

    Args:
        board: A 4x4 list of lists representing the game board.
               0: empty, 1: AI (you), -1: opponent.

    Returns:
        A tuple of two integers (row, col) indicating the chosen move.
    """
    player = 1  # AI is player 1

    # 1. Winning move check
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = player
                if check_win(board, player):
                    return (r, c)
                board[r][c] = 0  # Undo move

    # 2. Block opponent's winning move check
    opponent = -1
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = opponent
                if check_win(board, opponent):
                    return (r, c)
                board[r][c] = 0  # Undo move

    # 3. Center preference (for 4x4, the 2x2 center is good)
    center_cells = [(1, 1), (1, 2), (2, 1), (2, 2)]
    random.shuffle(center_cells) # Shuffle to add variety if multiple are empty
    for r, c in center_cells:
        if board[r][c] == 0:
            return (r, c)

    # 4. Corner preference (next best strategic positions)
    corner_cells = [(0, 0), (0, 3), (3, 0), (3, 3)]
    random.shuffle(corner_cells) # Shuffle to add variety if multiple are empty
    for r, c in corner_cells:
        if board[r][c] == 0:
            return (r, c)

    # 5. Find any open space (random move)
    empty_cells = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empty_cells.append((r, c))

    if empty_cells:
        return random.choice(empty_cells)
    
    # Should not happen in a valid game, but as a fallback
    return (0, 0)


def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the 4x4 Tic Tac Toe game.
    """
    # Check rows
    for r in range(4):
        if all(board[r][c] == player for c in range(4)):
            return True

    # Check columns
    for c in range(4):
        if all(board[r][c] == player for r in range(4)):
            return True

    # Check main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True

    # Check anti-diagonal
    if all(board[i][3 - i] == player for i in range(4)):
        return True

    return False

