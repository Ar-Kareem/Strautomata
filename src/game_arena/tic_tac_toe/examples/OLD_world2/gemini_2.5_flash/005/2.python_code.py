
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
    n = len(board)
    opponent = -1
    player = 1

    # 1. Check for an immediate win
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                board[r][c] = player
                if check_win(board, player):
                    return (r, c)
                board[r][c] = 0

    # 2. Block opponent's immediate win
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                board[r][c] = opponent
                if check_win(board, opponent):
                    return (r, c)
                board[r][c] = 0

    # 3. Prioritize center cells (for 4x4, the 2x2 center block)
    center_cells = [(1, 1), (1, 2), (2, 1), (2, 2)]
    random.shuffle(center_cells)  # Add some randomness for variety
    for r, c in center_cells:
        if board[r][c] == 0:
            return (r, c)

    # 4. Prioritize corners (secondary strategic spots)
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    random.shuffle(corners)
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)

    # 5. Play randomly if no strategic move is found (to avoid losing immediately)
    empty_cells = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                empty_cells.append((r, c))
    
    if empty_cells:
        return random.choice(empty_cells)
    
    # Should not happen in a valid game unless the board is full
    return (-1, -1) 

def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the 4x4 Tic Tac Toe game.
    """
    n = len(board)

    # Check rows
    for r in range(n):
        if all(board[r][c] == player for c in range(n)):
            return True

    # Check columns
    for c in range(n):
        if all(board[r][c] == player for r in range(n)):
            return True

    # Check main diagonal
    if all(board[i][i] == player for i in range(n)):
        return True

    # Check anti-diagonal
    if all(board[i][n - 1 - i] == player for i in range(n)):
        return True

    return False

# Example Usage (optional, for local testing)
if __name__ == '__main__':
    # Initial empty board
    empty_board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    print(f"Empty board move: {policy(empty_board)}") # Should pick a center cell or a random empty cell

    # Board where AI can win
    win_board = [
        [1, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    print(f"Winning move: {policy(win_board)}") # Should be (0, 3)

    # Board where AI needs to block opponent
    block_board = [
        [-1, -1, -1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    print(f"Blocking move: {policy(block_board)}") # Should be (0, 3)

    # More complex scenario
    complex_board = [
        [1, -1, 0, 0],
        [-1, 1, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    move = policy(complex_board)
    print(f"Complex board move: {move}") 
    # This might try to block (0,2) or (1,2) if opponent was to make a move there
    # Or prioritize center (2,2) or (2,1) or (1,2)
    
    # Board with immediate diagonal win for AI
    diag_win_board = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 0],
    ]
    print(f"Diagonal winning move: {policy(diag_win_board)}") # Should be (3, 3)

    # Board with immediate anti-diagonal block needed
    anti_diag_block_board = [
        [0, 0, 0, -1],
        [0, 0, -1, 0],
        [0, -1, 0, 0],
        [0, 0, 0, 0],
    ]
    print(f"Anti-diagonal blocking move: {policy(anti_diag_block_board)}") # Should be (3, 0)
